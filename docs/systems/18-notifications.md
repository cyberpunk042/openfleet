# System 18: Notifications

**Source:** `fleet/core/notification_router.py`, `fleet/core/cross_refs.py`, `fleet/core/urls.py`
**Status:** 🔨 Routing logic exists. IRC/ntfy clients work. Cross-refs designed.
**Design docs:** `observability-and-channels.md` (M53-56), `phase-f3-irc-the-lounge.md` (M92-96)

---

## Purpose

Route events to the right channel with the right priority. IRC for real-time fleet awareness. ntfy for PO mobile alerts. Cross-references link related items across surfaces automatically.

## Key Concepts

### Notification Routing (notification_router.py)

3 levels:
- `INFO` — ntfy progress topic only (quiet, in history)
- `IMPORTANT` — ntfy review topic (prominent)
- `URGENT` — ntfy alert topic + Windows toast (immediate)

Admonition tags for visual classification: ✅ task_done, 🚀 pr_merged, 👀 review_needed, 🚨 escalation, 🔒 security_alert, ⚠️ agent_stuck, etc.

Deduplication with cooldown prevents spam.

### Cross-References (cross_refs.py)

When event on one surface → auto-create reference on others:
- Task completed with PR → Plane issue gets PR link
- Plane issue created → OCMC board memory notes it
- PR merged → OCMC task comment links to merged PR
- Agent @mentioned in Plane → IRC cross-post with link

PO requirement: "always cross reference"

### URL Builder (urls.py)

Config-driven URL resolution for GitHub, MC, Plane, IRC. Templates filled with project, task, PR, issue IDs.

### IRC Channels (from design docs)

3 channels:
- `#fleet` — general fleet activity
- `#alerts` — critical alerts, security findings
- `#reviews` — PR reviews, approval notifications

The Lounge (web IRC client) for human visibility.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Events** | Events route to notifications | Events → Notifications |
| **MCP Tools** | fleet_alert, fleet_escalate, fleet_notify_human | MCP → Notifications |
| **Storm** | WARNING+ → IRC #alerts, STORM+ → ntfy | Storm → Notifications |
| **Orchestrator** | Wake notifications, health alerts | Orchestrator → Notifications |

## What's Needed

- [ ] The Lounge deployment (M92-96)
- [ ] IRC channel setup (#fleet, #alerts, #reviews)
- [ ] Cross-reference automation live test
- [ ] Daily digest generation (fleet-ops responsibility)
