"""Tests for the GitHub API client (pr/client.py)."""

import json
import pytest
import httpx
from guardian.pr.client import GitHubClient


@pytest.fixture
def client():
    return GitHubClient(token="test-token", repo="owner/repo")


@pytest.fixture
def mock_httpx(httpx_mock):
    return httpx_mock


class TestGitHubClient:
    def test_get_pr_diff(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/42",
            method="GET",
            text="diff --git a/file.py b/file.py\n+print('hello')",
            headers={"Content-Type": "text/plain"},
        )
        diff = client.get_pr_diff(42)
        assert "diff --git" in diff
        assert "print('hello')" in diff

    def test_get_pr_diff_sends_diff_accept_header(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/42",
            method="GET",
            text="diff",
        )
        client.get_pr_diff(42)
        request = mock_httpx.get_request()
        assert request.headers["Accept"] == "application/vnd.github.v3.diff"

    def test_get_commit_diff(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/commits/abc123",
            method="GET",
            text="diff --git a/f.py b/f.py\n+new code",
        )
        diff = client.get_commit_diff("abc123")
        assert "new code" in diff

    def test_get_file_content_returns_decoded(self, client, mock_httpx):
        import base64
        content = base64.b64encode(b"hello world").decode()
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/contents/src/main.py?ref=HEAD",
            method="GET",
            json={"content": content, "encoding": "base64"},
        )
        result = client.get_file_content("src/main.py")
        assert result == "hello world"

    def test_get_file_content_returns_none_on_404(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/contents/missing.py?ref=HEAD",
            method="GET",
            status_code=404,
        )
        result = client.get_file_content("missing.py")
        assert result is None

    def test_post_comment_returns_id(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/issues/42/comments",
            method="POST",
            json={"id": 123},
        )
        comment_id = client.post_comment(42, "Nice PR!")
        assert comment_id == 123

    def test_add_label(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/issues/42/labels",
            method="POST",
            json=[],
        )
        client.add_label(42, "guardian:high")
        request = mock_httpx.get_request()
        assert json.loads(request.content) == {"labels": ["guardian:high"]}

    def test_remove_label(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/issues/42/labels/guardian:low",
            method="DELETE",
            status_code=204,
        )
        client.remove_label(42, "guardian:low")

    def test_create_check_run(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/check-runs",
            method="POST",
            json={"id": 456},
        )
        output = {"title": "Review", "summary": "OK", "text": ""}
        result = client.create_check_run("Guardian Review", "neutral", output)
        assert result["id"] == 456
        request = mock_httpx.get_request()
        body = json.loads(request.content)
        assert body["name"] == "Guardian Review"
        assert body["conclusion"] == "neutral"

    def test_update_check_run(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/check-runs/456",
            method="PATCH",
            status_code=200,
        )
        output = {"title": "Updated", "summary": "Done", "text": ""}
        client.update_check_run(456, "success", output)
        request = mock_httpx.get_request()
        body = json.loads(request.content)
        assert body["conclusion"] == "success"

    def test_get_reactions(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/issues/comments/789/reactions",
            method="GET",
            json=[{"id": 1, "content": "+1"}],
        )
        reactions = client.get_reactions(789)
        assert len(reactions) == 1
        assert reactions[0]["content"] == "+1"

    def test_post_reaction(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/issues/comments/789/reactions",
            method="POST",
            status_code=201,
        )
        client.post_reaction(789, "+1")
        request = mock_httpx.get_request()
        assert json.loads(request.content) == {"content": "+1"}

    def test_auth_header_set_correctly(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            text="diff",
        )
        client.get_pr_diff(1)
        request = mock_httpx.get_request()
        assert request.headers["Authorization"] == "Bearer test-token"

    def test_rate_limit_backoff(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            status_code=429,
            headers={"Retry-After": "0"},
        )
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            text="diff after retry",
        )
        result = client.get_pr_diff(1)
        assert result == "diff after retry"

    def test_server_error_retry(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            status_code=500,
        )
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            text="diff after retry",
        )
        result = client.get_pr_diff(1)
        assert result == "diff after retry"

    def test_all_retries_exhausted_raises(self, client, mock_httpx):
        for _ in range(3):
            mock_httpx.add_response(
                url="https://api.github.com/repos/owner/repo/pulls/1",
                method="GET",
                status_code=500,
            )
        with pytest.raises(httpx.HTTPStatusError):
            client.get_pr_diff(1)

    def test_token_not_in_error_message(self, client, mock_httpx):
        mock_httpx.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            method="GET",
            status_code=401,
        )
        with pytest.raises(httpx.HTTPStatusError) as exc:
            client.get_pr_diff(1)
        assert "test-token" not in str(exc.value)
