"""Tests for the metrics collector and dashboard server."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from guardian.audit.logger import AuditLogger
from guardian.audit.models import AuditEntry
from guardian.detector.models import DetectionResult
from guardian.metrics.collector import MetricsCollector
from guardian.reviewer.models import Violation


@pytest.fixture
def logger(temp_dir):
    return AuditLogger(repo="owner/repo", audit_dir=temp_dir)


@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def seeded_logger(temp_dir):
    logger = AuditLogger(repo="owner/repo", audit_dir=temp_dir)
    now = datetime.now(timezone.utc)

    e1 = AuditEntry(
        repo="owner/repo", pr_number=1, action="analysis", risk_level="low",
        timestamp=(now - timedelta(hours=3)).isoformat(),
        detection_results=[DetectionResult(file_path="a.py", total_lines=5, confidence="low")],
        violations=[],
    )
    e2 = AuditEntry(
        repo="owner/repo", pr_number=2, action="analysis", risk_level="high",
        timestamp=(now - timedelta(hours=2)).isoformat(),
        detection_results=[DetectionResult(file_path="b.py", total_lines=10, confidence="high")],
        violations=[
            Violation(rule_name="hallucinated-api", severity="high", file_path="b.py", line=5,
                       pattern_found="fake()", explanation="Bad call", remediation="Fix it"),
        ],
    )
    e3 = AuditEntry(
        repo="owner/repo", pr_number=2, action="comment_posted", risk_level="high",
        timestamp=(now - timedelta(hours=1)).isoformat(),
    )
    e4 = AuditEntry(
        repo="owner/repo", pr_number=3, action="analysis", risk_level="critical",
        timestamp=(now - timedelta(minutes=30)).isoformat(),
        detection_results=[
            DetectionResult(file_path="c.py", total_lines=20, confidence="high"),
            DetectionResult(file_path="d.py", total_lines=15, confidence="medium"),
        ],
        violations=[
            Violation(rule_name="hallucinated-api", severity="critical", file_path="c.py", line=10,
                       pattern_found="bad()", explanation="Critical", remediation="Fix"),
            Violation(rule_name="hardcoded-secrets", severity="critical", file_path="c.py", line=12,
                       pattern_found="sk-xxx", explanation="Secret", remediation="Remove"),
        ],
        feedback="confirmed",
    )

    for e in [e1, e2, e3, e4]:
        logger.append(e)
    return logger


class TestMetricsCollector:
    def test_total_prs(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        assert collector.total_prs == 3

    def test_ai_prs(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        assert collector.ai_prs == 2

    def test_ai_code_pct(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        assert collector.ai_code_pct == 75.0

    def test_violations_by_rule(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        assert collector.violations_by_rule["hallucinated-api"] == 2
        assert collector.violations_by_rule["hardcoded-secrets"] == 1

    def test_violation_trends(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        trends = collector.violation_trends
        assert len(trends) >= 1
        total = sum(t["count"] for t in trends)
        assert total == 3

    def test_false_positive_rate(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        assert collector.false_positive_rate == 0.0

    def test_false_positive_rate_with_disputed(self, temp_dir):
        logger = AuditLogger(repo="owner/repo", audit_dir=temp_dir)
        logger.append(AuditEntry(repo="owner/repo", pr_number=1, action="analysis", feedback="confirmed"))
        logger.append(AuditEntry(repo="owner/repo", pr_number=2, action="analysis", feedback="disputed"))
        collector = MetricsCollector(logger)
        assert collector.false_positive_rate == 0.5

    def test_recent_prs(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        prs = collector.recent_prs[:2]
        assert len(prs) == 2
        assert prs[0]["pr_number"] == 3
        assert prs[1]["pr_number"] == 2

    def test_recent_prs_violation_count(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        prs = {p["pr_number"]: p for p in collector.recent_prs}
        assert prs[1]["violation_count"] == 0
        assert prs[2]["violation_count"] == 1
        assert prs[3]["violation_count"] == 2

    def test_to_dict_keys(self, seeded_logger):
        collector = MetricsCollector(seeded_logger)
        d = collector.to_dict()
        assert "total_prs" in d
        assert "ai_prs" in d
        assert "ai_code_pct" in d
        assert "violations_by_rule" in d
        assert "violation_trends" in d
        assert "false_positive_rate" in d
        assert "recent_prs" in d
        assert d["total_prs"] == 3

    def test_empty_logger(self, temp_dir):
        logger = AuditLogger(repo="empty/repo", audit_dir=temp_dir)
        collector = MetricsCollector(logger)
        assert collector.total_prs == 0
        assert collector.ai_prs == 0
        assert collector.ai_code_pct == 0.0
        assert collector.violations_by_rule == {}
        assert collector.false_positive_rate == 0.0
        assert collector.recent_prs == []


class TestDashboardAPI:
    @pytest.fixture
    def client(self, seeded_logger):
        from guardian.server.app import app
        return TestClient(app)

    def test_api_stats_endpoint(self, client, temp_dir):
        response = client.get(f"/api/stats?audit_dir={temp_dir}")
        assert response.status_code == 200
        data = response.json()
        assert "total_prs" in data

    def test_dashboard_endpoint(self, client, temp_dir):
        response = client.get(f"/dashboard?audit_dir={temp_dir}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_dashboard_contains_stats(self, client, temp_dir):
        response = client.get(f"/dashboard?audit_dir={temp_dir}")
        html = response.text
        assert "PRs Analyzed" in html
        assert "Recent PRs" in html
        assert "Violations by Rule" in html
