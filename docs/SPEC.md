# SPEC: AI Code Guardian — Technical Specification

**Status:** ✅ Approved — 2026-06-24
**Author:** deghosal-2026
**Approved by:** deghosal-2026
**Repository:** github.com/deghosal-2026/ai-code-guardian
**PRD Reference:** docs/PRD.md (v1, approved 2026-06-24)
**Structure:** Sections 1–10 are technical reference. Section 11 contains the full ticket breakdown — each ticket maps to a GitHub issue (title, description, labels, acceptance criteria) organized by milestone for direct issue creation after approval.

---

## 1. Overview

This document translates the approved PRD into a detailed technical blueprint covering architecture, component design, data flow, API contracts, data models, implementation order, and testing strategy.

### Scope

Guardian is a Python CLI tool packaged as a GitHub Action. It runs on every PR (and optionally on direct pushes), detects AI-generated code via marker scanning, applies configurable policy rules, posts PR comments and labels, logs an immutable audit trail, and surfaces metrics via GitHub Check Run summaries and GitHub Pages.

---

## 2. Directory Structure

```
ai-code-guardian/
├── action.yml                        # GitHub Action metadata
├── Dockerfile                        # Action runner image
├── pyproject.toml                    # Project config, dependencies, build
├── guardian-policy.yml               # Reference/default policy file
├── .github/
│   └── workflows/
│       └── guardian.yml              # Example workflow for adopting repos
├── docs/
│   ├── PRD.md                        # Product Requirements Document
│   └── SPEC.md                       # This document
├── src/guardian/                     # Python package root
│   ├── __init__.py
│   ├── __main__.py                   # `python -m guardian` entry
│   ├── cli.py                        # CLI argument parsing (argparse)
│   ├── config.py                     # Policy + config loading (pydantic)
│   ├── action.py                     # GitHub Action entry point
│   ├── detector/
│   │   ├── __init__.py
│   │   ├── models.py                 # DetectionResult, MarkerMatch
│   │   ├── marker.py                 # Marker-based detection engine
│   │   └── style.py                  # Style-based detection (Phase 2, stub)
│   ├── reviewer/
│   │   ├── __init__.py
│   │   ├── engine.py                 # Policy evaluation engine
│   │   ├── rules.py                  # Built-in rule implementations
│   │   └── models.py                 # Violation, ReviewResult
│   ├── policy/
│   │   ├── __init__.py
│   │   ├── loader.py                 # YAML loader + schema validation
│   │   └── models.py                 # PolicyConfig, RuleConfig
│   ├── pr/
│   │   ├── __init__.py
│   │   ├── client.py                 # GitHub API client (httpx)
│   │   ├── commentator.py            # PR comment markdown template
│   │   ├── labeler.py                # Risk level label assignment
│   │   └── check_run.py              # Check Run output generation
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── logger.py                 # Append-only JSONL audit log
│   │   └── models.py                 # AuditEntry
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── collector.py              # In-memory metrics aggregation
│   │   └── prometheus.py             # Prometheus /metrics export
│   └── server/
│       ├── __init__.py
│       ├── app.py                    # FastAPI app
│       └── templates/
│           └── dashboard.html        # Jinja2 dashboard template
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Shared fixtures
│   ├── test_detector.py
│   ├── test_reviewer.py
│   ├── test_policy.py
│   ├── test_pr_client.py
│   ├── test_commentator.py
│   ├── test_labeler.py
│   ├── test_check_run.py
│   ├── test_audit.py
│   ├── test_cli.py
│   └── fixtures/
│       ├── pr_diff_ai.txt            # PR diff with AI markers
│       ├── pr_diff_human.txt         # PR diff without markers
│       ├── guardian-policy-valid.yml
│       └── guardian-policy-invalid.yml
└── scripts/
    └── generate-pages.sh            # CI script to build + deploy Pages dashboard
```

---

## 3. Architecture

### 3.1 High-Level Data Flow

```
GitHub Trigger (PR / push)
        │
        ▼
┌─────────────────┐
│  action.py       │  Receives GITHUB_TOKEN, PR number, repo
│  (entry point)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  cli.py          │  Parses args, orchestrates flow
│  guardian detect │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│config  │ │pr.client │  Fetch PR diff via GitHub API
│.py     │ │          │
│load    │ └────┬─────┘
│policy  │      │
└───┬────┘      │
    │           ▼
    │    ┌──────────┐
    │    │detector/ │  Scan diff for AI markers
    │    │marker.py │  → List[DetectionResult]
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │reviewer/ │  Apply policy rules to detections
    │    │engine.py │  → List[Violation]
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │ pr/      │  Generate comment + label + check run
    │    │ *        │  → Post to GitHub
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │ audit/   │  Append JSONL entry
    │    │ logger   │
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │ metrics/ │  Update counters
    │    │collector │
    │    └──────────┘
    │
    │  (Separate CI step)
    ▼
┌──────────────┐
│ generate-    │  Build static HTML dashboard
│ pages.sh     │  Deploy to GitHub Pages
└──────────────┘
```

### 3.2 Component Dependency Graph

```
action.py → cli.py
cli.py → config.py
cli.py → pr/client.py → (GitHub API)
cli.py → detector/marker.py
cli.py → reviewer/engine.py → reviewer/rules.py
cli.py → pr/commentator.py
cli.py → pr/labeler.py
cli.py → pr/check_run.py
cli.py → audit/logger.py
cli.py → metrics/collector.py

server/app.py → metrics/prometheus.py
server/app.py → audit/logger.py (read-only)
```

### 3.3 Execution Modes

| Mode | Trigger | Entry | Output |
|---|---|---|---|
| **PR analysis** | `pull_request` event | `action.py` → `cli.detect(pr_number)` | Comment + label + check run + audit |
| **Direct push** | `push` event (opt-in) | `action.py` → `cli.detect(commit_sha)` | Commit status + audit |
| **Local serve** | CLI command | `cli.serve()` | FastAPI dashboard (localhost) |
| **Config check** | CLI command | `cli.check_config(path)` | Validation pass/fail + errors |
| **Pages build** | CLI command | `cli.generate_pages()` | Static HTML directory |

---

## 4. Data Models

### 4.1 Detection Models (`detector/models.py`)

```python
@dataclass
class MarkerMatch:
    tool: str                      # "copilot" | "cursor" | "claude-code"
    pattern: str                   # The regex pattern that matched
    line: int
    confidence: Literal["high", "medium"]

@dataclass
class DetectionResult:
    file_path: str
    total_lines: int
    matches: list[MarkerMatch]
    confidence: Literal["high", "medium", "low"]
    # high = multiple markers from same tool
    # medium = single marker
    # low = detected via style classifier (Phase 2)
```

