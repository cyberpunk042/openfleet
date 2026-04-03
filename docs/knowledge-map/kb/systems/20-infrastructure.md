# System 20: Infrastructure — Client Libraries & IaC

**Type:** Fleet System
**ID:** S20
**Files:** 8 infra clients + IaC scripts
**Total:** ~1,908 lines
**Tests:** 30+

## What This System Does

Every external service accessed through typed clients — never raw HTTP. Centralizes auth, error handling, caching, protocol. 8 clients wrap: gateway (WebSocket JSON-RPC), MC (REST + SQLite cache), Plane (REST), IRC (gateway WebSocket), ntfy (HTTP push), GitHub (gh CLI), config (YAML loader), cache (SQLite TTL).

IaC scripts automate all setup via Makefile targets.

## 8 Clients

| Client | Protocol | What It Wraps |
|--------|----------|--------------|
| gateway_client.py | WebSocket JSON-RPC (ws://localhost:18789) | Prune/compact/inject sessions, enable/disable CRONs, update CRON tempo |
| mc_client.py | REST (http://localhost:8000) | CRUD tasks/agents/memory/approvals/comments. SQLite response cache. |
| plane_client.py | REST (Plane API) | Issues/labels/states/comments/sprints/modules |
| irc_client.py | IRC via gateway WebSocket | notify_event, post_message to channels |
| ntfy_client.py | HTTP push | Publish with title/message/priority/topic/tags/emoji |
| gh_client.py | gh CLI subprocess | create_pr, push_branch, get_pr_status, get_diff |
| config_loader.py | YAML files | fleet.yaml, phases.yaml, agent-identities.yaml, agent-tooling.yaml |
| cache_sqlite.py | SQLite with TTL | Key-value cache for MC API responses |

## IaC Scripts

provision-agents.sh, setup-agent-tools.sh, install-plugins.sh, generate-tools-md.sh, generate-agents-md.sh, validate-agents.sh, deploy-skills.sh + optimize-models.sh, configure-board.sh, setup-mc.sh.

Makefile targets: make setup, make provision, make setup-tools, make validate-agents, make generate-tools, make generate-agents, make install-plugins.

## Ecosystem Gap

Researched but not deployed: prompt caching (90% savings), Claude-Mem (45K stars), 1000+ MCP servers, 5400+ skills, Agent Teams, Batch API (50%). Deployed: codex plugin, statusline, KV cache, .claudeignore, Docker /data persistence, function calling grammar.

## Relationships

- CONSUMED BY: every system that calls external services
- CONNECTS TO: ALL systems (infrastructure is the foundation)
- CONNECTS TO: gateway (WebSocket RPC for session management)
- CONNECTS TO: MC (REST for task/agent/memory CRUD)
- CONNECTS TO: Plane (REST for issue/sprint management)
- CONNECTS TO: IRC (notifications via miniircd)
- CONNECTS TO: ntfy (push notifications to PO)
- CONNECTS TO: GitHub (PR/branch management via gh CLI)
