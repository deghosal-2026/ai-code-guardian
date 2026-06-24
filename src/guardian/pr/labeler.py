"""Risk level labeler — maps risk level to guardian:* labels."""


def apply_risk_label(client: object, pr_number: int, risk_level: str) -> None:
    raise NotImplementedError("TODO: implement risk labeler")


def compute_risk_level(violations: list) -> str:
    raise NotImplementedError("TODO: implement risk level computation")
