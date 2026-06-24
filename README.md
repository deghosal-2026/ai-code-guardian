# AI Code Guardian

**AI Code Governance CI Bot** — detects AI-generated code in pull requests, enforces governance policies, and tracks AI code quality metrics.

## What It Does

- **Detects** AI-attributed code in PR diffs using marker-based and/or style-based classification
- **Reviews** code against a configurable governance policy file (hallucinated APIs, missing error handling, hardcoded secrets, etc.)
- **Labels** PRs with risk levels (low / medium / high / critical)
- **Comments** with educational feedback — explains *why* a pattern is risky, not just flags it
- **Reports** metrics — AI code percentage, acceptance rate, violation trends — on a dashboard
- **Blocks** (optional) merges that violate critical policies, after trust is established

## Why

Engineers use AI coding tools ad-hoc — Copilot, Cursor, Claude Code — with zero guardrails. AI-generated code enters production without review standards, hallucinated APIs sneak through, and no one tracks whether AI code is better or worse than human code.

Guardian bridges the gap between **having AI governance opinions** and **being the person the org trusts to implement it**.

## Getting Started

> **Status:** Active development. See [Guardian project note](https://github.com/deghosal-2026/ai-code-guardian) for the roadmap.

1. Configure a `guardian-policy.yml` file in your repo
2. Add the Guardian GitHub Action to your workflow
3. Review PR comments and iterate on policy rules

## Governance Model

Guardian follows an **advisory-first** approach:

| Phase | Behavior | Duration |
|---|---|---|
| Trust-building | Comment + label only, no blocking | 2–3 sprints |
| Enforcement | Block merges on critical policy violations | After team opt-in |

## License

MIT