### 4.2 Policy Models (`policy/models.py`)

```python
class RuleConfig(BaseModel):
    name: str                      # "hallucinated-api"
    severity: Literal["low", "medium", "high", "critical"]
    enabled: bool = True
    description: str = ""

class PolicyConfig(BaseModel):
    version: int                   # Schema version (1)
    mode: Literal["advisory", "enforcement"] = "advisory"
    detection: Literal["marker", "style", "both"] = "marker"
    model: str | None = None       # "ollama/codellama", "openai/gpt-4o-mini", etc.
    rules: list[RuleConfig]

    @field_validator("rules")
    @classmethod
    def check_duplicate_names(cls, v):
        names = [r.name for r in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate rule names")
        return v
```

### 4.3 Review Models (`reviewer/models.py`)

```python
@dataclass
class Violation:
    rule_name: str
    severity: Literal["low", "medium", "high", "critical"]
    file_path: str
    line: int | None
    pattern_found: str              # The problematic code/text
    explanation: str                # Why it's risky
    remediation: str                # How to fix it
    governance_url: str | None      # Link to vault doc for this rule

@dataclass
class ReviewResult:
    violations: list[Violation]
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str                    # Brief one-liner for check run
```

### 4.4 Audit Models (`audit/models.py`)

```python
@dataclass
class AuditEntry:
    version: int = 1
    timestamp: str                  # ISO 8601
    event_id: str                   # UUID
    repo: str                       # "owner/name"
    pr_number: int | None
    commit_sha: str | None
    action: Literal[
        "analysis", "comment_posted", "label_applied",
        "check_run_created", "feedback_received", "error"
    ]
    detection_results: list[DetectionResult] | None
    violations: list[Violation] | None
    risk_level: str | None
    feedback: Literal["confirmed", "disputed"] | None
    duration_ms: int
    error: str | None
```

### 4.5 Config Model (`config.py` — top-level runtime config)

```python
class GuardianConfig(BaseModel):
    github_token: str
    repo: str                       # "owner/name"
    pr_number: int | None = None
    commit_sha: str | None = None
    policy_path: str = "guardian-policy.yml"
    audit_dir: str = "~/.guardian/audit"
    verbose: bool = False
```

---

## 5. Component Specifications

### 5.1 CLI (`src/guardian/cli.py` + `__main__.py`)

**Interface:**

```
guardian detect [--token TOKEN] --repo OWNER/REPO --pr NUMBER [--policy PATH] [--audit-dir PATH] [--verbose]
guardian detect [--token TOKEN] --repo OWNER/REPO --commit SHA [--policy PATH] [--audit-dir PATH] [--verbose]
guardian serve [--port PORT] [--audit-dir PATH]
guardian check-config [--policy PATH]
guardian generate-pages [--audit-dir PATH] [--output DIR]
guardian version
```

**Implementation:**
- argparse-based (stdlib, no external dep for CLI parsing)
- Subcommands via `add_subparsers()`
- `detect` is the primary command — orchestrates the full flow
- Exit codes: 0 = success (or violations in advisory), 1 = error, 2 = enforcement violation

### 5.2 GitHub Action Entry (`src/guardian/action.py`)

Reads environment variables set by GitHub Actions and calls `cli.detect()`:

```python
def run_action():
    token = os.environ["INPUT_GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    event_name = os.environ["GITHUB_EVENT_NAME"]

    if event_name == "pull_request":
        pr_number = json.loads(os.environ["GITHUB_EVENT_PATH"])["number"]
        cli.detect(token=token, repo=repo, pr_number=pr_number)
    elif event_name == "push":
        commit_sha = os.environ["GITHUB_SHA"]
        cli.detect(token=token, repo=repo, commit_sha=commit_sha)
```

### 5.3 Config Loader (`src/guardian/config.py`)

- Loads `guardian-policy.yml` from repo root (fetched via GitHub API)
- Validates against `PolicyConfig` pydantic model
- Falls back to default config if file not found (advisory mode, 3 rules enabled)
- Returns `tuple[PolicyConfig, GuardianConfig]`

### 5.4 Detector: Marker-Based (`src/guardian/detector/marker.py`)

**Patterns:**

```python
MARKER_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "copilot": [
        (r"#?\s*Generated by Copilot", "high"),
        (r"#?\s*This code was generated by GitHub Copilot", "high"),
        (r"//\s*Auto-generated by Copilot", "high"),
    ],
    "cursor": [
        (r"#?\s*Generated by Cursor", "high"),
        (r"//\s*Cursor-generated code", "high"),
    ],
    "claude-code": [
        (r"#?\s*Generated by Claude Code", "high"),
        (r"//\s*Claude Code generated", "high"),
    ],
}
```

**Algorithm:**
```python
def analyze_diff(diff: str) -> list[DetectionResult]:
    # 1. Split diff into per-file hunks
    # 2. For each file, scan added lines for marker patterns
    # 3. If any line matches a marker, record MarkerMatch
    # 4. Compute file confidence:
    #    - high: ≥2 matches from same tool
    #    - medium: 1 match from any tool
    # 5. Return DetectionResult per file
```

- Only analyzes added lines (diff lines starting with `+`)
- Case-insensitive matching
- Configurable pattern set — can be extended via policy file in Phase 2

### 5.5 Detector: Style-Based (`src/guardian/detector/style.py`)

Phase 2 implementation. Stub in Phase 1 that returns empty results with TODO logging.

**Interface (Phase 2):**
```python
def analyze_by_style(
    diff: str,
    model_endpoint: str,
    api_key: str | None = None,
) -> list[DetectionResult]:
    # 1. Extract code blocks from diff (added lines)
    # 2. Send to LLM with classification prompt
    # 3. Parse response for per-file AI likelihood scores
    # 4. Return DetectionResult with confidence="low" for AI-likely files
```

**Prompt template (to be refined in Phase 2):**
```
Analyze the following code diff. For each file, determine if it was likely
generated or heavily assisted by an AI coding tool. Consider:
- Overly verbose comments explaining obvious code
- Unusual variable naming patterns
- Hallucinated or non-existent API calls
- Repetitive or boilerplate-heavy patterns
- Lack of error handling for edge cases

Return a JSON array: [{"file": "...", "ai_likelihood": 0.0-1.0, "indicators": [...]}]
```

### 5.6 Reviewer Engine (`src/guardian/reviewer/engine.py`)

