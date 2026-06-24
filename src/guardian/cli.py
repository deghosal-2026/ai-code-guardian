import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="guardian")
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser("detect", help="Run analysis on a PR or commit")
    detect.add_argument("--token", required=True)
    detect.add_argument("--repo", required=True)
    detect.add_argument("--pr", type=int, default=None)
    detect.add_argument("--commit", default=None)
    detect.add_argument("--policy", default="guardian-policy.yml")
    detect.add_argument("--audit-dir", default="~/.guardian/audit")
    detect.add_argument("--verbose", action="store_true")

    sub.add_parser("serve", help="Start the local dashboard server")
    sub.add_parser("check-config", help="Validate a policy file")
    sub.add_parser("generate-pages", help="Build static dashboard HTML")
    sub.add_parser("version", help="Print version")

    args = parser.parse_args()

    if args.command == "version":
        from importlib.metadata import version
        print(f"ai-code-guardian v{version('ai-code-guardian')}")
        sys.exit(0)

    if args.command == "detect":
        from guardian.action import run_detect
        sys.exit(run_detect(args))

    if args.command == "serve":
        print("guardian serve — coming soon")
        sys.exit(0)

    if args.command == "check-config":
        print("guardian check-config — coming soon")
        sys.exit(0)

    if args.command == "generate-pages":
        print("guardian generate-pages — coming soon")
        sys.exit(0)
