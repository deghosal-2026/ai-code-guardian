# AGENTS.md — AI Code Guardian

## Project Goal
Implement M2 (Policy Engine) milestone with tests and closing its GitHub issues.

## Constraints & Preferences
- SPEC.md docs/SPEC.md and PRD.md docs/PRD.md are approved reference documents
- 29 open GitHub issues across M1-M9; only developer-chosen issues should be closed when delivered
- No code changes without user direction
- Advisory-first governance model (comment + label, no blocking) per spec

## Done
- Implemented `policy/loader.py` with YAML parsing, pydantic schema validation, missing-file default fallback, and duplicate-name rejection
- Added `@field_validator("rules")` for duplicate rule name detection to `policy/models.py`
- Implemented `reviewer/rules.py` with 3 built-in rules: hallucinated-api (known-API registry + lowercase-variable heuristic), missing-error-handling (bare except detection), hardcoded-secrets (credential regex patterns)
- Implemented `reviewer/engine.py` with `evaluate()` and `compute_risk_level()`
- Updated `config.py` to delegate to `load_policy_file()` from `policy/loader.py`
- Fixed multi-file diff processing bug in `detector/marker.py` (was only returning last file; added `_process_file_lines()` flush on each `+++ b/` header)
- Wrote `tests/test_detector.py` — 23 tests covering all 7 marker patterns individually, case-insensitivity, human diff FPR (zero), empty diff, multi-file paths, confidence levels, result structure
- Wrote `tests/test_policy.py` — 9 tests covering valid YAML load, field correctness, missing file fallback, YAML syntax error, bad severity, duplicate names, non-dict YAML, deep-copy isolation
- Wrote `tests/test_reviewer.py` — 22 tests covering all 3 rules (detection, false-positive avoidance, low-confidence skip, local-variable skip, nested-call skip, integration with real diffs), engine evaluate (all rules, disabled rules, empty detections, unknown rules), compute_risk_level (empty, highest severity)
- Closed GitHub issues #5 (M1-DEV), #6 (M1-TEST), #7 (M2-DEV), #8 (M2-DEV), #9 (M2-TEST)

## Previous Sessions
- Scaffolded project directory structure, stubs, configs (milestones M1-M9)
- Wrote and approved PRD v1
- Wrote and approved SPEC v1 (14 sections, 29-ticket breakdown across 9 milestones)
- M1: Implemented marker-based detection engine (`detector/marker.py`)
- M1: Wrote tests for detection engine (`tests/test_detector.py`)
- M2: Implemented policy loader and schema (`policy/loader.py`, `policy/models.py`)
- M2: Implemented 3 built-in review rules (`reviewer/rules.py`)
- M2: Implemented review engine (`reviewer/engine.py`)
- M2: Updated config loader (`config.py`)
- M2: Fixed multi-file bug in marker.py
- M2: Wrote tests for policy engine (`tests/test_policy.py`, `tests/test_reviewer.py`)
- Closed issues #5, #6, #7, #8, #9

## Test Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_reviewer.py -v
```

## Notes
- Hallucinated API rule uses a built-in known-API registry (stdlib modules + common third-party libs)
- Dotted calls starting with lowercase first segment treated as "likely local variable" to reduce FPs
- Regex-based extraction cannot match nested calls inside argument lists (Phase 1 limitation)
- Detection scans only `+` lines in diffs
- Confidence: single match → `"medium"`, ≥2 matches same tool → `"high"`
- Risk level computed as max severity across all violations
- 24 open issues remain (M3-M9)