```python
def evaluate(
    detections: list[DetectionResult],
    policy: PolicyConfig,
    diff: str,
) -> ReviewResult:
    violations: list[Violation] = []
    for rule in policy.rules:
        if not rule.enabled:
            continue
        rule_fn = BUILTIN_RULES.get(rule.name)
        if not rule_fn:
            continue
        rule_violations = rule_fn(detections, diff, rule.severity)
        violations.extend(rule_violations)

    risk_level = compute_risk_level(violations)
    return ReviewResult(violations=violations, risk_level=risk_level, ...)
```

### 5.7 Built-in Rules (`src/guardian/reviewer/rules.py`)

Each rule is a function with signature:
```python
RuleFn = Callable[
    [list[DetectionResult], str, str],  # detections, diff, severity
    list[Violation],
]
```

**Rule: hallucinated-api**
- Scans added lines for function/method calls matching known hallucination patterns
- Checks against a built-in registry of known-real APIs per language
- Flags function names that look plausible but don't exist in stdlib or common libraries
- Pattern: `[A-Za-z_][A-Za-z0-9_]*\(` — then lookup against known API set

**Rule: missing-error-handling**
- Scans AI-detected files for bare `except:` / `catch` blocks without specific exception types
- Flags missing `try`/`finally` cleanup blocks in resource-heavy functions
- Flags missing `null`/`None` checks after API calls

**Rule: hardcoded-secrets**
- Regex patterns: API keys (`sk-...`, `AKIA...`), tokens, passwords
- Flags any match in added lines of AI-detected files
- Skips test files and known false-positive paths

### 5.8 PR Client (`src/guardian/pr/client.py`)

Wrapper around GitHub REST API via `httpx`:

```python
class GitHubClient:
    def __init__(self, token: str, repo: str):
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_pr_diff(self, pr_number: int) -> str:
        # GET /repos/{repo}/pulls/{number}
        # Accept: application/vnd.github.v3.diff
        ...

    def get_commit_diff(self, commit_sha: str) -> str:
        # GET /repos/{repo}/commits/{sha}
        ...

    def get_file_content(self, path: str, ref: str = "HEAD") -> str | None:
        # GET /repos/{repo}/contents/{path}?ref={ref}
        ...

    def post_comment(self, pr_number: int, body: str) -> int:
        # POST /repos/{repo}/issues/{pr_number}/comments
        # Returns comment ID
        ...

    def add_label(self, pr_number: int, label: str) -> None:
        # POST /repos/{repo}/issues/{pr_number}/labels
        ...

    def remove_label(self, pr_number: int, label: str) -> None:
        # DELETE /repos/{repo}/issues/{pr_number}/labels/{label}
        ...

    def create_check_run(self, name: str, conclusion: str, output: dict) -> None:
        # POST /repos/{repo}/check-runs
        ...

    def update_check_run(self, check_run_id: int, conclusion: str, output: dict) -> None:
        # PATCH /repos/{repo}/check-runs/{check_run_id}
        ...

    def get_reactions(self, comment_id: int) -> list[dict]:
        # GET /repos/{repo}/issues/comments/{comment_id}/reactions
        ...

    def post_reaction(self, comment_id: int, content: str) -> None:
        # POST /repos/{repo}/issues/comments/{comment_id}/reactions
        ...
```

**Rate Limiting:**
- Respect `X-RateLimit-Remaining` header
- Back off on `429` with `Retry-After`
- Use GitHub App installation tokens (if available) for higher limits

### 5.9 Commentator (`src/guardian/pr/commentator.py`)

Generates the markdown comment body using a Jinja2 template or f-string:

```python
def generate_comment(
    review: ReviewResult,
    mode: str,                     # "advisory" | "enforcement"
    policy_url: str | None,       # Link to vault docs
) -> str:
    ...
```

**Template structure:**
```
🤖 **AI Code Guardian — Review Summary**

**Risk Level:** {emoji} **{risk_level}** ({violation_count} violation(s))

<details>
<summary>⚠️ Rule: {rule_name} — `{file}:{line}`</summary>

{explanation}

**Recommendation:** {remediation}
[Learn more →]({governance_url})
</details>

---
ℹ️ **{mode} mode** — {mode_description}
Feedback? React 👍 (accurate) or 👎 (false positive) to this comment.
```

### 5.10 Labeler (`src/guardian/pr/labeler.py`)

```python
RISK_LABELS: dict[str, str] = {
    "low": "guardian:low",
    "medium": "guardian:medium",
    "high": "guardian:high",
    "critical": "guardian:critical",
}

def apply_risk_label(client: GitHubClient, pr_number: int, risk_level: str) -> None:
    # 1. Remove any existing guardian:* labels
    # 2. Add the new risk label
    ...

def compute_risk_level(violations: list[Violation]) -> str:
    if not violations:
        return "low"
    severities = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    max_sev = max(v.severity for v in violations, key=lambda s: severities[s])
    return max_sev
```

### 5.11 Check Run (`src/guardian/pr/check_run.py`)

Generates the Check Run summary visible in the GitHub Checks tab:

```python
def generate_check_run_output(review: ReviewResult, stats: dict) -> dict:
    return {
        "title": "AI Code Guardian — Review Complete",
        "summary": f"""\
**Risk Level:** {review.risk_level.emoji} {review.risk_level.upper()}
**AI Code:** {stats['ai_file_count']}/{stats['total_file_count']} files ({stats['ai_pct']}%)
**Violations:** {len(review.violations)}
**FPR:** {stats.get('fpr', 'N/A')}
""",
        "text": markdown_to_text(review),  # Plain text version
    }

def determine_conclusion(review: ReviewResult, mode: str) -> str:
    if mode == "advisory":
        return "neutral"  # Never fails in advisory mode
    # enforcement mode:
    if review.risk_level == "critical":
        return "failure"
    return "success"
```

### 5.12 Audit Logger (`src/guardian/audit/logger.py`)

```python
class AuditLogger:
    def __init__(self, repo: str, audit_dir: str):
        # ~/.guardian/audit/{owner}/{repo}.jsonl
        self.path = Path(audit_dir).expanduser() / repo.replace("/", "_") / "audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        with open(self.path, "a") as f:
            f.write(entry.to_json() + "\n")

    def read(self, since: datetime | None = None) -> list[AuditEntry]:
        # Read and parse entries, optionally filtered by timestamp
        ...
```

### 5.13 Metrics Collector (`src/guardian/metrics/collector.py`)

In-memory metrics aggregated from audit log:

