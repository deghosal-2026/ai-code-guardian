# TODO — AI Code Guardian

## Project Status

- **PRD:** docs/PRD.md (approved)
- **SPEC:** docs/SPEC.md (approved)
- **Test count:** 167 tests, all passing

---

## Milestone Status

### ✅ M1: Detection Engine (done)
- `detector/marker.py` — marker-based detection (Copilot, Cursor, Claude Code)
- `detector/models.py` — DetectionResult, MarkerMatch dataclasses
- `detector/style.py` — stub for Phase 2
- `tests/test_detector.py` — 23 tests
- Closed: #5, #6

### ✅ M2: Policy Engine (done)
- `policy/loader.py` — YAML loader + pydantic schema validation
- `policy/models.py` — PolicyConfig, RuleConfig
- `reviewer/rules.py` — 3 built-in rules (hallucinated-api, missing-error-handling, hardcoded-secrets)
- `reviewer/engine.py` — evaluate() + compute_risk_level()
- `config.py` — delegates to policy loader
- `tests/test_policy.py` — 9 tests
- `tests/test_reviewer.py` — 22 tests
- Closed: #7, #8, #9

### ✅ M3: PR Integration (done)
- `pr/client.py` — GitHubClient (diff fetch, comments, labels, check runs, reactions, rate-limit backoff)
- `pr/commentator.py` — generate_comment() with severity-grouped violations, truncation at 20
- `pr/labeler.py` — apply_risk_label() with old-label cleanup
- `pr/check_run.py` — generate_check_run_output(), determine_conclusion()
- `docs/pr-integration.md` — comment format, labels, check runs, feedback, setup guide
- `tests/test_pr_client.py` — 19 tests
- `tests/test_commentator.py` — 12 tests
- `tests/test_labeler.py` — 8 tests
- `tests/test_check_run.py` — 15 tests
- Closed: #12, #13, #14, #15, #16, #17

### ✅ M4: Audit Trail (done)
- `audit/models.py` — AuditEntry dataclass with auto-generated timestamp/event_id, to_json() serialization, nested dataclass reconstruction from dicts
- `audit/logger.py` — AuditLogger (append-only JSONL, file-per-repo isolation, read with since filter)
- `tests/test_audit.py` — 20 tests
- Closed: #10, #11

### ✅ M5: CLI Framework (done)
- `config.py` — GuardianConfig pydantic model with token/repo validation
- `cli.py` — detect orchestrates full flow, serve/check-config/version commands
- `action.py` — full detect pipeline with error handling, audit logging, exit codes, env var support (GUARDIAN_*)
- `tests/test_cli.py` — 19 tests
- Closed: #18, #19
- Closed: #18, #19, #20 (M5-DOCS)

### ✅ M6: Dashboard (done)
- `metrics/collector.py` — MetricsCollector (total_prs, ai_prs, ai_code_pct, violations_by_rule, violation_trends, false_positive_rate, recent_prs)
- `metrics/prometheus.py` — Prometheus-format /metrics export
- `server/app.py` — FastAPI server with /dashboard (HTML), /api/stats (JSON), /metrics (Prometheus)
- `server/templates/dashboard.html` — Jinja2 template with stats grid, bar chart, PR table
- `guardian serve` CLI command
- `tests/test_metrics.py` — 15 tests
- Closed: #21, #22, #23, #24, #25, #26 (M6-DOCS)

### ✅ M7: Action Packaging (done)
- `Dockerfile` — python:3.12-slim, non-root user, proper build order, OCI labels
- `action.yml` — Docker-based GitHub Action with 5 inputs + 3 outputs, GUARDIAN_* env vars
- `tests/test_action.py` — 8 tests (Docker build, container execution, action.yml structure, env vars)
- `.github/workflows/ci.yml` — matrix CI across Python 3.11/3.12, ruff lint, Docker smoke test
- Closed: #27, #28, #29

### ✅ M8: Reference Files (done)
- `guardian-policy.yml` — example policy at repo root
- `.github/workflows/guardian.yml` — example workflow with proper permissions (pull-requests: write, checks: write)
- Closed: #30

### ✅ M9: Documentation & Release (done)
- `README.md` — rewritten with badges, quick start, commands, env vars, dashboard, architecture, development setup
- `CONTRIBUTING.md` — created with dev setup, test commands, code style, PR guidelines
- Closed: #31, #32, #33 (e2e validation)
- All 33 issues across M1-M9 closed

---

## Project Complete

All milestones M1 through M9 are delivered:

- **167 tests**, all passing
- **9 milestones**, 33 issues closed
- **Docker image** builds and runs
- **GitHub Action** with full input/output/env var support
- **Dashboard** with metrics API and HTML interface
- **Full documentation** in README.md and CONTRIBUTING.md
