from dataclasses import dataclass
from typing import Literal


@dataclass
class AuditEntry:
    version: int = 1
    timestamp: str = ""
    event_id: str = ""
    repo: str = ""
    pr_number: int | None = None
    commit_sha: str | None = None
    action: Literal[
        "analysis", "comment_posted", "label_applied",
        "check_run_created", "feedback_received", "error"
    ] = "analysis"
    detection_results: list | None = None
    violations: list | None = None
    risk_level: str | None = None
    feedback: Literal["confirmed", "disputed"] | None = None
    duration_ms: int = 0
    error: str | None = None
