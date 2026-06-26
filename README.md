# AI Code Guardian

[![CI](https://github.com/deghosal-2026/ai-code-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/deghosal-2026/ai-code-guardian/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

AI Code Governance CI Bot — detects AI-generated code in pull requests, enforces governance policies, and tracks AI code quality metrics across your organization.

## Features

- **Detect** AI-attributed code in PR diffs — Copilot, Cursor, and Claude Code attribution markers
- **Review** code against a configurable governance policy — hallucinated APIs, missing error handling, hardcoded secrets
- **Label** PRs with risk levels — `guardian:low` / `guardian:medium` / `guardian:high` / `guardian:critical`
- **Comment** with educational feedback — explains *why* a pattern is risky, not just flags it
- **Block** merges on critical violations (optional enforcement mode) — requires branch protection rules
- **Dashboard** with metrics — AI code percentage, violation trends, false positive rate, recent PRs
- **Audit trail** — append-only JSONL log of every analysis
- **Docker** — packaged as a Docker image for reproducible CI runs

## Quick Start

### 1. Add the Workflow

Create `.github/workflows/guardian.yml`:

```yaml
name: AI Code Guardian
on:
  pull_request:
    types: [opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
  checks: write
jobs:
  guardian:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: deghosal-2026/ai-code-guardian@v1
        with:
          github_token: ${{ github.token }}
```

### 2. Create a Policy

Create `guardian-policy.yml` in your repo root:

```yaml
version: 1
mode: advisory              # "advisory" (comment+label) or "enforcement" (block critical)
detection: marker           # Detection backend (marker only in Phase 1)

rules:
  - name: hallucinated-api
    severity: critical
    enabled: true
    description: Detects API calls that don't exist in standard or common third-party libraries
  - name: missing-error-handling
    severity: high
    enabled: true
    description: Flags bare exception handlers and missing null checks in AI-generated code
  - name: hardcoded-secrets
    severity: critical
    enabled: true
    description: Detects API keys, tokens, and passwords hardcoded in source code
```

### 3. Open a PR

Guardian runs automatically on every PR. You'll see:

| Output | Description |
|--------|-------------|
| 💬 **Comment** | Violations grouped by severity in collapsible blocks |
| 🏷 **Label** | `guardian:low` / `guardian:medium` / `guardian:high` / `guardian:critical` |
| ✅ **Check Run** | Risk level, AI code stats, violation count |

## Governance Model

Guardian follows an **advisory-first** approach:

| Phase | Mode | Behavior | Duration |
|---|---|---|---|
| Trust-building | `advisory` | Comment + label only, check run always `neutral` | 2–3 sprints |
| Enforcement | `enforcement` | Check run `failure` on critical → blocks merge | After team opt-in |

### Advisory Mode (default)

```yaml
mode: advisory
```

- PR comment with violations grouped by severity
- Risk label applied (`guardian:critical`, etc.)
- Check run always shows `neutral` — never blocks
- Workflow exits with code 0
- Comment footer: "No code is blocked"

### Enforcement Mode

```yaml
mode: enforcement
```

- Same comment + label behavior as advisory
- Check run returns `failure` for critical risk level — blocks merge
- Low/medium/high risk still return `success`
- Workflow exits with code 2 for critical violations
- Comment footer: "Critical violations will fail the check"
- Requires [branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule) configured to require "AI Code Guardian" check

### Switching Modes

Start in advisory mode for 2–3 sprints to build trust. Monitor the dashboard for false positive rate. When the team is confident in the signal quality, switch to enforcement.

## Built-in Rules

| Rule | Severity | What It Detects |
|------|----------|-----------------|
| `hallucinated-api` | critical | Function calls to APIs that look real but don't exist in stdlib or common third-party libraries |
| `missing-error-handling` | high | Bare `except:` blocks that catch all exceptions including SystemExit |
| `hardcoded-secrets` | critical | API keys (`sk-...`), tokens (`ghp_...`), AWS keys (`AKIA...`), private keys, hardcoded credentials |

Rules only scan files detected as AI-generated (confidence ≠ low) — reducing false positives on human-written code.

## CLI Commands

```bash
# Analyze a PR
guardian detect --token $GH_TOKEN --repo owner/repo --pr 42

# Analyze a commit
guardian detect --token $GH_TOKEN --repo owner/repo --commit SHA

# Start dashboard server
guardian serve --port 8080

# Validate a policy file
guardian check-config --policy guardian-policy.yml

# Print version
guardian version
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Pass — no violations or advisory mode |
| 1 | Error — config, API, or analysis failure |
| 2 | Enforcement block — critical violation in enforcement mode |

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GUARDIAN_TOKEN` | GitHub API token | `INPUT_GITHUB_TOKEN` |
| `GUARDIAN_REPO` | Repository (`owner/name`) | `GITHUB_REPOSITORY` |
| `GUARDIAN_POLICY_PATH` | Path to policy YAML | `guardian-policy.yml` |
| `GUARDIAN_AUDIT_DIR` | Directory for audit logs | `~/.guardian/audit` |
| `GUARDIAN_DEBUG` | Enable debug logging | `false` |

Set automatically by the GitHub Action. Override for local testing.

## Dashboard

Guardian includes a local dashboard server for viewing metrics:

```bash
guardian serve --port 8080 --audit-dir ~/.guardian/audit
```

| Endpoint | Description |
|----------|-------------|
| `GET /dashboard` | HTML dashboard — stats grid, violation trends bar chart, recent PRs table |
| `GET /api/stats` | JSON API — all metrics (for custom dashboards) |
| `GET /metrics` | Prometheus-format metrics (for scraping) |

### Dashboard Metrics

| Metric | Description |
|--------|-------------|
| PRs Analyzed | Total unique PRs in the audit log |
| AI Code % | Percentage of files flagged as AI-generated |
| False Positive Rate | Ratio of 👎 to (👍 + 👎) feedback reactions |
| Violations by Rule | Count per rule type |
| Violation Trends | Daily violation counts over last 30 days (bar chart) |
| Recent PRs | Last 10 PRs with risk level and violation count |

## Audit Log

Every analysis is recorded in an append-only JSONL file:

```
~/.guardian/audit/
└── owner_repo/
    └── audit.jsonl
```

Each entry: event_id, timestamp, repo, pr_number, action, detection_results, violations, risk_level, feedback, duration_ms.

## Docker

```bash
# Build locally
docker build -t guardian .

# Run version check
docker run --rm guardian version

# Analyze a PR
docker run --rm \
  -e GUARDIAN_TOKEN=$GH_TOKEN \
  -e GUARDIAN_REPO=owner/repo \
  -e GUARDIAN_PR_NUMBER=42 \
  guardian detect

# Start dashboard
docker run --rm -p 8080:8080 \
  -v ~/.guardian/audit:/app/audit \
  guardian serve --port 8080 --audit-dir /app/audit
```

## Architecture

```
src/guardian/
├── cli.py           CLI entry point
├── action.py        GitHub Action pipeline
├── config.py        Configuration model
├── detector/        AI code detection (marker-based)
├── policy/          Policy loading & validation
├── reviewer/        Rule evaluation engine
├── pr/              GitHub API client, commenting, labeling, check runs
├── audit/           Append-only JSONL audit log
├── metrics/         Dashboard metrics collector & Prometheus exporter
└── server/          FastAPI dashboard server
```

See [docs/architecture.md](docs/architecture.md) for the full architecture.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (167+ tests)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_detector.py -v

# Run with coverage
python -m pytest tests/ --cov=src/guardian

# Lint
ruff check src/

# Build Docker image
docker build -t guardian .
docker run --rm guardian version
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Full architecture, data flow, component details |
| [docs/user-guide.md](docs/user-guide.md) | Comprehensive user guide — setup, policy, PR workflow, dashboard, Docker, troubleshooting |
| [docs/test-plan.md](docs/test-plan.md) | E2E test scenarios and results |
| [docs/e2e-results.md](docs/e2e-results.md) | Completed E2E test results |

## License

MIT
