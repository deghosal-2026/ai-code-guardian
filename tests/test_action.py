"""Tests for the Docker image and action packaging."""

import os
import subprocess
import pytest


def test_docker_build_and_version():
    result = subprocess.run(
        ["docker", "run", "--rm", "guardian:test", "version"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "ai-code-guardian v0.1.0"


def test_docker_help():
    result = subprocess.run(
        ["docker", "run", "--rm", "guardian:test", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "usage: guardian" in result.stdout


def test_action_yml_exists():
    assert os.path.exists("action.yml")
    with open("action.yml") as f:
        content = f.read()
    assert "name: 'AI Code Guardian'" in content
    assert "using: 'docker'" in content
    assert "image: 'Dockerfile'" in content


def test_dockerfile_exists():
    assert os.path.exists("Dockerfile")
    with open("Dockerfile") as f:
        content = f.read()
    assert "FROM python:3.12-slim" in content
    assert 'ENTRYPOINT ["python", "-m", "guardian"]' in content


@pytest.mark.parametrize("env_var", [
    "GUARDIAN_TOKEN",
    "GUARDIAN_POLICY_PATH",
    "GUARDIAN_AUDIT_DIR",
    "GUARDIAN_DEBUG",
])
def test_action_env_vars_in_action_yml(env_var):
    with open("action.yml") as f:
        content = f.read()
    assert env_var in content
