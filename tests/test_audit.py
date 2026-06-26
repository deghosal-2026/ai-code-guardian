"""Tests for the audit log (audit/models.py, audit/logger.py)."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from guardian.audit.models import AuditEntry
from guardian.audit.logger import AuditLogger
from guardian.detector.models import DetectionResult
from guardian.reviewer.models import Violation


@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def logger(temp_dir):
    return AuditLogger(repo="owner/repo", audit_dir=temp_dir)


class TestAuditEntry:
    def test_default_timestamp_generated(self):
        entry = AuditEntry()
        assert entry.timestamp != ""
        assert "T" in entry.timestamp

    def test_default_event_id_generated(self):
        entry = AuditEntry()
        assert entry.event_id != ""
        assert len(entry.event_id) == 36

    def test_custom_timestamp_preserved(self):
        ts = "2026-06-25T12:00:00+00:00"
        entry = AuditEntry(timestamp=ts)
        assert entry.timestamp == ts

    def test_custom_event_id_preserved(self):
        eid = "my-custom-id"
        entry = AuditEntry(event_id=eid)
        assert entry.event_id == eid

    def test_to_json_contains_all_fields(self):
        entry = AuditEntry(
            repo="owner/repo",
            pr_number=42,
            action="analysis",
            duration_ms=1500,
        )
        data = json.loads(entry.to_json())
        assert data["repo"] == "owner/repo"
        assert data["pr_number"] == 42
        assert data["action"] == "analysis"
        assert data["duration_ms"] == 1500
        assert data["version"] == 1
        assert "timestamp" in data
        assert "event_id" in data

    def test_to_json_with_violations(self):
        v = Violation(
            rule_name="test", severity="high", file_path="f.py", line=1,
            pattern_found="bad()", explanation="risky", remediation="fix it",
        )
        entry = AuditEntry(violations=[v])
        data = json.loads(entry.to_json())
        assert len(data["violations"]) == 1
        assert data["violations"][0]["rule_name"] == "test"

    def test_to_json_with_detection_results(self):
        d = DetectionResult(file_path="f.py", total_lines=10, confidence="high")
        entry = AuditEntry(detection_results=[d])
        data = json.loads(entry.to_json())
        assert len(data["detection_results"]) == 1
        assert data["detection_results"][0]["file_path"] == "f.py"

    def test_to_json_handles_unicode(self):
        entry = AuditEntry(
            repo="owner/repo",
            error="检测到问题",
        )
        data = json.loads(entry.to_json())
        assert data["error"] == "检测到问题"

    def test_to_json_with_none_feedback(self):
        entry = AuditEntry(feedback=None)
        data = json.loads(entry.to_json())
        assert data["feedback"] is None


class TestAuditLogger:
    def test_append_creates_file(self, logger, temp_dir):
        entry = AuditEntry(repo="owner/repo", pr_number=1)
        logger.append(entry)
        log_path = Path(temp_dir) / "owner_repo" / "audit.jsonl"
        assert log_path.exists()
        content = log_path.read_text()
        assert entry.event_id in content

    def test_append_writes_valid_jsonl(self, logger, temp_dir):
        entry = AuditEntry(repo="owner/repo", pr_number=1)
        logger.append(entry)
        log_path = Path(temp_dir) / "owner_repo" / "audit.jsonl"
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["event_id"] == entry.event_id

    def test_multiple_appends_preserved_in_order(self, logger, temp_dir):
        e1 = AuditEntry(repo="owner/repo", pr_number=1)
        e2 = AuditEntry(repo="owner/repo", pr_number=2)
        e3 = AuditEntry(repo="owner/repo", pr_number=3)
        logger.append(e1)
        logger.append(e2)
        logger.append(e3)
        log_path = Path(temp_dir) / "owner_repo" / "audit.jsonl"
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 3
        assert json.loads(lines[0])["pr_number"] == 1
        assert json.loads(lines[1])["pr_number"] == 2
        assert json.loads(lines[2])["pr_number"] == 3

    def test_read_returns_all_entries(self, logger, temp_dir):
        for i in range(5):
            logger.append(AuditEntry(repo="owner/repo", pr_number=i))
        entries = logger.read()
        assert len(entries) == 5
        pr_numbers = [e.pr_number for e in entries]
        assert pr_numbers == [0, 1, 2, 3, 4]

    def test_read_filters_by_since(self, logger, temp_dir):
        t1 = datetime.now(timezone.utc) - timedelta(hours=2)
        t2 = datetime.now(timezone.utc) - timedelta(hours=1)
        t3 = datetime.now(timezone.utc)

        e1 = AuditEntry(repo="owner/repo", pr_number=1, timestamp=t1.isoformat())
        e2 = AuditEntry(repo="owner/repo", pr_number=2, timestamp=t2.isoformat())
        e3 = AuditEntry(repo="owner/repo", pr_number=3, timestamp=t3.isoformat())

        logger.append(e1)
        logger.append(e2)
        logger.append(e3)

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)
        entries = logger.read(since=cutoff)
        assert len(entries) == 2
        assert entries[0].pr_number == 2
        assert entries[1].pr_number == 3

    def test_read_empty_file_returns_empty_list(self, logger):
        entries = logger.read()
        assert entries == []

    def test_file_per_repo_isolation(self, temp_dir):
        logger_a = AuditLogger(repo="owner/repo-a", audit_dir=temp_dir)
        logger_b = AuditLogger(repo="owner/repo-b", audit_dir=temp_dir)

        logger_a.append(AuditEntry(repo="owner/repo-a", pr_number=1))
        logger_b.append(AuditEntry(repo="owner/repo-b", pr_number=100))

        assert len(logger_a.read()) == 1
        assert len(logger_b.read()) == 1
        assert logger_a.read()[0].pr_number == 1
        assert logger_b.read()[0].pr_number == 100

    def test_no_modification_of_existing_entries(self, logger, temp_dir):
        e1 = AuditEntry(repo="owner/repo", pr_number=1)
        logger.append(e1)
        log_path = Path(temp_dir) / "owner_repo" / "audit.jsonl"
        original = log_path.read_text()

        logger.append(AuditEntry(repo="owner/repo", pr_number=2))
        modified = log_path.read_text()

        assert modified.startswith(original.strip())

    def test_unicode_content(self, logger, temp_dir):
        entry = AuditEntry(
            repo="owner/repo",
            error="检测到问题",
            action="analysis",
        )
        logger.append(entry)
        entries = logger.read()
        assert len(entries) == 1
        assert entries[0].error == "检测到问题"

    def test_directory_created_on_first_write(self, temp_dir):
        nested = os.path.join(temp_dir, "deep", "nested")
        logger = AuditLogger(repo="test/repo", audit_dir=nested)
        logger.append(AuditEntry(repo="test/repo", pr_number=1))
        log_path = Path(nested) / "test_repo" / "audit.jsonl"
        assert log_path.exists()

    def test_default_audit_dir(self):
        logger = AuditLogger(repo="owner/repo")
        assert ".guardian/audit" in str(logger.path)
        assert "owner_repo" in str(logger.path)
        assert logger.path.name == "audit.jsonl"
