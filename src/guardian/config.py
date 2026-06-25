from guardian.policy.loader import load_policy_file
from guardian.policy.models import PolicyConfig


def load_policy(path: str | None = None) -> PolicyConfig:
    return load_policy_file(path or "guardian-policy.yml")
