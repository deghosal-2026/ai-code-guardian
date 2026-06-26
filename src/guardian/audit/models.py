import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4


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

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.event_id:
            self.event_id = str(uuid4())

    def to_json(self) -> str:
        d = asdict(self)
        d["action"] = str(self.action) if self.action else None
        d["feedback"] = str(self.feedback) if self.feedback else None
        if d["violations"] is not None:
            d["violations"] = [_violation_to_dict(v) for v in d["violations"]]
        if d["detection_results"] is not None:
            d["detection_results"] = [_detection_to_dict(r) for r in d["detection_results"]]
        return json.dumps(d, default=str, ensure_ascii=False)


def _violation_to_dict(v) -> dict:
    if hasattr(v, "__dataclass_fields__"):
        return asdict(v)
    return dict(v)


def _detection_to_dict(d) -> dict:
    if hasattr(d, "__dataclass_fields__"):
        return asdict(d)
    return dict(d)
