# fleet_notify_human

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Send a notification to the human (PO) via ntfy push notification service. Supports three priority tiers that route to different ntfy topics with different notification behaviors. Used for sprint progress updates, review completions, alert summaries, and any event worth the human's attention. Lower friction than fleet_escalate — does not require the agent to stop working.

## Parameters

- `title` (string) — Short notification title.
- `message` (string) — Body text with context.
- `priority` (string, optional) — "info", "important", or "urgent". Default: "info".
- `url` (string, optional) — Click URL (task URL, PR URL) that opens when notification is clicked.
- `tags` (list[string], optional) — ntfy tags for classification (e.g., ["white_check_mark", "sprint"]).

## Chain Operations

```
fleet_notify_human(title, message, priority, url, tags)
├── CONTEXT: ctx.agent_name (sender identity)
├── TAG BUILD: append agent name to tags list
├── NTFY ROUTING by priority:
│   ├── "info"      → ntfy fleet-progress (quiet, in history)
│   ├── "important" → ntfy fleet-review (prominent notification)
│   └── "urgent"    → ntfy fleet-alert (persistent, sound, + Windows toast)
├── NtfyClient.publish(title="[{agent}] {title}", message, priority, tags, click_url)
└── RETURN: {ok, priority, channel: "ntfy"}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| PM | Sprint completion | Notify human of sprint progress |
| Fleet-ops | Review complete | Alert human that PR is ready for merge |
| Engineer | Task milestone | Share important progress |
| QA | Test suite results | Report test pass/fail summary |
| Any agent | Notable event | Human should be aware but no action needed |

## Relationships

- READS FROM: ctx.agent_name (sender identity)
- CALLS: NtfyClient from fleet/infra/ntfy_client.py
- CONNECTS TO: fleet_escalate (escalate is urgent + stops agent; notify_human is informational)
- CONNECTS TO: fleet_gate_request (gates use notification_router internally)
- PRIORITY ROUTING: info → fleet-progress, important → fleet-review, urgent → fleet-alert
- DOES NOT: post to board memory or IRC (ntfy only — use fleet_chat for IRC/memory)
- DOES NOT: require agent to stop working (informational, not blocking)
