import json
import os
from argparse import Namespace


def run_detect(args: Namespace) -> int:
    token = args.token or os.environ.get("INPUT_GITHUB_TOKEN", "")
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")

    pr_number = args.pr
    if pr_number is None and "GITHUB_EVENT_PATH" in os.environ:
        event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
        if "pull_request" in event:
            event_name = os.environ.get("GITHUB_EVENT_NAME", "")
            if event_name in ("pull_request", "pull_request_target"):
                pr_number = event["pull_request"]["number"]

    commit_sha = args.commit or os.environ.get("GITHUB_SHA")

    print(f"Guardian analyzing {repo} PR#{pr_number or commit_sha}")
    print("Detection engine — coming soon")
    return 0
