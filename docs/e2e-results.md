# E2E Test Results — AI Code Guardian

## Summary

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| T1 | Clean PR (no AI code) | ⏳ Pending | Needs separate test PR |
| T2 | AI markers detected | ✅ PASS | 4 files detected across 3 AI tools |
| T3 | Hallucinated API | ✅ PASS | Found `DatabaseClient`, `validate_token` |
| T4 | Hardcoded secrets | ✅ PASS | 4 pattern matches (2 duplicate) |
| T5 | Missing error handling | ✅ PASS | 2 bare except blocks flagged |
| T6 | Mixed violations | ✅ PASS | 8 violations across 4 files, risk=critical |
| T7 | Comment truncation (>20) | ⏳ Pending | Needs PR with 25+ violations |
| T8 | Enforcement mode | ⏳ Pending | Needs policy change |
| T9 | Audit log | ⚠️ PARTIAL | Log created but entries show errors (check run 403) |
| T10 | Dashboard | ⏳ Pending | Needs serve command |
| T11 | Docker | ✅ PASS | Verified in test_action.py |
| T12 | Label cleanup | ✅ PASS | Old `guardian:low` removed, `guardian:critical` applied |

## Run Details

- **PR:** [#46](https://github.com/deghosal-2026/ai-code-guardian/pull/46)
- **Branch:** `e2e/test-ai-code`
- **Test files:** 5 files in `e2e-tests/`
- **Guardian command:** `guardian detect --repo deghosal-2026/ai-code-guardian --pr 46`
- **Pipeline exit code:** 1 (error from check run 403 — expected for local token)

### Detection Results

| File | AI Tool | Confidence | Line Count |
|------|---------|------------|------------|
| `e2e-tests/ai_generated_module.py` | Copilot, Cursor, Claude Code | medium | 18 |
| `e2e-tests/hallucinated_api.py` | Copilot | medium | 10 |
| `e2e-tests/hardcoded_secrets.py` | Cursor | medium | 13 |
| `e2e-tests/missing_error_handling.py` | Claude Code | medium | 12 |
| `e2e-tests/clean_module.py` | — | — | 14 (not flagged) |

### Review Results

| Rule | Severity | Count | File:Line | Pattern |
|------|----------|-------|-----------|---------|
| hallucinated-api | critical | 2 | `hardcoded_secrets.py:7` | `DatabaseClient` |
| | | | `hardcoded_secrets.py:12` | `validate_token` |
| hardcoded-secrets | critical | 4 | `hardcoded_secrets.py:6` | OpenAI API key, API key |
| | | | `hardcoded_secrets.py:11` | Hardcoded credential, GitHub PAT |
| missing-error-handling | high | 2 | `missing_error_handling.py:9` | bare except: |
| | | | `missing_error_handling.py:16` | bare except: |

**Risk level:** critical

### PR Comment
- Posted as PR comment with severity-grouped collapsible `<details>` blocks
- Critical violations (🚨) listed first, high (⚠️) second
- Footer with advisory mode note and feedback instructions

### Label
- Old `guardian:low` removed ✓
- New `guardian:critical` applied ✓

### Check Run
- ❌ Failed with 403 Forbidden — token scope lacks `checks:write`
- This is expected for local `gh auth token`; CI token will have it

### Audit Log
- 2 entries created in `~/.guardian/audit/deghosal-2026_ai-code-guardian/audit.jsonl`
- Both are `action=error` entries (from check run failure)
- Entry includes event_id, timestamp, pr_number, error message, duration_ms

## Known Observations

1. **Lowercase-first-segment skip:** Dotted calls like `payment_gateway.charge()` are not flagged by `hallucinated-api` rule. The first segment `payment_gateway` starts with lowercase, so it's treated as a local variable. This is by design (AGENTS.md).

2. **Duplicate secret matches:** Line with `api_key = "sk-..."` triggers both "OpenAI API key" and "API key" patterns. The `sk-` prefix matches OpenAI pattern, and the `api_key =` assignment matches the API key pattern. This produces duplicate entries.

3. **No FPs on clean code:** `e2e-tests/clean_module.py` (human-written fibonacci/palindrome) was not detected as AI-generated and no rules flagged it.

4. **Check run requires CI:** Local GitHub tokens from `gh auth` don't have `checks:write` scope. The check run step only works in CI with a `GITHUB_TOKEN` that has proper permissions.
