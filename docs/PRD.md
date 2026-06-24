# PRD: AI Code Guardian

**Status:** ✅ Approved — 2026-06-24
**Author:** deghosal-2026
**Approved by:** deghosal-2026
**Repository:** github.com/deghosal-2026/ai-code-guardian

---

## 1. Executive Summary

AI Code Guardian is a CI bot that detects AI-generated code in pull requests, enforces configurable governance policies, and surfaces quality metrics — so engineering teams can adopt AI coding tools safely without compromising review standards.

It starts in advisory mode (comments + labels, no blocking), builds trust through low false-positive rates, and optionally escalates to enforcement (blocking merges on critical violations) once teams validate signal quality.

---

## 2. Problem Statement

Engineers across the organization use AI coding tools — GitHub Copilot, Cursor, Claude Code — on an ad-hoc basis with zero guardrails:

- AI-generated code enters pull requests without any automated review standard
- Hallucinated API calls and packages sneak through human review
- Missing error handling and hardcoded secrets appear more frequently in AI-generated code
- There is no data on whether AI code is higher or lower quality than human-written code
- The organization has governance *opinions* but no *running system* to enforce them

This gap between having AI governance policies and being able to demonstrate enforcement is the problem Guardian solves.

---

## 3. Users & Personas

### Engineer (Primary)
- **Needs:** Clear, educational PR feedback when AI-generated code is detected. Wants to learn *why* a pattern is risky, not just be flagged.
- **Pain points:** False positives waste time. Noise in PR comments causes alert fatigue.
- **Success:** Guardian comments are useful, accurate, and teach better coding habits.

### Engineering Manager
- **Needs:** Dashboard showing AI code adoption rates, policy violation trends, and false positive metrics per team/repo.
- **Pain points:** No visibility into AI code quality across the team. Can't answer "is AI code helping or hurting us?"
- **Success:** Opens a dashboard and sees clear trends. Uses data to coach the team, not punish.

### VP / Director of Engineering
- **Needs:** Org-wide data on AI code governance. Correlation between AI-attributed code and incidents.
- **Pain points:** Board and leadership ask "what's our AI code policy?" — needs to show evidence.
- **Success:** Has a slide-ready dashboard showing governance in action. Can point to a running system, not a document.

---

## 4. Goals & Non-Goals

### Goals
- Detect AI-generated code in PR diffs using marker-based classification (Phase 1) and style-based classification (Phase 2)
- Apply configurable governance policies from a version-controlled YAML file in the repo
- Enforce 3 built-in rules at launch: hallucinated API detection, missing error handling, hardcoded secrets
- Label PRs with risk levels: low / medium / high / critical
- Post educational PR comments explaining *why* a pattern is risky, with links to governance documentation
- Surface per-PR stats inline on GitHub via the Check Run summary (visible in the Checks tab of every PR — no external tool required)
- Deploy a cross-repo historical dashboard to GitHub Pages via CI workflow (trends across all adopting repos, auto-updated on each run)
- Provide a local dashboard via `guardian serve` (FastAPI + Jinja2) as a secondary fallback for debugging
- Log an immutable audit trail of every decision (detection, review, label, comment)
- Support opt-in to external LLM for style-based detection on a per-repo basis
- Phase 2: Block merges on critical policy violations after team trust is established
- Be installable on any repo in the user's GitHub account via a standard `uses` reference in a workflow file — no per-repo publishing or marketplace listing required
- Analyze non-PR commits (direct pushes to default branch) if the repo opts in, extending coverage beyond pull requests

### Non-Goals
- Replace human code review — Guardian augments, does not substitute
- Replace static analysis / SAST / linting — those tools address different problems
- Real-time IDE detection — this is CI-only at launch
- Code quality scoring beyond AI attribution — no generic "quality score"
- Multi-CI support at launch — GitHub Actions only
- Dashboard-as-a-Service — metrics surface via GitHub Check Runs + GitHub Pages at launch; `guardian serve` is a secondary debug tool

