# Contributing to AI Code Guardian

## Quick Start

```bash
git clone https://github.com/deghosal-2026/ai-code-guardian.git
cd ai-code-guardian
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_detector.py -v

# Run with coverage
python -m pytest tests/ --cov=src/guardian

# Run Docker tests (requires Docker)
python -m pytest tests/test_action.py -v
```

## Code Style

- Python 3.11+ target
- Lint with `ruff check src/`
- Line length: 100 characters
- No `type: ignore` comments unless absolutely necessary
- Tests use pytest, pytest-httpx for HTTP mocking

## Project Structure

See [docs/architecture.md](docs/architecture.md) for the full architecture.

## Testing Enforcement Mode

Enforcement mode behavior is tested across 3 test files:

```bash
# Check Run conclusion tests (advisory=neutral, enforcement+critical=failure)
python -m pytest tests/test_check_run.py -v -k "enforcement"

# Action pipeline exit code (2 = enforcement + critical)
python -m pytest tests/test_cli.py -v -k "enforcement"

# Comment text in enforcement mode
python -m pytest tests/test_commentator.py -v -k "enforcement"
```

To test enforcement mode end-to-end locally:

```bash
# 1. Switch policy to enforcement
sed -i '' 's/mode: advisory/mode: enforcement/' guardian-policy.yml

# 2. Run against a PR with critical violations
guardian detect --token $GH_TOKEN --repo owner/repo --pr 42

# 3. Check exit code (should be 2 for critical violations)
echo $?

# 4. Switch back to advisory
sed -i '' 's/mode: enforcement/mode: advisory/' guardian-policy.yml
```

## Pull Request Guidelines

1. Include tests for all new functionality
2. Run the full test suite: `python -m pytest tests/ -v`
3. Run `ruff check src/` before committing
4. Keep PRs focused on a single feature or fix

## Milestones

See [docs/TODO.md](docs/TODO.md) for the current milestone tracking. Open issues on the [issues page](https://github.com/deghosal-2026/ai-code-guardian/issues).

## License

MIT
