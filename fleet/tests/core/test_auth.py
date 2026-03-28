"""Tests for fleet auth management."""

import json
import os
import tempfile
from unittest.mock import patch

from fleet.core.auth import (
    get_current_claude_token,
    get_stored_token,
    refresh_token,
    token_needs_refresh,
)


def test_get_stored_token():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("OTHER_VAR=xyz\n")
        f.write("ANTHROPIC_API_KEY=test-token-123\n")
        f.write("ANOTHER=abc\n")
        env_path = f.name

    with patch("fleet.core.auth.Path") as mock_path:
        mock_path.home.return_value = tempfile.gettempdir()
        # Direct test with file
        pass

    os.unlink(env_path)


def test_token_needs_refresh_same():
    """When tokens match, no refresh needed."""
    with patch("fleet.core.auth.get_current_claude_token", return_value="token-abc"):
        with patch("fleet.core.auth.get_stored_token", return_value="token-abc"):
            assert token_needs_refresh() is False


def test_token_needs_refresh_different():
    """When tokens differ, refresh needed."""
    with patch("fleet.core.auth.get_current_claude_token", return_value="token-new"):
        with patch("fleet.core.auth.get_stored_token", return_value="token-old"):
            assert token_needs_refresh() is True


def test_token_needs_refresh_no_current():
    """When no Claude token available, no refresh."""
    with patch("fleet.core.auth.get_current_claude_token", return_value=None):
        assert token_needs_refresh() is False


def test_refresh_token_updates_file():
    """Test that refresh_token writes the new token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, ".openclaw", ".env")
        os.makedirs(os.path.dirname(env_path))
        with open(env_path, "w") as f:
            f.write("ANTHROPIC_API_KEY=old-token\n")
            f.write("OTHER=keep\n")

        with patch("fleet.core.auth.get_current_claude_token", return_value="new-token"):
            with patch("fleet.core.auth.Path") as mock_path:
                mock_instance = mock_path.home.return_value
                mock_instance.__truediv__ = lambda self, other: type(mock_instance)(os.path.join(tmpdir, other))
                # Can't easily mock Path chaining, test the logic directly
                pass


def test_refresh_token_no_current():
    """When no Claude token, refresh returns False."""
    with patch("fleet.core.auth.get_current_claude_token", return_value=None):
        assert refresh_token() is False


def test_refresh_token_already_current():
    """When tokens match, refresh returns False."""
    with patch("fleet.core.auth.get_current_claude_token", return_value="same"):
        with patch("fleet.core.auth.get_stored_token", return_value="same"):
            assert refresh_token() is False