# Fleet IaC Migration — OpenClaw → OpenArms (with Legacy Support)

## Summary

Update openclaw-fleet's IaC to install and use OpenArms instead of OpenClaw, while maintaining backwards compatibility with existing OpenClaw installations. Also inject clean Claude Code session environment variables to prevent telemetry leakage.

## Problem

The fleet IaC currently:
1. Installs `openclaw` globally via npm
2. References `~/.openclaw/` config directory in 15+ scripts
3. Calls `openclaw` CLI commands (onboard, approvals, gateway)
4. Does NOT set telemetry-disabling environment variables for Claude Code sessions
5. Injects fleet-identifying env vars (`FLEET_AGENT`, `FLEET_TASK_ID`) into MCP configs visible to Claude Code

## Design Principles

1. **Dual-vendor support** — detect whether `openarms` or `openclaw` is installed, use whichever is available. OpenArms preferred.
2. **Single config detection** — scripts check `~/.openarms/` first, fall back to `~/.openclaw/`
3. **Clean Claude Code sessions** — inject telemetry-disabling env vars at agent spawn time
4. **No breaking changes** — existing fleet installations continue to work with OpenClaw until migrated

## Changes

### 1. Vendor Detection Helper

Create a shared shell function used by all scripts:

```bash
# Resolve which vendor is installed (openarms preferred over openclaw)
resolve_vendor() {
  if command -v openarms >/dev/null 2>&1; then
    VENDOR_CLI="openarms"
    VENDOR_NAME="OpenArms"
    VENDOR_CONFIG_DIR="${HOME}/.openarms"
    VENDOR_CONFIG_FILE="${VENDOR_CONFIG_DIR}/openarms.json"
    VENDOR_ENV_FILE="${VENDOR_CONFIG_DIR}/.env"
  elif command -v openclaw >/dev/null 2>&1; then
    VENDOR_CLI="openclaw"
    VENDOR_NAME="OpenClaw"
    VENDOR_CONFIG_DIR="${HOME}/.openclaw"
    VENDOR_CONFIG_FILE="${VENDOR_CONFIG_DIR}/openclaw.json"
    VENDOR_ENV_FILE="${VENDOR_CONFIG_DIR}/.env"
  else
    echo "ERROR: Neither openarms nor openclaw found in PATH" >&2
    return 1
  fi
}
```

### 2. Scripts to Update

All scripts below currently hardcode `openclaw` / `~/.openclaw/`. Each needs to source the vendor detection helper and use the resolved variables.

| Script | Current References | Change |
|--------|-------------------|--------|
| `scripts/install-openclaw.sh` | `npm install -g openclaw`, `openclaw --version` | Install openarms from `../openarms`, fall back to openclaw |
| `scripts/configure-openclaw.sh` | `~/.openclaw/openclaw.json`, `openclaw onboard`, `openclaw approvals` | Use `$VENDOR_CLI`, `$VENDOR_CONFIG_FILE` |
| `scripts/configure-auth.sh` | `~/.openclaw/.env` | Use `$VENDOR_ENV_FILE` |
| `scripts/configure-channel.sh` | `~/.openclaw/openclaw.json`, `openclaw agents bind` | Use `$VENDOR_CLI`, `$VENDOR_CONFIG_FILE` |
| `scripts/clean-gateway-config.sh` | `~/.openclaw/openclaw.json` | Use `$VENDOR_CONFIG_FILE` |
| `scripts/clean-stale-agents.sh` | `~/.openclaw/agents/`, `~/.openclaw/openclaw.json`, `~/.openclaw/logs/` | Use `$VENDOR_CONFIG_DIR` |
| `scripts/refresh-auth.sh` | `~/.openclaw/.env` | Use `$VENDOR_ENV_FILE` |
| `scripts/install-service.sh` | `command -v openclaw`, systemd template vars | Use `$VENDOR_CLI` |
| `scripts/setup-irc.sh` | `~/.openclaw/openclaw.json` | Use `$VENDOR_CONFIG_FILE` |
| `scripts/ws-monitor.sh` | `~/.openclaw/openclaw.json`, `'openclaw-control-ui'` | Use `$VENDOR_CONFIG_FILE`, `'${VENDOR_CLI}-control-ui'` |
| `setup.sh` | `openclaw onboard`, `~/.openclaw/openclaw.json` | Use `$VENDOR_CLI`, `$VENDOR_CONFIG_FILE` |
| `gateway/setup.py` | `~/.openclaw/openclaw.json`, `"OpenClaw Fleet"` | Read from resolved config path |
| `fleet/cli/dispatch.py` | `~/.openclaw/openclaw.json` | Read from resolved config path |
| `systemd/openclaw-fleet-gateway.service.template` | `{{OPENCLAW_BIN}}`, `{{OPENCLAW_BIN_DIR}}` | Rename to `{{VENDOR_BIN}}`, `{{VENDOR_BIN_DIR}}` |

