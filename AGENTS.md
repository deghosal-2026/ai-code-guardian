# AGENTS.md — AI Code Guardian

## Constraints & Preferences
- SPEC.md docs/SPEC.md and PRD.md docs/PRD.md are approved reference documents
- No code changes without user direction
- Advisory-first governance model (comment + label, no blocking) per spec

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
