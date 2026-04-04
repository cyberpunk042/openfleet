"""Fleet auth management — token refresh and validation.

Handles Claude Code OAuth token rotation automatically.
The token rotates periodically and must be updated in
the vendor env file for the gateway to authenticate with Anthropic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fleet.infra.config_loader import resolve_vendor_env


def get_current_claude_token() -> Optional[str]:
    """Extract current OAuth token from Claude Code credentials."""
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        return None
    try:
        with open(creds_path) as f:
            creds = json.load(f)
        return creds.get("claudeAiOauth", {}).get("accessToken") or None
    except Exception:
        return None


def get_stored_token() -> Optional[str]:
    """Get the token currently stored in the vendor env file."""
    env_path = Path(resolve_vendor_env())
    if not env_path.exists():
        return None
    try:
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def token_needs_refresh() -> bool:
    """Check if the stored token differs from Claude Code's current token."""
    current = get_current_claude_token()
    stored = get_stored_token()
    if not current:
        return False
    return current != stored


def refresh_token() -> bool:
    """Update the stored token with Claude Code's current token.

    Returns True if token was updated, False if no update needed.
    """
    current = get_current_claude_token()
    if not current:
        return False

    stored = get_stored_token()
    if current == stored:
        return False

    env_path = Path(resolve_vendor_env())
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve other env vars
    lines = []
    if env_path.exists():
        lines = [
            l for l in env_path.read_text().splitlines()
            if not l.startswith("ANTHROPIC_API_KEY")
        ]
    lines.append(f"ANTHROPIC_API_KEY={current}")
    env_path.write_text("\n".join(lines) + "\n")
    return True


def needs_gateway_restart() -> bool:
    """Check if the gateway needs restart due to token change.

    The gateway reads the token at startup. If the token changed
    after the gateway started, a restart is needed.
    """
    return token_needs_refresh()