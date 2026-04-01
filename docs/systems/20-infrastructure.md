# System 20: Infrastructure Clients

**Source:** `fleet/infra/gateway_client.py`, `fleet/infra/mc_client.py`, `fleet/infra/plane_client.py`, `fleet/infra/irc_client.py`, `fleet/infra/ntfy_client.py`, `fleet/infra/gh_client.py`, `fleet/infra/config_loader.py`, `fleet/infra/cache_sqlite.py`
**Status:** 🔨 All clients built and functional. Gateway RPC verified.
**Design docs:** Various (infrastructure supports everything)

---

## Purpose

Client libraries for all external services the fleet talks to. Each client handles authentication, error handling, and retry logic. The fleet never makes raw HTTP calls — always through these clients.

## Key Concepts

### Gateway Client (gateway_client.py)

Talks to OpenClaw Gateway via WebSocket JSON-RPC on `ws://localhost:18789`.

| Function | RPC Method | Purpose |
|----------|-----------|---------|
| `prune_agent(session_key)` | `sessions.delete` | Kill sick session (immune response) |
| `force_compact(session_key)` | `sessions.compact` | Reduce context (teaching) |
| `inject_content(session_key, content)` | `chat.send` | Inject lesson/wake data |
| `create_fresh_session(session_key)` | `sessions.patch` | Fresh session after prune |
| `disable_gateway_cron_jobs()` | file edit | Pause all heartbeats |
| `enable_gateway_cron_jobs()` | file edit | Resume heartbeats |

Auth: reads token from `~/.openclaw/openclaw.json`.

### MC Client (mc_client.py)

Mission Control API client. CRUD for tasks, agents, board memory, approvals, comments.

### Plane Client (plane_client.py)

Plane CE API client. Issues, labels, states, comments, sprints, modules.

### IRC Client (irc_client.py)

IRC message posting. Used by event chains and notifications.

### ntfy Client (ntfy_client.py)

Push notifications. Priority routing (info → progress topic, urgent → alert topic).

### GitHub Client (gh_client.py)

GitHub API for PR creation, branch management, commit metadata.

### Config Loader (config_loader.py)

Loads `config/*.yaml` files: fleet.yaml, phases.yaml, agent-identities.yaml, skill-assignments.yaml.

### Cache (cache_sqlite.py)

SQLite-backed cache for expensive API responses.

## Connections to Other Systems

Every system uses infrastructure clients:
- **Orchestrator** → MC, IRC, Gateway
- **MCP Tools** → MC, GitHub, Plane
- **Notifications** → IRC, ntfy
- **Doctor** → Gateway (prune, compact, inject)
- **Plane Sync** → Plane, MC
- **Events** → IRC (channel events)

## What's Needed

- [ ] LocalAI client integration (AICP has openai_client.py, fleet has separate)
- [ ] OpenRouter client (for free tier routing)
- [ ] Health checking via infrastructure clients
- [ ] Connection pooling / retry hardening