```python
class MetricsCollector:
    def __init__(self, audit_logger: AuditLogger):
        self.entries = audit_logger.read()

    @property
    def total_prs(self) -> int: ...

    @property
    def ai_prs(self) -> int: ...          # PRs with at least one AI file

    @property
    def ai_code_pct(self) -> float: ...

    @property
    def violations_by_rule(self) -> dict[str, int]: ...

    @property
    def violation_trends(self) -> list[dict]: ...  # Per-day counts

    @property
    def false_positive_rate(self) -> float: ...

    @property
    def recent_prs(self, limit: int = 20) -> list[dict]: ...
```

### 5.14 Dashboard Server (`src/guardian/server/app.py`)

FastAPI application:

```python
app = FastAPI(title="AI Code Guardian Dashboard")

@app.get("/metrics")
async def metrics():
    # Prometheus-format text output
    ...

@app.get("/dashboard")
async def dashboard(request: Request):
    collector = MetricsCollector(audit_logger)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": collector},
    )

@app.get("/api/stats")
async def api_stats():
    collector = MetricsCollector(audit_logger)
    return collector.to_dict()
```

### 5.15 GitHub Pages Generator (`scripts/generate-pages.sh`)

CI script that:
1. Runs `guardian generate-pages --audit-dir ~/.guardian/audit --output ./_pages`
2. Commits `./_pages` to `gh-pages` branch
3. Pushes to deploy GitHub Pages

---

## 6. Error Handling Strategy

### 6.1 Failure Modes

| Scenario | Behavior | CI Status |
|---|---|---|
| Config file invalid (YAML parse error) | Post error comment on PR with details | ❌ failure |
| Config file invalid (schema violation) | Post error comment on PR with details | ❌ failure |
| GitHub API unavailable | Retry 3x with exponential backoff, then skip | ⚪ skipped |
| GitHub API rate limited | Wait `Retry-After` seconds, retry, then skip | ⚪ skipped |
| Detection engine crashes | Log error to audit, skip analysis | ⚪ skipped |
| Comment post fails | Log error, continue (label + check run still posted) | ⚪ neutral |
| Label apply fails | Log error, continue | ⚪ neutral |
| Check run creation fails | Log error, continue | ⚪ neutral |
| Audit log write fails (disk full) | Log to stderr, continue | ⚪ neutral |
| Metrics collector fails | Log error, skip metrics update | ⚪ neutral |
| Style detection LLM timeout (Phase 2) | Fall back to marker-only, log warning | ⚪ neutral |

### 6.2 Graceful Degradation Chain

```
style detection (if enabled)
    │ fail
    ▼
marker detection (always primary)
    │ fail
    ▼
no detection (skip analysis, log error)
    │
    ▼
comment: "Guardian analysis unavailable due to [reason]"
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Module | Tests | Fixtures |
|---|---|---|
| `detector/test_marker.py` | Each marker pattern matches known AI diffs. No false positives on human diffs. Case insensitivity. | `pr_diff_ai.txt`, `pr_diff_human.txt` |
| `policy/test_loader.py` | Valid YAML loads correctly. Invalid YAML raises. Schema violations raise with field path. | `guardian-policy-valid.yml`, `guardian-policy-invalid.yml` |
| `reviewer/test_engine.py` | 3 rules fire correctly. Empty detections = no violations. Disabled rules don't fire. Severity sorting. | DetectionResult fixtures |
| `reviewer/test_rules.py` | Each rule detects known patterns. No false positives on clean code. | Code snippet strings |
| `pr/test_commentator.py` | Comment format matches template. Handles 0, 1, 5, 20+ violations. Mode text correct. | ReviewResult fixtures |
| `pr/test_labeler.py` | Risk level mapping. Label removal + addition. | Mock GitHubClient |
| `pr/test_check_run.py` | Summary format. Conclusion logic (advisory=neutral, enforcement=critical→failure). | ReviewResult fixtures |
| `pr/test_client.py` | API calls correct. Rate limit handling. Error responses. | `responses` / `pytest-httpx` mocking |
| `audit/test_logger.py` | Append creates entry. Read returns entries. file-per-repo isolation. | Temp directory |
| `cli/test_cli.py` | Arg parsing. Subcommand dispatch. Exit codes. | (argparse tests) |

### 7.2 Integration Tests

- **End-to-end mock test:** Mock GitHub API → run `guardian detect` → verify comment body, label, check run, audit entry
- **GitHub Actions docker test:** Build Docker image → run with fake event payload → verify output

### 7.3 Performance Tests

- Benchmark against 500-line PR diff: target <2 min total
- Benchmark against 2000-line PR diff: verify line-limit truncation works
- Measure audit log write throughput

### 7.4 Test Fixtures (`tests/fixtures/`)

- `pr_diff_ai.txt`: Multi-file PR diff with Copilot + Cursor + Claude Code markers mixed across files
- `pr_diff_human.txt`: Equivalent-sized diff with zero AI markers (for FPR testing)
- `guardian-policy-valid.yml`: Full valid config with all 3 rules
- `guardian-policy-invalid.yml`: Invalid YAML + schema violations (unknown field, bad severity)

---

## 8. GitHub Action (`action.yml`)

```yaml
name: 'AI Code Guardian'
description: 'Detect AI-generated code in PRs and enforce governance policies'
author: 'deghosal-2026'
branding:
  icon: 'shield'
  color: 'blue'

inputs:
  github_token:
    description: 'GitHub token for API access'
    required: true
    default: ${{ github.token }}
  policy_path:
    description: 'Path to guardian-policy.yml'
    required: false
    default: 'guardian-policy.yml'
  mode:
    description: 'Override mode (advisory/enforcement)'
    required: false

runs:
  using: 'docker'
  image: 'Dockerfile'
```

---

## 9. Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/
COPY scripts/ scripts/

ENTRYPOINT ["python", "-m", "guardian"]
```

---

## 10. Dependencies (`pyproject.toml`)

```toml
[project]
name = "ai-code-guardian"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.5",
    "pyyaml>=6.0",
    "fastapi>=0.109",
    "uvicorn[standard]>=0.27",
    "jinja2>=3.1",
    "prometheus-client>=0.19",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-httpx>=0.30",
    "ruff>=0.3",
    "mypy>=1.8",
]

[project.scripts]
guardian = "guardian.cli:main"
```

---

## 11. Ticket Breakdown (for GitHub Issues)

Each ticket maps to a GitHub issue. Naming convention: `[M{N}] {Title}` — e.g., `[M1] Implement marker-based detection engine`. Labels use the taxonomy from the project board. Tickets are organized by milestone in build order.

---

### Milestone M1: Detection Engine

