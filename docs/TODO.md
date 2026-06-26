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

### 🔜 M4: Audit Trail
- **Open:** #10 (M4-DEV), #11 (M4-TEST)
- `audit/` — stubs exist

### 🔜 M5: CLI Framework
- **Open:** #18 (M5-DEV epic), #19 (M5-TEST), #20 (M5-DOCS)
- `cli.py`, `action.py`, `__main__.py` — partial stubs exist

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

## Next Up: M4 (Audit Trail)

The audit logger is the next dependency for M5+ — it feeds both the CLI flow and the dashboard:
1. `audit/models.py` — AuditEntry dataclass
2. `audit/logger.py` — append-only JSONL logger with file-per-repo isolation
3. `tests/test_audit.py`

## Open Issues Summary

| Milestone | Open |
|-----------|------|
| M3: PR Integration | 0 |
| M4: Audit Trail | 2 |
| M5: CLI Framework | 3 |
| M6: Dashboard | 6 |
| M7: Action Packaging | 3 |
| M8: Reference Files | 1 |
| M9: Docs & Release | 3 |
| **Total** | **18** |
