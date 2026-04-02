# fleet_alert

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Raise an alert for security, quality, architecture, workflow, or tooling concerns. Posts a formatted alert to board memory with severity tags, and routes IRC notification to the appropriate channel based on severity. Alerts are discoverable by all agents via fleet_read_context (active_alerts field).

## Parameters

- `severity` (string) — "critical", "high", "medium", or "low".
- `title` (string) — Short alert title.
- `details` (string) — Detailed description with evidence.
- `category` (string, optional) — "security", "quality", "architecture", "workflow", "tooling". Default: "quality".

## Chain Operations

```
fleet_alert(severity, title, details, category)
├── CONTEXT: ctx.agent_name (alert source)
├── memory_tmpl.format_alert(severity, title, details, category, agent)
├── memory_tmpl.alert_tags(severity, category, project)
│   └── Tags: ["alert", severity, category, "project:{name}"]
├── mc.post_memory(board_id, content, tags, source)
│   └── Persisted for agent discovery in active_alerts
├── IRC ROUTING: irc_tmpl.route_channel(severity)
│   ├── critical/high → #alerts channel
│   └── medium/low → #fleet channel
├── irc.notify(channel, formatted alert message)
└── RETURN: {ok, severity, channel}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| DevSecOps | Security scan | Report vulnerabilities |
| QA | Test failure | Report quality regressions |
| Architect | Design review | Flag architecture violations |
| Engineer | During work | Report unexpected issues |
| Fleet-ops | Heartbeat | Escalate systemic problems |

## Relationships

- READS FROM: ctx.agent_name (alert source identity)
- STORES: board memory with alert + severity + category tags
- DISCOVERED BY: fleet_read_context (active_alerts field)
- IRC: routed by severity — critical/high to #alerts, medium/low to #fleet
- CONNECTS TO: memory_tmpl.format_alert, memory_tmpl.alert_tags (formatting)
- CONNECTS TO: irc_tmpl.route_channel (severity-based channel routing)
- CONNECTS TO: fleet_escalate (alerts that need human decision become escalations)
- CONNECTS TO: fleet_pause (alerts that block work lead to pausing)
- FEEDS: doctor system (protocol_violation alerts trigger intervention)
