# tests — Test Suite

Unit and integration tests for all Guardian modules.

- `test_detector.py` — Marker detection patterns and false positives
- `test_reviewer.py` — Policy engine and rule evaluation
- `test_policy.py` — YAML loading and schema validation
- `test_pr_client.py` — GitHub API client (mocked HTTP)
- `test_commentator.py` — Comment format and edge cases
- `test_labeler.py` — Risk level label logic
- `test_check_run.py` — Check Run output format
- `test_audit.py` — Audit log append/read/immutability
- `test_cli.py` — Argument parsing and exit codes
- `fixtures/` — Sample PR diffs and policy files for tests
