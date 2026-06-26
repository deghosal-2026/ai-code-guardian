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
- No type: ignore comments unless absolutely necessary
- Tests use pytest, pytest-httpx for HTTP mocking

## Project Structure

```
src/guardian/
├── detector/    # AI code detection
├── policy/      # Policy loading
├── reviewer/    # Rule evaluation
├── pr/          # GitHub integration
├── audit/       # Audit logging
├── metrics/     # Dashboard metrics
├── server/      # Dashboard server
├── cli.py       # CLI commands
├── action.py    # Action pipeline
└── config.py    # Configuration
tests/
├── test_detector.py
├── test_policy.py
└── ...
```

## Pull Request Guidelines

1. Include tests for all new functionality
2. Run the full test suite: `python -m pytest tests/ -v`
3. Run `ruff check src/` before committing
4. Keep PRs focused on a single feature or fix
5. Update docs/TODO.md if adding or completing milestones

## Milestones

See [docs/TODO.md](docs/TODO.md) for the current milestone tracking. Open issues are organized by milestone (M1-M9) on the [issues page](https://github.com/deghosal-2026/ai-code-guardian/issues).

## License

MIT
