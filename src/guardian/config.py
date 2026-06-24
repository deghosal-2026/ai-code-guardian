from guardian.policy.models import PolicyConfig


DEFAULT_POLICY = PolicyConfig(
    version=1,
    mode="advisory",
    detection="marker",
    rules=[
        {"name": "hallucinated-api", "severity": "critical", "enabled": True, "description": ""},
        {"name": "missing-error-handling", "severity": "high", "enabled": True, "description": ""},
        {"name": "hardcoded-secrets", "severity": "critical", "enabled": True, "description": ""},
    ],
)


def load_policy(path: str | None = None) -> PolicyConfig:
    return DEFAULT_POLICY