---

## 5. Governance Framework Traceability

Guardian does not invent governance policy — it enforces the existing governance framework defined in the organization's AI governance vault. This section traces how each governance layer maps to Guardian components.

### Governance Layers → Guardian Implementation

| Governance Layer | Vault Reference | Guardian Implementation |
|---|---|---|
| **AI Code Detection** | Governance policy: "All AI-generated code must be labeled in PRs" | Detection engine identifies AI-attributed code via markers. Risk labels applied automatically. |
| **Code Review Standards** | Governance policy: "AI code must pass the same review bar as human code, plus AI-specific checks" | Policy engine applies 3 AI-specific rules (hallucinated APIs, error handling, secrets). PR comments link back to vault docs. |
| **Advisory-First Approach** | Governance policy: "New policies start advisory, escalate to enforcement based on data" | Phase 1 → Phase 2 model. Gate criteria defined in Section 10. |
| **Audit & Traceability** | Governance policy: "All AI governance decisions must be auditable" | Append-only JSONL audit log. Every detection, label, and comment is recorded with timestamp. |
| **Metrics-Driven** | Governance policy: "Policy effectiveness must be measurable" | Dashboard shows FPR, violation trends, AI code %. Data informs policy iteration. |

### Policy Document → Code Enforcement Flow

```
Governance Vault (policies)
        │
        ▼
guardian-policy.yml (repo, version-controlled)
        │
        ▼
Policy Engine (loader + schema validation)
        │
        ▼
Review Engine (rules applied to PR diff)
        │
        ▼
PR Comment + Label (engineer-facing enforcement)
        │
        ▼
Audit Log (immutable record)
        │
        ▼
Dashboard (metrics for managers)
```

Every policy rule in `guardian-policy.yml` links back to a vault page explaining the policy's rationale. This connects the document-based governance framework to the running CI system.

---

## 6. User Experience

### 6.1 PR Comment UX

Guardian posts a single summary comment on each PR after analysis. If multiple violations are found, they are grouped in the comment with collapsible sections.

**Comment format:**

```
🤖 **AI Code Guardian — Review Summary**

**Risk Level:** 🔴 **Critical** (3 violations)

<details>
<summary>⚠️ Rule: Hallucinated API — `fetchDataFromInternalDB()` (line 42)</summary>

This function name matches a known hallucinated API pattern. It references a method
`fetchDataFromInternalDB()` that does not exist in any imported module or standard library.

**Why it matters:** AI models sometimes invent API names that look plausible.
Using these in production causes silent runtime failures.

**Recommendation:** Verify the API exists in your project's dependencies or documentation.
[Learn more about hallucinated API patterns →](link-to-governance-vault)
</details>

<details>
<summary>🔴 Rule: Hardcoded Secret — line 89</summary>

A string matching an API key pattern (`sk-...`) was found inlined in source code.

**Why it matters:** Hardcoded secrets in AI-generated code are a common security risk.
Credentials should use environment variables or a secrets manager.

**Recommendation:** Replace with `os.getenv("API_KEY")` and add the key to your CI secrets.
</details>

---

ℹ️ **Advisory mode** — Guardian currently comments and labels only. No PRs are blocked.
Feedback? React 👍 (accurate) or 👎 (false positive) to this comment.
```

**Key UX decisions:**
- One comment per PR, not per-file — avoids noise
- Collapsible sections — engineer can skim or dive deep
- Educational tone — explains *why*, not just *what*
- Links to governance vault — connects enforcement to policy
- Reaction buttons — lightweight feedback mechanism

### 6.2 GitHub Check Run UX

Guardian creates a **Check Run** on each PR (GitHub Actions integration). The Check Run summary is the primary stats surface — visible in the Checks tab of every PR without any external tool or dashboard.

**Check Run output:**

