"""Tests for the PR comment generator (pr/commentator.py)."""

import pytest
from guardian.reviewer.models import ReviewResult, Violation
from guardian.pr.commentator import generate_comment


def make_violation(
    rule_name: str = "test-rule",
    severity: str = "medium",
    file_path: str = "src/main.py",
    line: int | None = 42,
    pattern_found: str = "suspicious_code()",
    explanation: str = "This looks risky.",
    remediation: str = "Refactor it.",
    governance_url: str | None = None,
) -> Violation:
    return Violation(
        rule_name=rule_name,
        severity=severity,
        file_path=file_path,
        line=line,
        pattern_found=pattern_found,
        explanation=explanation,
        remediation=remediation,
        governance_url=governance_url,
    )


class TestGenerateComment:
    def test_no_violations(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        comment = generate_comment(review, mode="advisory")
        assert "No violations found" in comment
        assert "**Risk Level:** LOW" in comment
        assert "0 violation(s)" in comment

    def test_single_violation(self):
        v = make_violation()
        review = ReviewResult(violations=[v], risk_level="high", summary="Issue found")
        comment = generate_comment(review, mode="advisory")
        assert "test-rule" in comment
        assert "suspicious_code()" in comment
        assert "This looks risky" in comment
        assert "Refactor it" in comment
        assert "src/main.py:42" in comment
        assert "1 violation(s)" in comment

    def test_multiple_violations_grouped_by_severity(self):
        v_critical = make_violation(rule_name="critical-rule", severity="critical")
        v_low = make_violation(rule_name="low-rule", severity="low")
        v_high = make_violation(rule_name="high-rule", severity="high")
        review = ReviewResult(
            violations=[v_low, v_critical, v_high],
            risk_level="critical",
            summary="Multiple issues",
        )
        comment = generate_comment(review, mode="advisory")
        critical_pos = comment.index("critical-rule")
        high_pos = comment.index("high-rule")
        low_pos = comment.index("low-rule")
        assert critical_pos < high_pos < low_pos

    def test_advisory_mode_text(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        comment = generate_comment(review, mode="advisory")
        assert "Advisory mode" in comment
        assert "No code is blocked" in comment

    def test_enforcement_mode_text(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        comment = generate_comment(review, mode="enforcement")
        assert "Enforcement mode" in comment
        assert "Critical violations will fail" in comment

    def test_governance_url_included(self):
        v = make_violation(governance_url="https://docs.example.com/rule")
        review = ReviewResult(violations=[v], risk_level="medium", summary="Issue")
        comment = generate_comment(review, mode="advisory")
        assert "https://docs.example.com/rule" in comment
        assert "Learn more" in comment

    def test_more_than_twenty_violations_truncated(self):
        violations = [
            make_violation(rule_name=f"rule-{i}", severity="low")
            for i in range(25)
        ]
        review = ReviewResult(
            violations=violations,
            risk_level="low",
            summary="25 issues",
        )
        comment = generate_comment(review, mode="advisory")
        assert "showing top 20" in comment
        assert "5 additional violation(s)" in comment
        assert "25 violation(s)" in comment

    def test_exactly_twenty_violations_no_truncation(self):
        violations = [
            make_violation(rule_name=f"rule-{i}", severity="low")
            for i in range(20)
        ]
        review = ReviewResult(
            violations=violations,
            risk_level="low",
            summary="20 issues",
        )
        comment = generate_comment(review, mode="advisory")
        assert "showing top" not in comment
        assert "20 violation(s)" in comment

    def test_risk_level_emoji_mapping(self):
        for risk, emoji_char in [("critical", "🚨"), ("high", "⚠️"), ("medium", "⚡"), ("low", "ℹ️")]:
            review = ReviewResult(violations=[], risk_level=risk, summary="Test")
            comment = generate_comment(review, mode="advisory")
            assert emoji_char in comment

    def test_violation_without_line_number(self):
        v = make_violation(line=None, file_path="src/main.py")
        review = ReviewResult(violations=[v], risk_level="medium", summary="Issue")
        comment = generate_comment(review, mode="advisory")
        assert "src/main.py:None" not in comment
        assert "src/main.py" in comment

    def test_feedback_instructions_in_footer(self):
        review = ReviewResult(violations=[], risk_level="low", summary="Clean")
        comment = generate_comment(review, mode="advisory")
        assert "Feedback?" in comment
        assert "(accurate)" in comment
        assert "(false positive)" in comment
