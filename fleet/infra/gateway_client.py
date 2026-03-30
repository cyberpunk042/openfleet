"""Gateway client — wrapper around OpenClaw Gateway WebSocket RPC.

Provides the doctor's tools: prune (sessions.delete), force compact
(sessions.compact), inject content (chat.send), and fresh session
creation (sessions.patch).

The gateway communicates via WebSocket JSON-RPC on ws://localhost:18789.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Default gateway WebSocket URL
GATEWAY_WS_URL = "ws://localhost:18789"


async def _gateway_rpc(
    method: str,
    params: dict,
    timeout: float = 10.0,
) -> tuple[bool, dict]:
    """Send a JSON-RPC request to the gateway.

    Args:
        method: RPC method name (e.g., "sessions.delete").
        params: Method parameters.
        timeout: Connection and response timeout in seconds.

    Returns:
        Tuple of (success, response_payload).
    """
    try:
        import websockets
    except ImportError:
        logger.error("websockets package not installed")
        return False, {"error": "websockets not installed"}

    oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(oc_path) as f:
            cfg = json.load(f)
        oc_token = cfg.get("gateway", {}).get("auth", {}).get("token", "")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to read openclaw config: %s", exc)
        return False, {"error": str(exc)}

    try:
        async with websockets.connect(
            GATEWAY_WS_URL,
            origin="http://localhost:18789",
        ) as ws:
            # Read challenge
            await asyncio.wait_for(ws.recv(), timeout=timeout)

            # Authenticate
            await ws.send(json.dumps({
                "type": "req",
                "id": str(uuid.uuid4()),
                "method": "connect",
                "params": {
                    "minProtocol": 3,
                    "maxProtocol": 3,
                    "role": "operator",
                    "scopes": [
                        "operator.read", "operator.admin",
                        "operator.approvals", "operator.pairing",
                    ],
                    "client": {
                        "id": "fleet-doctor",
                        "version": "1.0.0",
                        "platform": "python",
                        "mode": "daemon",
                    },
                    "auth": {"token": oc_token},
                },
            }))
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            auth_resp = json.loads(raw)
            if not auth_resp.get("ok"):
                return False, {"error": "Gateway auth failed"}

            # Send the actual RPC request
            req_id = str(uuid.uuid4())
            await ws.send(json.dumps({
                "type": "req",
                "id": req_id,
                "method": method,
                "params": params,
            }))

            # Read response (skip events until we get our response)
            for _ in range(10):
                raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                resp = json.loads(raw)
                if resp.get("id") == req_id:
                    return resp.get("ok", False), resp.get("payload", {})

            return False, {"error": "No response for request"}

    except asyncio.TimeoutError:
        logger.error("Gateway RPC timeout: %s", method)
        return False, {"error": "timeout"}
    except Exception as exc:
        logger.error("Gateway RPC error: %s: %s", method, exc)
        return False, {"error": str(exc)}


# ─── Doctor's Tools ─────────────────────────────────────────────────────


async def prune_agent(session_key: str) -> bool:
    """Prune an agent — kill the sick session.

    The agent grows back fresh on next heartbeat when the gateway
    creates a new session via sessions.patch.

    Args:
        session_key: The agent's gateway session key.

    Returns:
        True if session was successfully deleted.
    """
    ok, resp = await _gateway_rpc("sessions.delete", {"key": session_key})
    if ok:
        logger.info("Pruned agent session: %s", session_key)
    else:
        logger.error("Failed to prune session %s: %s", session_key, resp)
    return ok


async def force_compact(session_key: str) -> bool:
    """Force compact an agent's context.

    Reduces the agent's context size, stripping what is unwanted,
    unnecessary, or superfluous. Agent continues with lean context.

    Args:
        session_key: The agent's gateway session key.

    Returns:
        True if compaction was successful.
    """
    ok, resp = await _gateway_rpc("sessions.compact", {"key": session_key})
    if ok:
        logger.info("Compacted agent session: %s", session_key)
    else:
        logger.error("Failed to compact session %s: %s", session_key, resp)
    return ok


async def inject_content(session_key: str, content: str) -> bool:
    """Inject content into an agent's session — rules reinjection.

    Sends content as a message into the agent's active session. The
    agent must autocomplete from this content before continuing its
    original work.

    Args:
        session_key: The agent's gateway session key.
        content: The lesson/rules content to inject.

    Returns:
        True if content was successfully sent.
    """
    ok, resp = await _gateway_rpc("chat.send", {
        "sessionKey": session_key,
        "message": content,
        "deliver": False,  # Don't trigger immediate execution
        "idempotencyKey": str(uuid.uuid4()),
    })
    if ok:
        logger.info("Injected content into session: %s (%d chars)", session_key, len(content))
    else:
        logger.error("Failed to inject into session %s: %s", session_key, resp)
    return ok


async def create_fresh_session(session_key: str, label: str = "") -> bool:
    """Create a fresh session for an agent — regrowth after pruning.

    Args:
        session_key: The session key to create.
        label: Optional label (usually agent name).

    Returns:
        True if session was successfully created.
    """
    params = {"key": session_key}
    if label:
        params["label"] = label
    ok, resp = await _gateway_rpc("sessions.patch", params)
    if ok:
        logger.info("Created fresh session: %s (label=%s)", session_key, label)
    else:
        logger.error("Failed to create session %s: %s", session_key, resp)
    return ok