# TODO — AI Code Guardian

## Project Status

- **PRD:** docs/PRD.md (approved)
- **SPEC:** docs/SPEC.md (approved)
- **Test count:** 105 tests, all passing

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
- `audit/models.py` — AuditEntry dataclass with auto-generated timestamp/event_id, to_json() serialization
- `audit/logger.py` — AppendLogger (append-only JSONL, file-per-repo isolation, read with since filter)
- `tests/test_audit.py` — 20 tests
- Closed: #10, #11

### ✅ M5: CLI Framework (done)
- `config.py` — GuardianConfig pydantic model with token/repo validation
- `cli.py` — detect orchestrates full flow, serve/check-config/version implemented
- `action.py` — full detect pipeline with error handling, audit logging, exit codes
- `tests/test_cli.py` — 19 tests
- Closed: #18, #19
- **Open: #20 (M5-DOCS)**

### 🔜 M6: Dashboard
- **Open:** #21, #22, #23, #24 (M6-DEV), #25 (M6-TEST), #26 (M6-DOCS)
- `metrics/`, `server/` — stubs exist

### 🔜 M7: Action Packaging
- **Open:** #27 (M7-DEV), #28 (M7-TEST), #29 (M7-RELEASE)
- `action.yml`, `Dockerfile` — stubs exist

### 🔜 M8: Reference Files
- **Open:** #30 (M8-DEV)
- `guardian-policy.yml` exists, `.github/workflows/guardian.yml` does not

### 🔜 M9: Documentation & Release
- **Open:** #31, #32 (M9-DOCS), #33 (M9-RELEASE)
- `README.md` — exists but needs full rewrite

---

## Next Up: M6 (Dashboard)

The dashboard teaml reads audit logs and exposes metrics via FastAPI + Prometheus:
1. `metrics/collector.py` — MetricsCollector reading audit entries
2. `metrics/prometheus.py` — Prometheus-format /metrics export
3. `server/app.py` — FastAPI server with /dashboard, /api/stats, /metrics
4. `guardian serve` CLI command (wired in M5, needs server module)

## Open Issues Summary

| Milestone | Open |
|-----------|------|
| M3: PR Integration | 0 |
| M4: Audit Trail | 0 |
| M5: CLI Framework | 1 (docs only) |
| M6: Dashboard | 6 |
| M7: Action Packaging | 3 |
| M8: Reference Files | 1 |
| M9: Docs & Release | 3 |
| **Total** | **14** |