**Ticket M1-DEV:** Implement marker-based detection engine
- **Labels:** `dev`, `epic`
- **Depends on:** None
- **Files:** `src/guardian/detector/models.py`, `src/guardian/detector/marker.py`
- **Description:** Build the core detection engine that scans PR diffs for AI attribution markers from Copilot, Cursor, and Claude Code. Define detection result models. Only scan added lines (`+` prefix in diff). Return per-file confidence scores.
- **Acceptance Criteria:**
  - [ ] `DetectionResult` and `MarkerMatch` dataclasses defined in `models.py`
  - [ ] Regex patterns for all 3 tools (Copilot, Cursor, Claude Code) defined in `marker.py`
  - [ ] `analyze_diff(diff: str) -> list[DetectionResult]` function implemented
  - [ ] Only added lines in diff are scanned (not removed or context lines)
  - [ ] Per-file confidence: high (≥2 matches same tool), medium (1 match any tool)
  - [ ] Case-insensitive pattern matching
  - [ ] Style detection stub created (`detector/style.py` returning `[]`)

**Ticket M1-TEST:** Write tests for detection engine
- **Labels:** `test`
- **Depends on:** M1-DEV
- **Files:** `tests/test_detector.py`, `tests/fixtures/pr_diff_ai.txt`, `tests/fixtures/pr_diff_human.txt`
- **Description:** Create test fixtures and unit tests for marker-based detection. Verify patterns match correctly on known AI diffs and produce no false positives on human diffs.
- **Acceptance Criteria:**
  - [ ] `pr_diff_ai.txt` fixture: multi-file diff with Copilot + Cursor + Claude Code markers
  - [ ] `pr_diff_human.txt` fixture: equivalent diff with zero AI markers
  - [ ] Each marker pattern verified independently
  - [ ] Case-insensitivity verified
  - [ ] No detections on human diff (zero false positives by construction)
  - [ ] Empty diff returns empty list
  - [ ] Line numbering in matches matches diff line numbers

---

### Milestone M2: Policy Engine

**Ticket M2-DEV:** Implement policy loader and schema
- **Labels:** `dev`
- **Depends on:** M1-DEV
- **Files:** `src/guardian/policy/models.py`, `src/guardian/policy/loader.py`
- **Description:** Build the YAML policy loader with pydantic schema validation. Define `PolicyConfig` and `RuleConfig` models. Handle missing file (use defaults), invalid YAML, and schema violations with actionable error messages.
- **Acceptance Criteria:**
  - [ ] `PolicyConfig` pydantic model with version, mode, detection, rules fields
  - [ ] `RuleConfig` with name, severity, enabled, description
  - [ ] Schema validation: duplicate rule names rejected
  - [ ] Schema validation: unknown severity values rejected
  - [ ] Missing policy file → return default config (advisory mode, 3 rules enabled)
  - [ ] YAML parse errors → raise with file path + line number + error detail
  - [ ] Field validator for severity: only low/medium/high/critical allowed

**Ticket M2-DEV:** Implement 3 built-in review rules
- **Labels:** `dev`
- **Depends on:** M2-DEV
- **Files:** `src/guardian/reviewer/rules.py`, `src/guardian/reviewer/models.py`, `src/guardian/reviewer/engine.py`
- **Description:** Implement the 3 built-in policy rules (hallucinated-api, missing-error-handling, hardcoded-secrets). Build the review engine that applies enabled rules to detection results and diff content. Compute risk level from violations.
- **Acceptance Criteria:**
  - [ ] `Violation` and `ReviewResult` dataclasses defined
  - [ ] `hallucinated-api` rule: scans for plausible but non-existent API calls in AI-detected files
  - [ ] `missing-error-handling` rule: flags bare excepts/catch in AI-detected files
  - [ ] `hardcoded-secrets` rule: regex patterns for API keys, tokens, passwords in AI-detected files
  - [ ] Each rule accepts `(detections, diff, severity)` and returns `list[Violation]`
  - [ ] `evaluate()` function: iterates enabled rules, collects violations, computes risk level
  - [ ] Risk level = highest severity among violations (low → medium → high → critical)
  - [ ] Empty detections → zero violations
  - [ ] Disabled rules don't fire

**Ticket M2-TEST:** Write tests for policy engine
- **Labels:** `test`
- **Depends on:** M2-DEV
- **Files:** `tests/test_policy.py`, `tests/test_reviewer.py`, `tests/fixtures/guardian-policy-valid.yml`, `tests/fixtures/guardian-policy-invalid.yml`
- **Description:** Test policy loading, schema validation, and all 3 rules.
- **Acceptance Criteria:**
  - [ ] Valid YAML loads successfully with correct field values
  - [ ] Invalid YAML (syntax error) raises with file + line
  - [ ] Bad severity value raises schema error with field path
  - [ ] Duplicate rule names raises schema error
  - [ ] Missing file returns default config
  - [ ] Each rule detects its target pattern on known-positive code snippets
  - [ ] Each rule produces no violations on clean code
  - [ ] Severity sorting works correctly
  - [ ] Disabled rule does not appear in ReviewResult.violations

---

### Milestone M3: PR Integration

**Ticket M3-DEV:** Implement GitHub API client
- **Labels:** `dev`
- **Depends on:** M1-DEV, M2-DEV
- **Files:** `src/guardian/pr/client.py`
- **Description:** Build the `GitHubClient` class wrapping the GitHub REST API via httpx. Support diff fetching, comment posting, label management, check run creation, and reaction reading. Handle rate limiting with exponential backoff.
- **Acceptance Criteria:**
  - [ ] `get_pr_diff(pr_number)` returns unified diff string
  - [ ] `post_comment(pr_number, body)` posts issue comment, returns comment ID
  - [ ] `add_label(pr_number, label)` and `remove_label(pr_number, label)` working
  - [ ] `create_check_run(name, conclusion, output)` creates check run
  - [ ] `update_check_run(check_run_id, conclusion, output)` updates existing
  - [ ] `get_reactions(comment_id)` returns reaction list
  - [ ] Rate limit: respect Retry-After header with configurable max retries
  - [ ] All API calls use `Authorization: Bearer {token}` header
  - [ ] Token never logged or exposed in error messages
  - [ ] Client accepts `(token, repo)` constructor

**Ticket M3-DEV:** Implement comment generator
- **Labels:** `dev`
- **Depends on:** M2-DEV
- **Files:** `src/guardian/pr/commentator.py`
- **Description:** Generate the markdown PR comment body with collapsible violation sections. Group violations by severity (highest first). Include explanation, remediation, and governance link per violation. Summarize if >20 violations.
- **Acceptance Criteria:**
  - [ ] Comment starts with emoji + risk level + violation count summary header
  - [ ] Each violation rendered as `<details><summary>` block
  - [ ] Each block contains: pattern, explanation, remediation, governance link
  - [ ] Violations grouped by severity (critical first, low last)
  - [ ] 0 violations → "No violations found" message
  - [ ] >20 violations → "Showing top 20 of N" with remaining summarized
  - [ ] Footer shows mode (advisory/enforcement) + feedback instructions (👍/👎)
  - [ ] `generate_comment(review, mode, policy_url) -> str`

