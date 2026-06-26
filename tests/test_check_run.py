"""Tests for the Check Run output generator (pr/check_run.py)."""

import pytest
from guardian.reviewer.models import ReviewResult, Violation
from guardian.pr.check_run import generate_check_run_output, determine_conclusion


def make_violation(
    rule_name: str = "test-rule",
    severity: str = "medium",
    file_path: str = "src/main.py",
    line: int | None = 42,
    explanation: str = "This looks risky.",
) -> Violation:
    return Violation(
        rule_name=rule_name,
        severity=severity,
        file_path=file_path,
        line=line,
        pattern_found="suspicious_code()",
        explanation=explanation,
        remediation="Refactor it.",
        governance_url=None,
    )


class TestGenerateCheckRunOutput:
    def test_title_is_correct(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        output = generate_check_run_output(review, {"ai_file_count": 0, "total_file_count": 5, "ai_pct": 0})
        assert output["title"] == "AI Code Guardian — Review Complete"

    def test_summary_contains_risk_level(self):
        review = ReviewResult(violations=[], risk_level="high", summary="Issues")
        output = generate_check_run_output(review, {"ai_file_count": 0, "total_file_count": 5, "ai_pct": 0})
        assert "HIGH" in output["summary"]

    def test_summary_contains_ai_code_stats(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        stats = {"ai_file_count": 2, "total_file_count": 10, "ai_pct": 20.0, "fpr": "0%"}
        output = generate_check_run_output(review, stats)
        assert "2/10" in output["summary"]
        assert "20.0%" in output["summary"]

    def test_summary_contains_violation_count(self):
        v = make_violation()
        review = ReviewResult(violations=[v], risk_level="high", summary="Issues")
        output = generate_check_run_output(review, {"ai_file_count": 1, "total_file_count": 5, "ai_pct": 20})
        assert "**Violations:** 1" in output["summary"]

    def test_summary_contains_fpr(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        output = generate_check_run_output(review, {"ai_file_count": 0, "total_file_count": 5, "ai_pct": 0, "fpr": "5%"})
        assert "5%" in output["summary"]

    def test_fpr_default_to_n_a_when_not_provided(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        output = generate_check_run_output(review, {"ai_file_count": 0, "total_file_count": 0, "ai_pct": 0})
        assert "N/A" in output["summary"]

    def test_text_contains_violation_details(self):
        v = make_violation(rule_name="test-rule", severity="high", explanation="Risky pattern")
        review = ReviewResult(violations=[v], risk_level="high", summary="Issues")
        output = generate_check_run_output(review, {"ai_file_count": 1, "total_file_count": 5, "ai_pct": 20})
        assert "[HIGH]" in output["text"]
        assert "test-rule" in output["text"]
        assert "src/main.py:42" in output["text"]
        assert "Risky pattern" in output["text"]

    def test_text_no_violations(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        output = generate_check_run_output(review, {"ai_file_count": 0, "total_file_count": 5, "ai_pct": 0})
        assert "No violations found" in output["text"]

    def test_text_with_multiple_violations(self):
        v1 = make_violation(rule_name="rule-a", severity="critical", file_path="a.py", line=1)
        v2 = make_violation(rule_name="rule-b", severity="low", file_path="b.py", line=2)
        review = ReviewResult(violations=[v1, v2], risk_level="critical", summary="Issues")
        output = generate_check_run_output(review, {"ai_file_count": 2, "total_file_count": 5, "ai_pct": 40})
        assert "rule-a" in output["text"]
        assert "rule-b" in output["text"]
        assert "a.py:1" in output["text"]
        assert "b.py:2" in output["text"]

    def test_violation_without_line_number(self):
        v = make_violation(line=None, file_path="src/main.py")
        review = ReviewResult(violations=[v], risk_level="medium", summary="Issues")
        output = generate_check_run_output(review, {"ai_file_count": 1, "total_file_count": 5, "ai_pct": 20})
        assert "src/main.py" in output["text"]
        assert "src/main.py:None" not in output["text"]


class TestDetermineConclusion:
    def test_advisory_always_neutral(self):
        review = ReviewResult(violations=[], risk_level="critical", summary="Issues")
        assert determine_conclusion(review, "advisory") == "neutral"

    def test_enforcement_critical_failure(self):
        review = ReviewResult(violations=[], risk_level="critical", summary="Issues")
        assert determine_conclusion(review, "enforcement") == "failure"

    def test_enforcement_high_success(self):
        review = ReviewResult(violations=[], risk_level="high", summary="Issues")
        assert determine_conclusion(review, "enforcement") == "success"

    def test_enforcement_medium_success(self):
        review = ReviewResult(violations=[], risk_level="medium", summary="Issues")
        assert determine_conclusion(review, "enforcement") == "success"

    def test_enforcement_low_success(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        assert determine_conclusion(review, "enforcement") == "success"
