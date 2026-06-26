"""Tests for the risk level labeler (pr/labeler.py)."""

import pytest
from guardian.pr.labeler import apply_risk_label, compute_risk_level, RISK_LABELS
from guardian.reviewer.models import Violation


class MockGitHubClient:
    def __init__(self):
        self.labels: list[str] = []
        self.removed: list[str] = []

    def add_label(self, pr_number: int, label: str) -> None:
        self.labels.append(label)

    def remove_label(self, pr_number: int, label: str) -> None:
        self.removed.append(label)


class MockGitHubClientRemoveFails:
    def add_label(self, pr_number: int, label: str) -> None:
        self.added = label

    def remove_label(self, pr_number: int, label: str) -> None:
        raise Exception("Network error")


class TestApplyRiskLabel:
    def test_removes_old_labels_before_adding_new(self):
        client = MockGitHubClient()
        apply_risk_label(client, 42, "high")
        for label in RISK_LABELS.values():
            assert label in client.removed
        assert "guardian:high" in client.labels
        assert len(client.labels) == 1

    def test_applies_correct_label_per_risk_level(self):
        for risk_level, expected_label in RISK_LABELS.items():
            client = MockGitHubClient()
            apply_risk_label(client, 42, risk_level)
            assert client.labels == [expected_label]

    def test_handles_remove_failure_gracefully(self):
        client = MockGitHubClientRemoveFails()
        apply_risk_label(client, 42, "low")
        assert client.added == "guardian:low"


class TestComputeRiskLevel:
    def test_empty_list_returns_low(self):
        assert compute_risk_level([]) == "low"

    def test_single_violation_returns_its_severity(self):
        v = Violation(
            rule_name="test", severity="high", file_path="f", line=1,
            pattern_found="", explanation="", remediation="",
        )
        assert compute_risk_level([v]) == "high"

    def test_returns_highest_severity(self):
        v_low = Violation(
            rule_name="test", severity="low", file_path="f", line=1,
            pattern_found="", explanation="", remediation="",
        )
        v_critical = Violation(
            rule_name="test", severity="critical", file_path="f", line=1,
            pattern_found="", explanation="", remediation="",
        )
        assert compute_risk_level([v_low, v_critical]) == "critical"

    def test_all_severities_ordered_correctly(self):
        for sev in ["low", "medium", "high", "critical"]:
            v = Violation(
                rule_name="test", severity=sev, file_path="f", line=1,
                pattern_found="", explanation="", remediation="",
            )
            assert compute_risk_level([v]) == sev

    def test_unknown_severity_treated_as_lowest(self):
        v = Violation(
            rule_name="test", severity="unknown", file_path="f", line=1,
            pattern_found="", explanation="", remediation="",
        )
        v2 = Violation(
            rule_name="test2", severity="medium", file_path="f", line=1,
            pattern_found="", explanation="", remediation="",
        )
        assert compute_risk_level([v, v2]) == "medium"