**Ticket M3-DEV:** Implement labeler
- **Labels:** `dev`
- **Depends on:** M3-DEV (client)
- **Files:** `src/guardian/pr/labeler.py`
- **Description:** Map risk level to guardian:* label and apply via GitHubClient. Remove any existing guardian:* labels before applying new one.
- **Acceptance Criteria:**
  - [ ] `apply_risk_label(client, pr_number, risk_level)` → removes old labels, adds new one
  - [ ] Label mapping: low→guardian:low, medium→guardian:medium, high→guardian:high, critical→guardian:critical
  - [ ] `compute_risk_level(violations)` → returns highest severity string
  - [ ] Empty violations list → "low" risk

**Ticket M3-DEV:** Implement Check Run output
- **Labels:** `dev`
- **Depends on:** M3-DEV (client), M2-DEV
- **Files:** `src/guardian/pr/check_run.py`
- **Description:** Generate the structured Check Run summary visible in the GitHub Checks tab. Include risk level, AI code stats, violation counts. Determine conclusion based on mode and risk level.
- **Acceptance Criteria:**
  - [ ] `generate_check_run_output(review, stats) -> dict` with title, summary, text fields
  - [ ] Summary shows: risk level emoji+text, AI file count/percentage, violation count, FPR
  - [ ] `determine_conclusion(review, mode)` → advisory returns "neutral", enforcement + critical returns "failure", else "success"
  - [ ] Text field contains plain-text summary of violations

**Ticket M3-TEST:** Write tests for PR integration
- **Labels:** `test`
- **Depends on:** M3-DEV (all sub-tickets)
- **Files:** `tests/test_pr_client.py`, `tests/test_commentator.py`, `tests/test_labeler.py`, `tests/test_check_run.py`
- **Description:** Unit tests for GitHubClient, commentator, labeler, and check run modules. Mock HTTP responses for API tests.
- **Acceptance Criteria:**
  - [ ] Client: each API method tested with mock httpx responses
  - [ ] Client: rate limit backoff tested (429 response → retry after wait)
  - [ ] Client: token auth header verified in test assertions
  - [ ] Commentator: comment format verified (0, 1, 5, 25 violations)
  - [ ] Commentator: mode text correct for advisory vs enforcement
  - [ ] Labeler: correct label applied per risk level
  - [ ] Labeler: old labels removed before new applied
  - [ ] Check Run: summary format matches spec
  - [ ] Check Run: conclusion logic correct per mode

**Ticket M3-DOCS:** Document PR integration setup
- **Labels:** `docs`
- **Depends on:** M3-DEV
- **Description:** Write documentation explaining how Guardian comments, labels, and check runs work. Include example comment screenshots.
- **Acceptance Criteria:**
  - [ ] PR comment format documented with example
  - [ ] Label meanings documented
  - [ ] Check Run output documented
  - [ ] How to provide feedback (👍/👎) documented

---

### Milestone M4: Audit Trail

**Ticket M4-DEV:** Implement audit log
- **Labels:** `dev`
- **Depends on:** M1-DEV, M2-DEV
- **Files:** `src/guardian/audit/models.py`, `src/guardian/audit/logger.py`
- **Description:** Build append-only JSONL audit logger. Each event records: PR/commit ID, timestamp, actions taken, detection results, violations, errors. File-per-repo isolation in configurable directory.
- **Acceptance Criteria:**
  - [ ] `AuditEntry` dataclass with all fields (version, timestamp, event_id, repo, pr_number, action, detection_results, violations, risk_level, feedback, duration_ms, error)
  - [ ] `AuditLogger(repo, audit_dir)` creates file at `{audit_dir}/{repo}/audit.jsonl`
  - [ ] `append(entry)` writes one JSON line, appends to file
  - [ ] `read(since)` parses all entries, optionally filtered by timestamp
  - [ ] File is created on first write (mkdir -p parent dirs)
  - [ ] Never modifies existing entries (append-only enforced at API level)
  - [ ] Configurable directory (default: `~/.guardian/audit/`)

**Ticket M4-TEST:** Write tests for audit log
- **Labels:** `test`
- **Depends on:** M4-DEV
- **Files:** `tests/test_audit.py`
- **Acceptance Criteria:**
  - [ ] Append creates file with valid JSONL
  - [ ] Read returns all entries
  - [ ] Read(since) filters correctly
  - [ ] Multiple appends preserved in order
  - [ ] No modification of existing entries possible via API
  - [ ] File-per-repo isolation verified
  - [ ] Handles Unicode content in entries

---

### Milestone M5: CLI Framework

**Ticket M5-DEV:** Implement CLI framework and config loader
- **Labels:** `dev`, `epic`
- **Depends on:** M1-DEV, M2-DEV, M3-DEV, M4-DEV
- **Files:** `src/guardian/cli.py`, `src/guardian/__main__.py`, `src/guardian/config.py`, `src/guardian/action.py`
- **Description:** Build the argparse CLI with subcommands: `detect`, `serve`, `check-config`, `generate-pages`, `version`. Implement the `GuardianConfig` pydantic model for runtime config. Build the action entry point that reads GitHub Actions env vars and calls `cli.detect()`.
- **Acceptance Criteria:**
  - [ ] `detect` command: accepts `--token`, `--repo`, `--pr` or `--commit`, `--policy`, `--audit-dir`, `--verbose`
  - [ ] `detect` command: orchestrates full flow (config → detect → review → comment → label → check run → audit)
  - [ ] `serve` command: starts FastAPI on configurable port with audit-dir
  - [ ] `check-config` command: validates policy file, exits 0 on pass, 1 on fail
  - [ ] `generate-pages` command: builds static HTML dashboard to output dir
  - [ ] `version` command: prints version from pyproject.toml
  - [ ] `action.py`: reads `GITHUB_REPOSITORY`, `GITHUB_EVENT_NAME`, `GITHUB_EVENT_PATH`, `INPUT_GITHUB_TOKEN` env vars
  - [ ] `action.py`: dispatches to `cli.detect()` with correct PR number or commit SHA
  - [ ] Exit codes: 0 = pass (or advisory violations), 1 = error, 2 = enforcement critical violation
  - [ ] `--verbose` flag enables debug logging to stderr
  - [ ] `GuardianConfig` validates token presence, repo format

