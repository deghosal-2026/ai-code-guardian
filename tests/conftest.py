"""Shared test fixtures and configuration."""

import pytest


@pytest.fixture
def sample_ai_diff():
    with open("tests/fixtures/pr_diff_ai.txt") as f:
        return f.read()


@pytest.fixture
def sample_human_diff():
    with open("tests/fixtures/pr_diff_human.txt") as f:
        return f.read()
