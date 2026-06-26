# Architecture — AI Code Guardian

## Overview

Guardian is a modular Python application that runs as a GitHub Action. It fetches PR diffs, detects AI-generated code, applies governance rules, posts results back to GitHub, and logs everything to an audit trail for dashboard/metrics.

## Data Flow

```
GitHub Trigger (PR / push)
        │
        ▼
┌──────────────────┐
│  action.py        │  Entry point — receives GITHUB_TOKEN, repo, PR
│  (GitHub Action)  │  Parses config, orchestrates pipeline
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  cli.py           │  CLI frontend (also used standalone)
│  guardian detect  │  Delegates to run_detect()
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│config  │ │pr.client     │  GET /repos/{repo}/pulls/{pr}
│.py     │ │(GitHubClient)│  Returns unified diff
│load    │ └──────┬───────┘
│policy  │        │
└───┬────┘        ▼
    │    ┌──────────────┐
    │    │detector/     │  Scan diff for AI attribution
    │    │marker.py     │  markers (Copilot, Cursor, Claude)
    │    │              │  → List[DetectionResult]
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │reviewer/     │  Apply enabled policy rules to
    │    │engine.py     │  AI-detected files only
    │    │              │  → ReviewResult(violations, risk_level)
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │pr/           │  Post comment → POST /issues/{pr}/comments
    │    │commentator   │  Apply label → DELETE+POST /issues/{pr}/labels
    │    │labeler       │  Create check run → POST /check-runs
    │    │check_run     │
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │audit/        │  Append JSONL entry to
    │    │logger.py     │  {audit_dir}/{repo}/audit.jsonl
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐     ┌────────────────┐
    │    │metrics/      │────▶│  server/       │
    │    │collector.py  │     │  app.py        │
    │    └──────────────┘     │  FastAPI       │
    │                         │  /dashboard    │
    │                         │  /api/stats    │
    │                         │  /metrics      │
    │                         └────────────────┘
    │
    ▼ (exit code)
  0 = pass/advisory
  1 = error
  2 = enforcement + critical
```

## Component Details

### 1. Entry Points

| Module | Purpose |
|--------|---------|
| `action.py` | GitHub Action pipeline — parses inputs, loads config, calls `run_detect()`, handles errors, exits with code |
| `cli.py` | CLI frontend — argparse-based, dispatches to detect/serve/check-config/version |

### 2. Configuration

| Module | Purpose |
|--------|---------|
| `config.py` | `GuardianConfig` pydantic model — validates token, repo (owner/name format), policy path, audit dir, verbose flag |
| `policy/loader.py` | Loads YAML policy file, validates via pydantic (`PolicyConfig`, `RuleConfig`), returns deep-copied default if missing |

### 3. Detection

| Module | Purpose |
|--------|---------|
| `detector/marker.py` | Regex-based marker scanner — 7 patterns across Copilot, Cursor, Claude Code. Case-insensitive. Only scans `+` lines in unified diffs. Returns `List[DetectionResult]` with per-file confidence (medium for 1 match, high for 2+ same tool) |

### 4. Review

| Module | Purpose |
|--------|---------|
| `reviewer/engine.py` | `evaluate()` iterates enabled policy rules, calls each rule function, aggregates violations, computes risk level (max severity) |
| `reviewer/rules.py` | 3 built-in rules: `hallucinated-api` (known-API registry + lowercase skip), `missing-error-handling` (bare except regex), `hardcoded-secrets` (7 regex patterns, test-file skip) |
| `reviewer/models.py` | `Violation` dataclass (rule_name, severity, file_path, line, pattern_found, explanation, remediation), `ReviewResult` (violations, risk_level, summary) |

### 5. PR Integration

| Module | Purpose |
|--------|---------|
| `pr/client.py` | `GitHubClient` — REST API wrapper with rate-limit backoff (429), server error retry (500, 3 attempts), token safety. Methods: get_pr_diff, get_commit_diff, get_file_content, post_comment, add_label, remove_label, create_check_run, update_check_run, get_reactions, post_reaction |
| `pr/commentator.py` | Generates Markdown comment — severity-grouped collapsible `<details>`, max 20 violations (truncate with note), governance link, feedback footer, mode indicator |
| `pr/labeler.py` | `apply_risk_label()` — removes all existing `guardian:*` labels, applies new risk label. Graceful 404 handling for non-existent labels |
| `pr/check_run.py` | `generate_check_run_output()` — structured Check Run with risk level, AI stats, violation text. `determine_conclusion()` — advisory → `neutral`, enforcement + critical → `failure`, else `success` |

### 6. Audit Trail

| Module | Purpose |
|--------|---------|
| `audit/models.py` | `AuditEntry` dataclass — auto-generated UUID event_id, ISO 8601 timestamp, nested dataclass reconstruction from dicts |
| `audit/logger.py` | Append-only JSONL writer — `{audit_dir}/{repo_safe}/audit.jsonl`, `append()` one entry per analysis, `read(since)` with optional timestamp filter, auto-creates directories |