**Ticket M5-TEST:** Write tests for CLI
- **Labels:** `test`
- **Depends on:** M5-DEV
- **Files:** `tests/test_cli.py`
- **Acceptance Criteria:**
  - [ ] Each subcommand parses correctly with required and optional args
  - [ ] Missing required args produce error message and non-zero exit
  - [ ] `detect` command orchestrates all sub-modules (verified via mocking)
  - [ ] Exit codes correct per mode (advisory vs enforcement)
  - [ ] `check-config` exit code correct for valid vs invalid policy
  - [ ] Version flag prints correct version string

**Ticket M5-DOCS:** Document CLI commands
- **Labels:** `docs`
- **Depends on:** M5-DEV
- **Description:** Document all CLI commands, options, and exit codes with usage examples.
- **Acceptance Criteria:**
  - [ ] All 5 subcommands documented with examples
  - [ ] Exit codes documented
  - [ ] Environment variables documented for action mode

---

### Milestone M6: Dashboard

**Ticket M6-DEV:** Implement metrics collector
- **Labels:** `dev`
- **Depends on:** M4-DEV
- **Files:** `src/guardian/metrics/collector.py`
- **Description:** Build the in-memory metrics collector that reads the audit log and computes dashboard stats: PRs analyzed, AI code %, violations by rule, violation trends, FPR, recent PRs.
- **Acceptance Criteria:**
  - [ ] `MetricsCollector(audit_logger)` reads audit entries on init
  - [ ] `total_prs` property returns count of unique PRs
  - [ ] `ai_code_pct` returns ratio of files with detections to total scanned
  - [ ] `violations_by_rule` returns dict of rule_name → count
  - [ ] `violation_trends` returns per-day violation counts (last 30 days)
  - [ ] `false_positive_rate` returns FP / (FP + confirmed) ratio
  - [ ] `recent_prs(limit=20)` returns list of most recent PRs with risk levels

**Ticket M6-DEV:** Implement metrics exporter
- **Labels:** `dev`
- **Depends on:** M6-DEV
- **Files:** `src/guardian/metrics/prometheus.py`
- **Description:** Expose metrics in Prometheus text format for local scraping and future Grafana integration.
- **Acceptance Criteria:**
  - [ ] PrometheusCounter, Gauge, Histogram defined for all metrics
  - [ ] `/metrics` endpoint returns valid Prometheus-format text
  - [ ] Metrics reset on process restart (in-memory)

**Ticket M6-DEV:** Implement dashboard server
- **Labels:** `dev`
- **Depends on:** M6-DEV, M6-DEV
- **Files:** `src/guardian/server/app.py`, `src/guardian/server/templates/dashboard.html`
- **Description:** Build FastAPI server with Jinja2 dashboard template. Serve `/dashboard` (HTML), `/api/stats` (JSON), and `/metrics` (Prometheus). Generate static HTML for GitHub Pages deployment.
- **Acceptance Criteria:**
  - [ ] `/dashboard` renders Jinja2 template with all stats
  - [ ] `/api/stats` returns JSON with all computed metrics
  - [ ] `/metrics` returns Prometheus text format
  - [ ] Dashboard HTML can be generated statically (via `generate-pages` command)
  - [ ] Template shows: PRs analyzed, AI code %, violations by rule (bar chart), trend line, FPR, recent PRs table
  - [ ] `generate-pages` writes static HTML + assets to output directory
  - [ ] `scripts/generate-pages.sh` CI script deploys to gh-pages branch

**Ticket M6-DEV:** Implement `guardian serve` CLI command
- **Labels:** `dev`
- **Depends on:** M6-DEV, M6-DEV, M6-DEV
- **Description:** Wire the dashboard server into the CLI `serve` command. Accept --port and --audit-dir flags.
- **Acceptance Criteria:**
  - [ ] `guardian serve --port 8080` starts server on port 8080
  - [ ] Server reads from configured audit directory
  - [ ] Graceful shutdown on SIGINT/SIGTERM
  - [ ] Server starts immediately, no background threads

**Ticket M6-TEST:** Write tests for dashboard and metrics
- **Labels:** `test`
- **Depends on:** M6-DEV (all sub-tickets)
- **Description:** Test metrics computation and dashboard endpoints.
- **Acceptance Criteria:**
  - [ ] Metrics computed correctly from sample audit log
  - [ ] FPR calculation verified (FP / (FP + confirmed))
  - [ ] Dashboard endpoints return 200 with correct content type
  - [ ] Static HTML generation produces valid output

