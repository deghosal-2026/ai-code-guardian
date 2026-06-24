"""Built-in policy rules for AI code review.

Each rule is a function:
  (detections, diff, severity) -> list[Violation]
"""


def hallucinated_api(detections: list, diff: str, severity: str) -> list:
    raise NotImplementedError("TODO: implement hallucinated-api rule")


def missing_error_handling(detections: list, diff: str, severity: str) -> list:
    raise NotImplementedError("TODO: implement missing-error-handling rule")


def hardcoded_secrets(detections: list, diff: str, severity: str) -> list:
    raise NotImplementedError("TODO: implement hardcoded-secrets rule")
