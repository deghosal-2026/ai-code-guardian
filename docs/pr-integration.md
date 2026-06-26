# PR Integration — AI Code Guardian

## Overview

When Guardian runs on a pull request, it produces three outputs visible on the PR:

1. **PR Comment** — inline review summary with collapsible violations
2. **Risk Label** — `guardian:*` label reflecting overall risk level
3. **Check Run** — summary in the GitHub Checks tab

---

## 1. PR Comment

Guardian posts a comment on the PR with this format:

```
🤖 AI Code Guardian — Review Summary

ℹ️ Risk Level: LOW (2 violation(s))

<details>
<summary>⚠️ Rule: missing-error-handling — src/api.py:15</summary>

Pattern: except:

Missing specific exception type in except clause. Bare excepts catch all
errors including SystemExit and KeyboardInterrupt, making debugging harder
and potentially masking critical failures.

Recommendation: Replace with specific exception types (ValueError, KeyError, etc.)
[Learn more →](https://docs.example.com/rules/missing-error-handling)
</details>

<details>
<summary>🚨 Rule: hardcoded-secrets — src/config.py:8</summary>

...

---
ℹ️ Advisory mode — This is an advisory review. No code is blocked.

Feedback? React 👍 (accurate) or 👎 (false positive) to this comment.
```

### Format Rules

| Section | Behavior |
|---------|----------|
| Header | Risk level emoji + name + total violation count |
| Violations | Grouped by severity (critical → low), each in a `<details>` block |
| Per-violation | Rule name, file:line, pattern found, explanation, remediation, optional governance link |
| Truncation | If >20 violations, only top 20 are shown with a note about remaining |
| Footer | Mode (advisory/enforcement) and feedback instructions |

### Feedback

React to the comment:
- **👍** = accurate detection (helps improve FPR metrics)
- **👎** = false positive (flagged for review)

---

## 2. Risk Labels

Guardian applies a single `guardian:*` label to the PR based on the highest severity violation found.

| Label | Meaning |
|-------|---------|
| `guardian:low` | No violations or only low-severity findings |
| `guardian:medium` | At least one medium-severity violation |
| `guardian:high` | At least one high-severity violation |
| `guardian:critical` | At least one critical-severity violation |

When a new analysis runs, Guardian removes any existing `guardian:*` labels before applying the updated one.

---

## 3. Check Run

Guardian creates a check run visible in the **Checks** tab of the PR. The check run shows:

```
Risk Level: HIGH
AI Code: 2/10 files (20%)
Violations: 3
FPR: 0%
```

### Conclusion Logic

| Mode | Risk Level | Conclusion |
|------|-----------|------------|
| Advisory | any | `neutral` — never fails |
| Enforcement | critical | `failure` |
| Enforcement | low/medium/high | `success` |

---

## 4. Setup for Adopting Repos

To see Guardian output on PRs, add this workflow (see `.github/workflows/guardian.yml` reference):

```yaml
name: AI Code Guardian
on: pull_request
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: deghosal-2026/ai-code-guardian@v1
        with:
          github_token: ${{ github.token }}
```

Guardian runs in **advisory** mode by default — comments and labels are applied but no check fails. Switch to `enforcement` mode in `guardian-policy.yml` to block PRs with critical violations.