### 7. Metrics & Dashboard

| Module | Purpose |
|--------|---------|
| `metrics/collector.py` | `MetricsCollector` — reads audit entries, computes 7 properties (total_prs, ai_prs, ai_code_pct, violations_by_rule, violation_trends, false_positive_rate, recent_prs) |
| `metrics/prometheus.py` | Prometheus-format gauge metrics export |
| `server/app.py` | FastAPI server — GET /dashboard (Jinja2 HTML), GET /api/stats (JSON), GET /metrics (Prometheus) |
| `server/templates/dashboard.html` | Jinja2 template — stats grid, Chart.js bar chart for violation trends, recent PRs table |

## Governance Modes

| Mode | Check Run Conclusion | Comment Footer | Exit Code | Blocks Merge? |
|------|---------------------|----------------|-----------|---------------|
| `advisory` | `neutral` | "No code is blocked" | 0 | No |
| `enforcement` | `failure` if critical, `success` otherwise | "Critical violations will fail the check" | 2 if critical, 0 otherwise | Yes (with branch protection) |

## Data Models

### DetectionResult
```
file_path: str
total_lines: int
matches: List[MarkerMatch]
confidence: str  # "low" | "medium" | "high"
```

### Violation
```
rule_name: str
severity: str  # "low" | "medium" | "high" | "critical"
file_path: str
line: Optional[int]
pattern_found: str
explanation: str
remediation: str
```

### ReviewResult
```
violations: List[Violation]
risk_level: str
summary: str
```

### AuditEntry
```
version: int = 1
timestamp: str (auto ISO 8601)
event_id: str (auto UUID)
repo: str
pr_number: Optional[int]
commit_sha: Optional[str]
action: str  # "analysis" | "error"
detection_results: List[DetectionResult]
violations: List[Violation]
risk_level: Optional[str]
feedback: Optional[dict]
duration_ms: Optional[int]
error: Optional[str]
```

## Key Design Decisions

1. **Advisory-first governance** — Start in advisory mode (comment + label only). Switch to enforcement only after teams trust the signal quality (AGENTS.md).

2. **Rules scan only AI-detected files** — `hallucinated-api`, `missing-error-handling`, and `hardcoded-secrets` only scan files where detection confidence is `high` or `medium`. This reduces false positives but means violations in non-AI files are not flagged.

3. **Lowercase-first-segment skip** — Dotted calls like `payment_gateway.charge()` are treated as local variables (not external APIs) because the first segment starts with lowercase. Reduces false positives from local variable method calls.

4. **File-per-repo audit isolation** — Audit logs are stored in `{audit_dir}/{repo_safe}/audit.jsonl` so multiple repos don't collide.

5. **Docker-based Action** — Guardian runs as a Docker container in CI for reproducible builds and dependency isolation.

## Project Structure

```
src/guardian/
├── __init__.py
├── cli.py                    # CLI entry point
├── action.py                 # GitHub Action pipeline
├── config.py                 # GuardianConfig model
├── detector/
│   ├── __init__.py
│   ├── marker.py             # Marker-based detection
│   └── models.py             # DetectionResult, MarkerMatch
├── policy/
│   ├── __init__.py
│   ├── loader.py             # YAML loader + validator
│   └── models.py             # PolicyConfig, RuleConfig
├── reviewer/
│   ├── __init__.py
│   ├── engine.py             # evaluate(), compute_risk_level()
│   ├── rules.py              # Built-in rule implementations
│   └── models.py             # Violation, ReviewResult
├── pr/
│   ├── __init__.py
│   ├── client.py             # GitHubClient (REST API)
│   ├── commentator.py        # PR comment generation
│   ├── labeler.py            # Risk label management
│   └── check_run.py          # Check Run output
├── audit/
│   ├── __init__.py
│   ├── models.py             # AuditEntry dataclass
│   └── logger.py             # Append-only JSONL logger
├── metrics/
│   ├── __init__.py
│   ├── collector.py          # MetricsCollector
│   └── prometheus.py         # Prometheus export
└── server/
    ├── __init__.py
    ├── app.py                # FastAPI server
    └── templates/
        └── dashboard.html    # Jinja2 template
tests/
├── test_detector.py          # 23 tests
├── test_policy.py            # 9 tests
├── test_reviewer.py          # 20 tests
├── test_commentator.py       # 12 tests
├── test_labeler.py           # 8 tests
├── test_check_run.py         # 15 tests
├── test_pr_client.py         # 20 tests
├── test_audit.py             # 20 tests
├── test_cli.py               # 19 tests
├── test_metrics.py           # 15 tests
└── test_action.py            # 8 tests
```