**Ticket M6-DOCS:** Document dashboard usage
- **Labels:** `docs`
- **Depends on:** M6-DEV
- **Description:** Document how to start the dashboard locally, access GitHub Pages dashboard, and interpret the metrics.
- **Acceptance Criteria:**
  - [ ] `guardian serve` usage documented
  - [ ] GitHub Pages dashboard documented
  - [ ] Each metric explained (what it means, how it's calculated)

---

### Milestone M7: GitHub Action Packaging

**Ticket M7-DEV:** Create GitHub Action and Docker packaging
- **Labels:** `dev`, `release`
- **Depends on:** M5-DEV
- **Files:** `action.yml`, `Dockerfile`, `pyproject.toml`, `.gitignore`
- **Description:** Create the GitHub Action metadata file, Docker image for the runner, and Python project configuration (pyproject.toml). Ensure the action can be referenced via `uses: deghosal-2026/ai-code-guardian@v1`.
- **Acceptance Criteria:**
  - [ ] `action.yml` with correct metadata, inputs, and Docker image reference
  - [ ] Dockerfile based on python:3.12-slim, installs package, sets entrypoint
  - [ ] `pyproject.toml` with all runtime dependencies (httpx, pydantic, pyyaml, fastapi, uvicorn, jinja2, prometheus-client)
  - [ ] `pyproject.toml` with dev dependencies (pytest, pytest-httpx, ruff, mypy)
  - [ ] Docker image builds successfully
  - [ ] Docker image runs `guardian --help` and shows all subcommands

**Ticket M7-TEST:** Test Docker image and action.yml
- **Labels:** `test`
- **Depends on:** M7-DEV
- **Description:** Build Docker image, verify entrypoint works, verify action.yml is valid.
- **Acceptance Criteria:**
  - [ ] `docker build` succeeds
  - [ ] `docker run image guardian --help` outputs all commands
  - [ ] `docker run image guardian detect --help` shows detect flags
  - [ ] `action.yml` passes GitHub Actions validation (no syntax errors)

**Ticket M7-RELEASE:** Set up versioning and changelog
- **Labels:** `release`
- **Depends on:** M7-DEV
- **Description:** Set up semver versioning in pyproject.toml, create CHANGELOG.md, set up git tags for releases.
- **Acceptance Criteria:**
  - [ ] `pyproject.toml` has correct version field (0.1.0 initial)
  - [ ] `CHANGELOG.md` created with initial entry
  - [ ] Release process documented (update version, tag, push)

---

### Milestone M8: Reference Files & Workflow

**Ticket M8-DEV:** Create default policy and example workflow
- **Labels:** `dev`, `docs`
- **Depends on:** M7-DEV
- **Files:** `guardian-policy.yml`, `.github/workflows/guardian.yml`
- **Description:** Create the reference `guardian-policy.yml` with all 3 rules enabled in advisory mode. Create the example GitHub Actions workflow that adopting repos copy-paste to enable Guardian.
- **Acceptance Criteria:**
  - [ ] `guardian-policy.yml` is valid YAML passing schema validation
  - [ ] All 3 rules included with sensible descriptions
  - [ ] Mode set to `advisory` by default
  - [ ] `.github/workflows/guardian.yml` triggers on `pull_request` (and `push` commented out as opt-in)
  - [ ] Workflow uses `uses: deghosal-2026/ai-code-guardian@v1`
  - [ ] Workflow passes `github.token` as `github_token` input

---

### Milestone M9: Documentation & Release Readiness

**Ticket M9-DOCS:** Write README
- **Labels:** `docs`, `release`
- **Depends on:** M7-DEV, M8-DEV
- **Files:** `README.md`
- **Description:** Write comprehensive README covering: what Guardian does, quick start (2 steps), policy file reference, CLI reference, dashboard, metrics, privacy model, phase model (advisory → enforcement), and links to vault docs.
- **Acceptance Criteria:**
  - [ ] Project description and purpose clearly stated
  - [ ] Quick start: 2-step setup (add policy + workflow) with copy-paste examples
  - [ ] Policy file reference with all 3 rules documented
  - [ ] CLI commands listed with examples
  - [ ] Dashboard usage (GitHub Pages + local serve)
  - [ ] Metrics explained
  - [ ] Privacy model documented (local-only default, external opt-in)
  - [ ] Advisory-first approach explained
  - [ ] Links to vault/governance docs

**Ticket M9-DOCS:** Write CONTRIBUTING guide
- **Labels:** `docs`
- **Depends on:** M7-DEV
- **Files:** `CONTRIBUTING.md`
- **Description:** Document how to set up the dev environment, run tests, lint, and submit PRs.
- **Acceptance Criteria:**
  - [ ] Dev setup instructions (clone, pip install -e ".[dev]", pre-commit)
  - [ ] Test commands (pytest, pytest -v)
  - [ ] Linting commands (ruff check, mypy)
  - [ ] PR guidelines and branch naming convention

**Ticket M9-RELEASE:** End-to-end validation on team repo
- **Labels:** `release`
- **Depends on:** M9-DOCS, M8-DEV, M7-DEV
- **Description:** Onboard Guardian onto the first real team repo. Verify end-to-end flow: PR opened → Guardian detects AI code → posts comment → assigns label → check run visible → audit log written.
- **Acceptance Criteria:**
  - [ ] Guardian Action runs on PR in team repo
  - [ ] Comment posted with correct format and violations
  - [ ] Risk label applied to PR
  - [ ] Check Run summary visible in Checks tab
  - [ ] Audit log entry created
  - [ ] Dashboard (`guardian serve`) shows the PR in recent PRs
  - [ ] GitHub Pages dashboard deployed and accessible
  - [ ] No errors in Action run log

---

### Summary: Total Tickets by Milestone

| Milestone | Dev | Test | Docs | Release | Total |
|---|---|---|---|---|---|
| M1: Detection Engine | 1 | 1 | — | — | 2 |
| M2: Policy Engine | 2 | 1 | — | — | 3 |
| M3: PR Integration | 4 | 1 | 1 | — | 6 |
| M4: Audit Trail | 1 | 1 | — | — | 2 |
| M5: CLI Framework | 1 | 1 | 1 | — | 3 |
| M6: Dashboard | 4 | 1 | 1 | — | 6 |
| M7: Action Packaging | 1 | 1 | — | 1 | 3 |
| M8: Reference Files | 1 | — | — | — | 1 |
| M9: Doc & Release | — | — | 2 | 1 | 3 |
| **Total** | **15** | **7** | **5** | **2** | **29** |

---

## 12. Phase 2 Stubs

To keep Phase 1 clean while designing for Phase 2:

| Component | Phase 1 | Phase 2 |
|---|---|---|
| `detector/style.py` | Empty `analyze_by_style()` that returns `[]` with TODO log | Full LLM classifier |
| `reviewer/rules.py` | 3 built-in rules | User-defined custom rules via policy |
| `pr/commentator.py` | Advisory-only footer | Enforcement footer with block message |
| `pr/check_run.py` | `conclusion="neutral"` always | `conclusion="failure"` for critical in enforcement |
| `config.py` | `detection: "marker"` hardcoded | `detection: "style"` or `"both"` supported |
| `style.py` | Stub | Configurable model endpoint |

---

## 13. Security Considerations

- **Token handling:** `GITHUB_TOKEN` is injected as an environment variable by GitHub Actions. Never logged or exposed in error messages.
- **No secrets in config:** `guardian-policy.yml` must never contain secrets. API keys for style detection go in GitHub Action secrets, not the policy file.
- **Local-first:** Default (marker) mode makes zero outbound network calls beyond the GitHub API.
- **Audit immutability:** JSONL files are append-only. No delete or update operations exist in the API.

---

## 14. Open Technical Decisions (resolve during implementation)

- [ ] **Per-repo audit file naming:** `{owner}_{repo}.jsonl` vs `{owner}/{repo}/audit.jsonl`?
- [ ] **Check Run ID caching:** Should we store check_run_id per PR to allow updates, or always create new check runs?
- [ ] **PR diff truncation:** What's the max line count before we refuse analysis? 2000 lines? 5000?
- [ ] **Parallel file scanning:** Should marker detection process files in parallel (`concurrent.futures`) or sequentially?
- [ ] **Audit log rotation:** Should we rotate logs by size/month, or keep them append-only forever?
- [ ] **Policy file caching:** Should we fetch policy from the PR's head ref or the base ref? (PR's head ref is correct — the policy being proposed should be validated.)
- [ ] **Error comment on existing PR:** If Guardian previously posted an error comment and the config is still broken, should it post another comment or update the existing one?

---

*End of SPEC v1*
