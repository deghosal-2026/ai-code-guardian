# AI Code Guardian

[![CI](https://github.com/deghosal-2026/ai-code-guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/deghosal-2026/ai-code-guardian/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

AI Code Governance CI Bot — detects AI-generated code in pull requests, enforces governance policies, and tracks AI code quality metrics across your organization.

## What It Does

- **Detects** AI-attributed code in PR diffs using marker-based heuristics (Copilot, Cursor, Claude Code signatures)
- **Reviews** code against a configurable governance policy — checks for hallucinated APIs, missing error handling, hardcoded secrets
- **Labels** PRs with risk levels (`low` / `medium` / `high` / `critical`)
- **Comments** with educational feedback — explains *why* a pattern is risky, not just flags it
- **Reports** metrics on a built-in dashboard — AI code percentage, violation trends, false positive rate
- **Blocks** (optional) merges that violate critical policies, after trust is established

## Quick Start

Add the following workflow to `.github/workflows/guardian.yml`:

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

Create a `guardian-policy.yml` in your repo root:

```yaml
mode: advisory  # or "enforcement"
detection: marker
rules:
  - name: hallucinated-api
    severity: high
    enabled: true
  - name: missing-error-handling
    severity: medium
    enabled: true
  - name: hardcoded-secrets
    severity: critical
    enabled: true
```

## Governance Model

Guardian follows an **advisory-first** approach:

| Phase | Behavior | Duration |
|---|---|---|
| Trust-building | Comment + label only, no blocking | 2–3 sprints |
| Enforcement | Block merges on critical policy violations | After team opt-in |

## Commands

```bash
# Analyze a PR
guardian detect --token $GH_TOKEN --repo owner/repo --pr 42

# Start the local dashboard
guardian serve --port 8080

# Validate a policy file
guardian check-config --policy guardian-policy.yml

# Print version
guardian version
```

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `GUARDIAN_TOKEN` | GitHub API token | `INPUT_GITHUB_TOKEN` |
| `GUARDIAN_REPO` | Repository (`owner/name`) | `GITHUB_REPOSITORY` |
| `GUARDIAN_POLICY_PATH` | Path to policy YAML | `guardian-policy.yml` |
| `GUARDIAN_AUDIT_DIR` | Directory for audit logs | `~/.guardian/audit` |
| `GUARDIAN_DEBUG` | Enable debug logging | `false` |

## Dashboard

Guardian includes a local dashboard server:

```bash
guardian serve --port 8080 --audit-dir /path/to/audit
```

Open http://localhost:8080/dashboard to view:

- Total PRs analyzed and AI code percentage
- Violations grouped by rule
- Violation trends over the last 30 days
- Recent PRs with risk levels and violation counts

The dashboard also exposes a JSON API at `/api/stats` and Prometheus metrics at `/metrics`.

## Architecture

```
src/guardian/
├── detector/    # AI code detection (marker-based)
├── policy/      # YAML policy loading & validation
├── reviewer/    # Rule evaluation engine
├── pr/          # GitHub API client, commenting, labeling, check runs
├── audit/       # Audit log (append-only JSONL)
├── metrics/     # Dashboard metrics collector & Prometheus exporter
├── server/      # FastAPI dashboard server
├── cli.py       # CLI entry point
├── action.py    # GitHub Action pipeline
└── config.py    # Configuration model
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Lint
ruff check src/

# Build Docker image
docker build -t guardian .
docker run --rm guardian version
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

MIT
