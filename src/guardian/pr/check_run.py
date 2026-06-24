"""Check Run output generator — builds the GitHub Checks tab summary."""


def generate_check_run_output(review: object, stats: dict) -> dict:
    raise NotImplementedError("TODO: implement check run output")


def determine_conclusion(review: object, mode: str) -> str:
    raise NotImplementedError("TODO: implement conclusion logic")