```
Guardian — AI Code Review
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✔ Analysis complete (2.3s)

  Risk Level:    🔴 Critical (3 violations)
  Files scanned: 12
  AI-attributed: 4 files (33%)
  False positive rate: 5.6%

  Violations:
    🔴 Hallucinated API     → 2  (fetchDataFromInternalDB, processWithBuffer)
    🟡 Missing Error Handl. → 1  (line 89)
    🔴 Hardcoded Secrets    → 1  (line 142)

  Details: https://github.com/.../checks/...

  Advisory mode — PR not blocked. Feedback? 👍 or 👎
```

The Check Run replaces the need for `guardian serve` for day-to-day use. The **GitHub Pages dashboard** provides historical cross-repo trends (deployed via CI after each run).

### 6.3 Label UX

Guardian adds a label to the PR with the risk level:

| Label | Color | Meaning |
|---|---|---|
| `guardian:low` | Green | AI code detected, no policy violations |
| `guardian:medium` | Yellow | AI code detected, minor violations |
| `guardian:high` | Orange | AI code detected, significant violations |
| `guardian:critical` | Red | AI code detected, critical policy violations |

Labels are prefixed `guardian:` to namespace them clearly.

### 6.5 Dashboard UX

Primary: **GitHub Pages dashboard** (auto-deployed via CI workflow). Secondary: `guardian serve` (local FastAPI server for debugging.

The dashboard is a single-page Jinja2 template (shared between both modes), updated on each CI run.

**Layout:**

```
┌──────────────────────────────────────────────────────────┐
│  🔵 AI Code Guardian Dashboard                          │
│  [repo: ai-code-guardian ▼]   [time: last 30 days ▼]    │
├──────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ PRs Analyzed│  │ AI Code %  │  │ Violations  │         │
│  │    142      │  │     34%    │  │     18      │         │
│  └────────────┘  └────────────┘  └────────────┘         │
│  ┌────────────┐  ┌────────────┐                          │
│  │ False Pos. │  │ FPR        │                          │
│  │     1      │  │   5.6%     │                          │
│  └────────────┘  └────────────┘                          │
├──────────────────────────────────────────────────────────┤
│  Violations by Rule (last 30 days)                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Hallucinated API  ████████████░░░░░░░  12        │    │
│  │ Missing Error Hdl ██████░░░░░░░░░░░░   4         │    │
│  │ Hardcoded Secrets ███░░░░░░░░░░░░░░░   2         │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────┤
│  Recent PRs                                              │
│  │ PR #142 │ 🔴 critical │ 3 violations │ 2m ago       │
│  │ PR #141 │ 🟢 low      │ 0 violations │ 15m ago      │
│  │ PR #140 │ 🟡 medium   │ 1 violation  │ 1h ago       │
└──────────────────────────────────────────────────────────┘
```

The CI workflow generates a static HTML dashboard and deploys it to GitHub Pages. `guardian serve` reads the same audit log locally for ad-hoc debugging.

### 6.6 Setup UX

Adopting Guardian takes 2 steps:

1. **Add `guardian-policy.yml`** to the repo root (copy from reference, customize rules)
2. **Add `.github/workflows/guardian.yml`** (copy from template)

On the first PR after setup, Guardian posts a comment that explains it's in advisory mode. This education message only appears on the first analyzed PR for a repo.

### 6.7 Policy Authoring UX

The `guardian-policy.yml` file uses a flat, readable schema:

```yaml
# guardian-policy.yml
version: 1
mode: advisory  # or "enforcement" (Phase 2)

rules:
  - name: hallucinated-api
    severity: critical
    enabled: true
    description: "Detects API calls that don't exist in known libraries"

  - name: missing-error-handling
    severity: high
    enabled: true
    description: "Flags AI-generated code with bare excepts or missing try/finally"

  - name: hardcoded-secrets
    severity: critical
    enabled: true
    description: "Detects API keys, tokens, passwords inlined in code"
```

If the YAML is invalid, Guardian posts a clear error comment:

```
❌ **Guardian configuration error**

guardian-policy.yml line 14: unknown severity 'criticalz'.
Available severities: low, medium, high, critical.
Fix the config and push again.
```

### 6.8 Feedback Loop UX

When an engineer reacts to a Guardian comment:

| Reaction | Meaning | Action |
|---|---|---|
| 👍 (thumbs up) | Accurate finding | Logged as "confirmed" in audit trail |
| 👎 (thumbs down) | False positive | Logged as "disputed" in audit trail. Comment updates: "👎 Flagged as false positive. Thanks — this helps us improve." |

No issues are filed. The feedback feeds into the FPR metric on the dashboard.

### 6.9 Error & Mode UX

| Scenario | CI Status | User Sees |
|---|---|---|
| Guardian runs successfully, no violations | ✅ Green (pass) | Normal PR comment with low risk label |
| Guardian runs successfully, violations found | ⚪ Neutral (pass) | PR comment with violations + risk label |
| Guardian config is invalid | ❌ Red (fail) | Error comment explaining what's wrong |
| Guardian crashes (bug, API timeout) | ⚪ Neutral (skipped) | No comment. PR is not blocked. Error logged. |
| Enforcement mode, critical violation | ❌ Red (fail) | PR merge blocked. Comment explains what must be fixed |

In advisory mode, Guardian never blocks a PR. This is critical for trust-building.

### 6.10 Opt-out UX

- **File-level opt-out:** Add `# guardian:ignore` comment at the top of a file to skip analysis
- **Repository-level opt-out:** Remove the `.github/workflows/guardian.yml` or set `mode: disabled` in policy
- **Per-finding opt-out (Phase 2):** Inline comment `# guardian:ignore reason` on the specific line

---

## 7. User Stories

### Phase 1 (Advisory) — Ordered by Priority

| # | User Story | Acceptance Criteria |
|---|---|---|
| US-01 | As an engineer, I want Guardian to detect AI-generated code in my PR so I know which code was AI-assisted | AI-attributed code identified with <10% false positive rate. Detection covers Copilot, Cursor, Claude Code markers. |
| US-02 | As an engineer, I want Guardian to label my PR with a risk level so I can assess urgency | Label matches severity of highest-violation rule. Labels appear within 2 minutes of PR open/update. |
| US-03 | As an engineer, I want Guardian to comment with educational feedback explaining *why* a pattern is risky | Comment includes pattern description, risk explanation, and remediation recommendation. Links to governance docs. |
| US-04 | As an engineer, I can thumbs up/down a Guardian comment to report feedback | Reaction is logged in audit trail. FPR metric updates on dashboard. |
| US-05 | As a manager, I want to see Guardian stats on GitHub itself without running any command | Check Run summary on each PR shows risk level, AI code %, violations, FPR. GitHub Pages dashboard shows cross-repo trends. |
| US-06 | As an engineer, I want policy files to live in my repo as version-controlled YAML | `guardian-policy.yml` at repo root. Changes go through PR review. Invalid config produces actionable error. |
| US-07 | As a lead, I want an immutable audit trail of every Guardian decision | Audit log (JSONL) records: PR ID, timestamp, detection results, violations, label, comment. |
| US-08 | As an engineer, I can opt a file out of Guardian analysis with `# guardian:ignore` | Comment at top of file skips analysis. Logged in audit trail. |
| US-09 | As an account owner, I can enable Guardian on any of my repos by adding a 3-line workflow file | Any public or private repo can reference `deghosal-2026/ai-code-guardian` in `.github/workflows/guardian.yml`. No marketplace listing, no org-level config needed. |
| US-10 | As a lead, I want Guardian to analyze direct pushes to main (not just PRs) if I opt in | Workflow supports `push` trigger. Analysis output appears in commit status check. Audit log distinguishes PR vs push events. |

### Phase 2 (Enforcement) — Future

| # | User Story | Acceptance Criteria |
|---|---|---|
| US-11 | As a lead, I want Guardian to block merges on critical violations after trust is established | Enforcement mode blocks PR with ❌ status. Only critical severities block. Team must opt in explicitly. |
| US-12 | As an engineer, I want style-based detection optionally enabled for my repo | Repo sets `detection: style` in policy. Requires external LLM opt-in. Falls back to marker-only if LLM unavailable. |

---

## 8. Functional Requirements

### FR-01: Detection Engine
- Scan PR diff for attribution markers from Copilot, Cursor, and Claude Code
- Return confidence score per detected file (high/medium/low based on marker strength)
- Style-based detection via external LLM (Phase 2, per-repo opt-in)

### FR-02: Policy Engine
- Load and validate `guardian-policy.yml` from repo root
- Validate against a defined schema (version, mode, rules)
- Reject unknown rule names, severities, or invalid YAML with actionable error messages
- Enforce 3 built-in rules: hallucinated-api, missing-error-handling, hardcoded-secrets
- Support enabling/disabling individual rules

### FR-03: PR Integration
- Fetch PR diff via GitHub API
- Post a single summary comment per PR
- Assign/update risk label on PR
- Handle PR updates (new commits trigger re-analysis)
- Handle draft PRs (analyze but note "draft" in audit log)

### FR-04: Comment Generator
- Group violations by severity, highest first
- Collapsible `<details>` sections per violation
- Include for each violation: file + line, pattern description, risk context, remediation, policy link
- Append footer with mode (advisory/enforcement) and feedback instructions
- If too many violations (>20), summarize: "20+ violations found — showing top 20"

### FR-05: GitHub Check Run Output
- Generate a structured Check Run summary on each PR analysis
- Include: risk level, files scanned, AI-code %, violation counts by rule, FPR, links to details
- Support both `success` (no violations), `neutral` (violations in advisory mode), and `failure` (violations in enforcement mode) conclusions
- Check Run output is the primary stats surface — no external tool needed

### FR-06: GitHub Pages Dashboard
- CI workflow generates a static HTML dashboard from the audit log
- Auto-deploys to GitHub Pages after each analysis run
- Same metrics layout as the Check Run but with cross-repo historical trends and time-range filtering
- Falls back to `guardian serve` (local FastAPI) for debugging when Pages deployment is not configured

### FR-07: Audit Log
- Append-only JSONL file per repo
- Each entry: PR ID, timestamp, action (analysis/comment/label/feedback), result data
- Never modified after append
- Location: configurable (`~/.guardian/audit/` by default)

### FR-08: CLI
- `guardian detect` — run analysis on a PR (used by GitHub Action)
- `guardian serve` — start the local dashboard (debug fallback)
- `guardian check-config` — validate a policy file without running analysis
- `guardian generate-pages` — build static dashboard HTML for GitHub Pages deployment
- `guardian version` — print version

### FR-06: Audit Log
- Append-only JSONL file per repo
- Each entry: PR ID, timestamp, action (analysis/comment/label/feedback), result data
- Never modified after append
- Location: configurable (`~/.guardian/audit/` by default)

### FR-07: CLI
- `guardian detect` — run analysis on a PR (used by GitHub Action)
- `guardian serve` — start the dashboard
- `guardian check-config` — validate a policy file without running analysis
- `guardian version` — print version

---

## 9. Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Performance** | CI check completes in <2 minutes for a typical PR (<500 lines changed) |
| **Privacy** | No code sent to external services unless repo explicitly opts in |
| **Security** | No secrets stored. No outbound network calls in default (marker-only) mode. |
| **Reliability** | If LLM/API call fails, fall back to marker-only mode. If marker-only fails, skip silently. Never block a PR incorrectly. |
| **Audit** | Every decision is logged with timestamp. Logs are append-only and immutable. |
| **Usability** | Setup in 2 steps (YAML + workflow). First comment educates the user. Error messages are actionable, not cryptic. |
| **False Positive Rate** | <10% for marker-based detection in Phase 1 |
| **Scalability** | Must handle repos with 50+ PRs/day |

---

## 10. Phases & Milestones

### Phase 1: Advisory (MVP)

| Milestone | Deliverable |
|---|---|
| M1 | Detection engine — marker-based for Copilot, Cursor, Claude Code |
| M2 | Policy engine — load, validate, enforce 3 rules |
| M3 | PR integration — fetch diff, post comment, assign label |
| M4 | Audit trail — append-only JSONL logging |
| M5 | Check Run output — summary in GitHub Checks tab per PR |
| M6 | Dashboard — GitHub Pages deployment + `guardian serve` fallback |
| M7 | CLI — `detect`, `serve`, `generate-pages`, `check-config` commands |
| M8 | GitHub Action — `action.yml` + `Dockerfile` |
| M9 | First team repo live — Guardian runs on every PR |

### Phase Gate Criteria

Transitions between phases require meeting defined criteria. Gating is data-driven, not calendar-driven.

| Gate | From | To | Criteria | Measurement |
|---|---|---|---|---|
| G1 | Phase 1 (Advisory) | Phase 2 (Enforcement) | FPR <10% sustained for 4 weeks | Dashboard FPR metric |
| | | | Team opt-in via PR to `guardian-policy.yml` setting `mode: enforcement` | File change in repo |
| | | | No open critical bugs in Guardian itself | Issue tracker |
| | | | At least 20 PRs analyzed during advisory period | Audit log |
| G2 | Phase 2 (Enforcement) | Phase 3 (Scale) | Enforcement active on 1 repo for 8+ weeks without rollback | Audit log |
| | | | At least 1 other team has requested adoption | Documented request |
| | | | Style-based detection FPR <5% (if enabled) | Dashboard FPR metric |

### Phase 2: Enforcement

| Milestone | Deliverable |
|---|---|
| M10 | Block merges on critical violations in enforcement mode |
| M11 | Style-based detection via external LLM (opt-in per repo) |
| M12 | Per-finding opt-out (`# guardian:ignore` on specific line) |

### Phase 3: Scale

| Milestone | Deliverable |
|---|---|
| M13 | Multi-repo dashboard support |
| M14 | DORA metric correlation (cycle time, deployment frequency) |
| M15 | Incident correlation — track incidents against AI-attributed code |

---

## 11. Competitive Context

| Tool | Focus | Guardian Difference |
|---|---|---|
| **SonarCloud** | Code quality / SAST | Free for public repos only. Private repos require paid plan. Not AI-specific. No AI attribution detection. No governance policy framework. |
| **CodeQL** | Semantic code analysis | Free for public repos. Private repos need GitHub Advanced Security (paid). Security vuln scanning only — no AI attribution or governance. |
| **Datadog SAST** | Static analysis in CI | Paid. General-purpose SAST. Doesn't distinguish AI vs human code. |
| **GitHub Copilot Chat** | Developer assistant | Not a review tool. No policy enforcement. No metrics. |
| **LLM-as-judge prompts** | Ad-hoc code review | No CI integration. No audit trail. No dashboard. No configurable policies. |
| **Guardian** | **AI-specific governance** | Detects AI code, enforces AI-specific policies, tracks AI code quality trends. Governance-first, educational, advisory-to-enforcement model. |

---

## 12. Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| AI tools to detect | Copilot, Cursor, Claude Code | Most common tools in the org |
| Detection method | Marker-based first | Simpler, lower FPR, builds trust before style-based |
| FPR target | <10% | High enough signal to be useful, low enough to avoid noise |
| Language | Python | Natural for CI tooling, easy MCP server integration later |
| Dashboard framework | FastAPI + Jinja2 | Lightweight, local CLI-only at launch |
| Metrics format | Prometheus-export format on /metrics | Pluggable into Grafana later |
| CI platform | GitHub Actions only | Org uses GitHub |
| Privacy model | Hybrid — local by default, external with opt-in | Respects security policy, enables style detection optionally |
| Detection model (Phase 1) | None — regex/pattern matching | Attribution markers from Copilot, Cursor, Claude Code. Zero cost, zero latency, fully private. |
| Detection model (Phase 2, style-based) | Configurable. Default: local via Ollama (CodeLlama/Llama 3). Cloud opt-in: GPT-4o-mini, Claude Haiku, or any OpenAI-compatible endpoint | Model choice is set in `guardian-policy.yml` (`detection.model`). Allows the org to choose any provider. CodeLlama for private, GPT-4o-mini when cloud is permitted. SPEC will finalize defaults after benchmarking. |
| Feedback mechanism | PR comment reactions (👍/👎) | Lowest friction approach for engineers |
| Policy format | YAML in repo root | Version-controlled, reviewable via PR |
| Audit format | Append-only JSONL | Simple, immutable, machine-readable |
| Dashboard hosting | GitHub Pages (primary) + `guardian serve` (debug fallback) | Stats visible on GitHub itself — Check Run per PR, Pages for cross-repo trends. No external infra. |
| Initial adoption | Single team (yours) | Prove value before scaling |
| Timeline | No fixed deadline | Build it right, not fast |
| Advisory-first approach | Yes | Build trust before enforcement |

---

## 13. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Marker detection misses unattributed AI code | Medium | High — engineers strip markers | Phase 2 adds style-based detection. Communicate detection limits clearly. |
| False positive rate exceeds 10% | Medium | Medium — engineers lose trust | Dashboard tracks FPR publicly. Iterate on marker patterns. Allow feedback via reactions. |
| Team doesn't adopt | Low | High — project has no impact | Start with own team. Show data in demos. Make it useful, not punitive. |
| External LLM blocked by security policy | Medium | Medium — no style detection | Marker-only mode is still valuable. Style detection is additive, not required. |
| AI tools change their marker formats | Medium | Low — missed detections | Detection patterns are configurable. Update as tooling evolves. |
| Performance >2 minutes for large PRs | Low | Medium — engineers disable the check | Implement file-count and line-count limits. Skip binary/lock files. Optimize diff processing. |
| Dashboard shows concerning trends to leadership | Low | Medium — pressure to "fix AI code" | Guardian is designed for data-driven conversations, not punishment. Frame metrics as coaching signals. |

---

## 14. Success Metrics & KPIs

| Metric | Phase 1 Target | Phase 2 Target |
|---|---|---|
| False positive rate (FPR) | <10% | <5% |
| Detection recall (marker-based) | >80% of AI-attributed code with markers | >90% (with style-based) |
| PR coverage | 100% of PRs in pilot repo | 100% across all adopted repos |
| Setup time for new repo | <15 minutes | <5 minutes (with templates) |
| Time from PR open to comment | <2 minutes | <30 seconds |
| Engineer satisfaction (via survey) | >3.5/5 | >4.0/5 |
| PRs analyzed per week (pilot) | >20 | >100 across org |
| Dashboard uptime (`guardian serve`) | On-demand, no SLO | On-demand, no SLO |

---

## 15. Dependencies & Assumptions

### Dependencies
- GitHub API access (PR diff fetching, comment posting, label management)
- `PyYAML` (policy file parsing)
- `httpx` or `requests` (GitHub API client)
- `fastapi` + `uvicorn` + `jinja2` (dashboard server)
- `prometheus-client` (metrics export)
- `pydantic` (configuration models)
- Local filesystem for audit log storage

### Assumptions
- AI coding tools leave identifiable attribution markers in generated code
- Team uses GitHub (not GitLab, Bitbucket, etc.)
- The org prefers advisory-first over enforcement-first governance
- Policy rules can be usefully expressed in a flat YAML file
- Engineers will engage with Guardian comments (read them, react, act on them)
- The pilot repo has active PR volume (>5 PRs/week)

---

## 16. Cost Model

### Marker-Based Detection (always-on)
| Component | Cost | Notes |
|---|---|---|
| Compute (GH Actions runner) | $0 — included in GitHub Actions free/minutes pool | Runs as a CI step on standard runners. Negligible CPU/memory. |
| Audit log storage | ~1 MB per 1,000 PRs (JSONL) | Stored on local filesystem or Action artifact. Essentially free. |

### Style-Based Detection (Phase 2, opt-in per repo)

| Component | Cost Estimate | Notes |
|---|---|---|
| External LLM API (e.g. GPT-4o-mini) | ~$0.01–$0.05 per PR | 500-line diff → ~5K tokens input + ~200 tokens output. At 50 PRs/week: ~$2.50–$12.50/week per repo. |
| External LLM API (e.g. Claude Haiku) | ~$0.005–$0.02 per PR | Cheaper alternative. ~$1.25–$5.00/week per repo at same volume. |
| LLM latency | ~2–5s per PR | Only for style analysis. Marker detection runs first and is fast. |

### Dashboard (`guardian serve`)

| Component | Cost | Notes |
|---|---|---|
| Compute (local machine) | $0 — runs on-demand | No server deployment. User starts it locally when needed. |
| No infrastructure costs | $0 | No hosting, no database server, no monitoring infra for the dashboard itself. |

### Future: Persistent Server (if dashboard evolves beyond CLI-only)

| Component | Cost Estimate | Notes |
|---|---|---|
| Cloud VM (e.g. 1 vCPU, 2GB RAM) | ~$10–$20/month | For always-on dashboard + webhook receiver |
| Storage (audit logs) | ~$1–$5/month (50GB) | Scales with PR volume |
| Total | ~$15–$30/month | Negligible for an org-wide tool |

### Summary

Guardian's ongoing cost for Phase 1 is effectively **$0** (GitHub Actions compute + local dashboard). Phase 2 adds LLM API costs of ~$5–$15/week per repo if style detection is enabled. The org can choose to never enable style detection and stay at $0.

---

## 17. Glossary

| Term | Definition |
|---|---|
| **AI-attributed code** | Code identified as likely generated or assisted by an AI coding tool |
| **Marker detection** | Detecting AI code by scanning for comment strings AI tools insert (e.g. `// Generated by Copilot`) |
| **Style detection** | Detecting AI code by analyzing code patterns, structure, or entropy using an LLM classifier |
| **False positive (FP)** | Human-written code incorrectly flagged as AI-generated |
| **False negative (FN)** | AI-generated code not detected by Guardian |
| **False positive rate (FPR)** | FP / (FP + TN) — percentage of human code incorrectly flagged |
| **Risk level** | Severity tier assigned to a PR based on the highest-severity rule violated |
| **Advisory mode** | Guardian comments and labels but never blocks. Trust-building phase. |
| **Enforcement mode** | Guardian can block PR merges on critical violations. Requires team opt-in. |
| **Policy file** | `guardian-policy.yml` — the YAML config that defines rules and mode for a repo |
| **Audit trail** | Append-only JSONL log of every Guardian decision |
| **Guardian comment** | The single summary PR comment Guardian posts with analysis results |
| **Rule** | A single policy check (e.g., hallucinated-api, hardcoded-secrets) |

---

## 18. Open Questions (resolve before SPEC)

- [ ] Exact audit log storage location? `~/.guardian/audit/` vs `./.guardian/audit/`? Both configurable?
- [ ] Data retention policy for audit logs? Keep forever? Prune after 90 days? Configurable TTL?
- [ ] Dashboard auth? None — `guardian serve` is localhost-only. Or add optional simple token auth?
- [ ] Rule severity configurable per rule? Hallucinated-api is `critical` by default — can a team downgrade it to `high`?
- [ ] "Opt-out" at file level — `# guardian:ignore` at top of file. Should it support a reason string? `# guardian:ignore: generated file`
- [ ] Should Guardian analyze commits on the default branch (not just PRs)? E.g., detect AI code pushed directly to main?
- [ ] What happens when Guardian is not installed for a repo but referenced in workflow? Documented error vs silent skip?
- [ ] Should the PRD define a specific output schema for detection results (detection confidence per file per rule)?

---

*End of PRD v1*
