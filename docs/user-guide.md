# AI Code Guardian — User Guide

## What is Guardian?

Guardian is a CI bot that detects AI-generated code in pull requests, enforces governance policies, and tracks AI code quality metrics. It runs as a GitHub Action in your workflow.

---

## Quick Start

### 1. Add the Workflow

Create `.github/workflows/guardian.yml` in your repository:

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
      - uses: deghosal-2026/ai-code-guardian@v1
        with:
          github_token: ${{ github.token }}
```

### 2. Create a Policy File

Create `guardian-policy.yml` in your repo root:

```yaml
version: 1
mode: advisory         # "advisory" or "enforcement"
detection: marker      # "marker" only (Phase 1)

rules:
  - name: hallucinated-api
    severity: critical
    enabled: true
  - name: missing-error-handling
    severity: high
    enabled: true
  - name: hardcoded-secrets
    severity: critical
    enabled: true
```

### 3. Open a PR

Guardian runs automatically on every PR. You'll see:
- A **comment** on the PR with violations grouped by severity
- A **label** (`guardian:low` / `guardian:medium` / `guardian:high` / `guardian:critical`)
- A **check run** in the Checks tab

---

## Governance Model

Guardian follows an **advisory-first** approach:

| Phase | Mode | Behavior | Duration |
|---|---|---|---|
| Trust-building | `advisory` | Comment + label only, check run always `neutral` | 2–3 sprints |
| Enforcement | `enforcement` | Check run `failure` on critical violations, blocks merge | After team opt-in |

Switch from `advisory` to `enforcement` in `guardian-policy.yml` when your team is ready.

### Enabling Enforcement Mode

To enable blocking:

1. **Set the policy:**
   ```yaml
   # guardian-policy.yml
   mode: enforcement
   ```

2. **Configure branch protection** (GitHub repo Settings → Branches):
   - Add a branch protection rule for `main`
   - Check ☑ "Require status checks to pass before merging"
   - Add "AI Code Guardian" as a required check
   - Optionally check ☑ "Require branches to be up to date"

3. **Verify:**
   - Open a test PR with critical violations
   - The check run should show as ❌ failing
   - The PR merge button should be blocked
   - The PR comment says "ENFORCEMENT MODE — Critical violations will fail the check"

### What Changes in Enforcement Mode

| Aspect | Advisory | Enforcement |
|---|---|---|
| Check run conclusion | `neutral` | `failure` on critical, `success` otherwise |
| Comment footer | "No code is blocked" | "Critical violations will fail the check" |
| Workflow exit code | 0 (pass) | 2 (enforcement + critical) |
| Merge blocked? | No | Yes, if check fails |

---

## Policy Reference

### Full Schema

```yaml
version: 1                          # Schema version (required)
mode: advisory                      # "advisory" or "enforcement"
detection: marker                   # Detection backend ("marker" only in Phase 1)

rules:
  - name: hallucinated-api          # Rule identifier
    severity: critical              # low | medium | high | critical
    enabled: true                   # Enable or disable the rule
    description: >                  # Optional — shown in PR comments
      Detects API calls that match known hallucination patterns.
```

### Built-in Rules

| Rule | Severity | What It Detects |
|---|---|---|
| `hallucinated-api` | critical | Function calls to APIs that look real but don't exist in stdlib or common third-party libraries |
| `missing-error-handling` | high | Bare `except:`, missing try/finally, absent null checks after API calls |
| `hardcoded-secrets` | critical | API keys, tokens, passwords hardcoded in source (`sk-...`, `AKIA...`, etc.) |

### Custom Rules

Rules are loaded from `guardian-policy.yml`. Disable a rule by setting `enabled: false`. Custom rule development is planned for a future phase.

---

## PR Workflow

When Guardian runs on a PR, it produces three outputs:

### 1. PR Comment

A comment with this structure:

```
🤖 AI Code Guardian — Review Summary

ℹ️ Risk Level: HIGH (3 violation(s))

<details>
<summary>🚨 Rule: hardcoded-secrets — src/config.py:8</summary>

Pattern: sk-xxx

API key detected in source code. Use a secrets manager or environment
variables instead.

Recommendation: Replace with a reference to your secrets store.
</details>

<details>
<summary>⚠️ Rule: hallucinated-api — src/api.py:15</summary>
...
</details>

---
ℹ️ Advisory mode — No code is blocked.