### 3. Clean Claude Code Sessions

From the Claude Code source cross-reference (`../claude-code-main`), these environment variables control telemetry and detection:

**Must be set in agent spawn environment (gateway/executor.py):**

```python
clean_env = {
    "DISABLE_TELEMETRY": "1",               # Kills Datadog + first-party event logging
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0",     # Belt and suspenders
}

# Must be UNSET (not present) in agent environment:
strip_vars = [
    "CLAUDE_CODE_ENTRYPOINT",          # Auto-detects as 'sdk-cli' if non-interactive
    "CLAUDE_AGENT_SDK_VERSION",         # Appears in User-Agent header
    "CLAUDE_AGENT_SDK_CLIENT_APP",      # Appears in API headers
    "CLAUDE_CODE_CONTAINER_ID",         # Sent in x-claude-remote-container-id header
    "CLAUDE_CODE_REMOTE_SESSION_ID",    # Sent in x-claude-remote-session-id header
    "CLAUDE_CODE_REMOTE",               # Signals remote execution
    "CLAUDECODE",                       # Presence signals Claude Code context
    "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING",  # SDK feature flag
]
```

**Where to apply:** `gateway/executor.py` before `subprocess.run(cmd, ...)` — build a clean env dict, strip identifying vars, inject telemetry disablers.

### 4. MCP Config Sanitization

Current `.mcp.json` files inject fleet env vars that Claude Code can see:

```json
{
  "env": {
    "FLEET_AGENT": "project-manager",
    "FLEET_TASK_ID": "abc123",
    "FLEET_WORKSPACE": "/home/jfortin/openclaw-fleet/workspace-mc-..."
  }
}
```

These are visible to Claude Code's MCP subsystem. While not directly transmitted to Anthropic, they appear in tool call context.

**Solution:** MCP server reads its own config file instead of relying on env vars passed through `.mcp.json`. The fleet MCP server (`fleet/mcp/server.py`) already has access to the workspace — it can discover its own context from files on disk rather than env vars.

**Change:** In `.mcp.json`, only pass `FLEET_DIR` and `PYTHONUNBUFFERED`. The MCP server resolves agent name, task ID, and workspace from a local state file (e.g., `workspace/.fleet-context.json`) written by the dispatch script before spawning.

### 5. Gateway Comments/Branding Cleanup

| File | Current | Change |
|------|---------|--------|
| `gateway/ws_server.py:1` | `"""OCF Gateway WebSocket server — speaks the OpenClaw gateway protocol."""` | Remove product name from docstring |
| `gateway/ws_server.py:33` | `GATEWAY_VERSION = "2026.3.26"` | Change to generic version or remove |
| `gateway/ws_server.py:144` | `"name": "OCF Gateway"` | Change to generic name |
| `gateway/setup.py:293` | `"=== OpenClaw Fleet Setup ==="` | Use vendor-neutral name |
| `gateway/setup.py:326` | `create_organization("OpenClaw Fleet", "openclaw-fleet")` | Use config-driven names |

### 6. Vendor Source Directory

| Current | New |
|---------|-----|
| `vendor/openclaw/` | `vendor/openarms/` (symlink or copy from `../openarms/dist/`) |

The install script builds OpenArms from `../openarms` and copies the dist output to `vendor/openarms/`. Legacy installs keep `vendor/openclaw/` untouched.

## Out of Scope

- OpenArms source changes (already done — separate spec)
- Mission Control changes (MC doesn't touch Anthropic, no fingerprints)
- Agent SOUL.md / HEARTBEAT.md content (these are in Claude Code's context window but are normal CLAUDE.md-style files — not detectable as orchestration)
- Workspace directory renaming (`workspace-mc-*` patterns) — these use UUIDs and don't contain "openclaw"

## Migration Path

1. Build OpenArms, install globally (`npm install -g ../openarms`)
2. Run `openarms onboard` to create `~/.openarms/` config
3. Update fleet scripts to use vendor detection
4. Update gateway to inject clean env vars
5. Update MCP config generation
6. Verify: agent sessions show as normal `claude` CLI sessions in telemetry

Legacy OpenClaw installations continue working until the PO decides to cut over.