Feedback? React 👍 (accurate) or 👎 (false positive) to this comment.
```

**Format rules:**
- Violations grouped by severity (critical → low)
- Each violation in a collapsible `<details>` block
- Max 20 violations shown (with a note if truncated)
- Footer shows mode and feedback instructions

**Feedback:**
- React **👍** = accurate detection (improves FPR metrics)
- React **👎** = false positive (flagged for review)

### 2. Risk Label

Guardian applies a `guardian:*` label:

| Label | Meaning |
|---|---|
| `guardian:low` | No violations or only low-severity findings |
| `guardian:medium` | At least one medium-severity violation |
| `guardian:high` | At least one high-severity violation |
| `guardian:critical` | At least one critical-severity violation |

Old labels are cleaned up before applying the new one.

### 3. Check Run

Visible in the Checks tab of the PR:

```
Risk Level: HIGH
AI Code: 2/10 files (20%)
Violations: 3
FPR: 0%
```

**Conclusion logic:**

| Mode | Risk Level | Conclusion | Merge Blocked? |
|---|---|---|---|
| Advisory | any | `neutral` | No |
| Enforcement | critical | `failure` | ✅ Yes (with branch protection) |
| Enforcement | low/medium/high | `success` | No |

---

## Audit Trail

All analyses are logged to append-only JSONL files. One file per repository:

```
.guardian/audit/
└── owner/
    └── repo.jsonl
```

Each entry contains: timestamp, event_id, repo, pr_number, action, detection_results, violations, risk_level, duration_ms, feedback.

---

## Dashboard

Guardian includes a local dashboard server.

### Start the server

```bash
guardian serve --port 8080 --audit-dir /path/to/audit
```

### Pages and APIs

| Endpoint | Description |
|---|---|
| `GET /dashboard` | HTML dashboard with stats grid, bar chart, PR table |
| `GET /api/stats?audit_dir=...` | JSON API with all metrics |
| `GET /metrics` | Prometheus-format metrics |

### Dashboard Metrics

| Metric | Description |
|---|---|
| PRs Analyzed | Total unique PRs in the audit log |
| AI Code % | Percentage of files flagged as AI-generated (confidence != low) |
| False Positive Rate | Ratio of disputed to (confirmed + disputed) feedback |
| Rules Triggered | Sum of all violation counts |
| Violations by Rule | Table of rule → count |
| Violation Trends | Daily violation counts over the last 30 days (bar chart) |
| Recent PRs | Table of PRs with risk level, violations, and date |

---

## Commands

```bash
# Analyze a PR
guardian detect --token $GH_TOKEN --repo owner/repo --pr 42

# Analyze a commit
guardian detect --token $GH_TOKEN --repo owner/repo --commit SHA

# Start dashboard server
guardian serve --port 8080

# Validate policy file
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
| `GUARDIAN_MODE` | Override advisory/enforcement | from policy file |

These env vars are set automatically by the GitHub Action.

---

## Docker

Guardian runs as a Docker container. The image is published at the container registry.

```bash
# Build locally
docker build -t guardian .

# Run
docker run --rm -e GUARDIAN_TOKEN=$TOKEN guardian detect --repo owner/repo --pr 42
```

---

## Audit Log

The audit log is an append-only JSONL file at `{audit_dir}/{owner}/{repo}.jsonl`. Each line is a JSON object:

```json
{
  "event_id": "abc123",
  "timestamp": "2026-06-25T12:00:00+00:00",
  "repo": "owner/repo",
  "pr_number": 42,
  "action": "analysis",
  "risk_level": "high",
  "violations": [
    {"rule_name": "hallucinated-api", "severity": "critical", "file_path": "src/api.py", "line": 10}
  ],
  "duration_ms": 1234
}
```

Entry types:
- `analysis` — full detection + review pipeline
- `comment_posted` — PR comment was posted
- `error` — analysis failed



---

## Troubleshooting

### No comment appears on the PR

Check that the workflow has `pull-requests: write` permission. Guardian needs write access to post comments and labels.

### Check run shows "neutral" for critical violations

You're in `advisory` mode. Set `mode: enforcement` in `guardian-policy.yml` to fail checks on critical violations.

### PR already exists, Guardian didn't run

The workflow triggers on `opened`, `synchronize`, and `reopened` events. Re-open the PR or push a new commit to trigger a run.

### "Configuration error: github_token must not be empty"

The `github_token` input is not being passed. Make sure your workflow has:
```yaml
with:
  github_token: ${{ github.token }}
```

### Dashboard is empty

The dashboard reads from the audit log. If no analyses have run (or the audit dir is wrong), the dashboard shows zeros. Pass `--audit-dir` pointing to where Guardian stores its logs.

---

## Architecture

See [docs/architecture.md](architecture.md) for the full architecture document covering data flow, component details, data models, and design decisions.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  PR Diff    │────▶│  Detector    │────▶│  Reviewer    │
│  (GitHub)   │     │  (markers)   │     │  (rules)     │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                    ┌───────────────────────────┤
                    │                           │
                    ▼                           ▼
            ┌──────────────┐           ┌──────────────┐
            │  PR Output   │           │  Audit Log   │
            │  comment     │           │  (JSONL)     │
            │  label       │           └──────┬───────┘
            │  check run   │                  │
            └──────────────┘                  ▼
                                      ┌──────────────┐
                                      │  Dashboard   │
                                      │  (FastAPI)   │
                                      └──────────────┘
```
