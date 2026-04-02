# fleet_chat

**Type:** MCP Tool
**System:** S08 (MCP Tools)
**Module:** fleet/mcp/tools.py
**Stage gating:** None — allowed in ALL stages

## Purpose

Post to the internal fleet chat system. Messages are stored in board memory with chat tags and mirrored to IRC #fleet. Supports @mentions to direct messages to specific agents — mentioned agents see the message in their next fleet_read_context call. @lead always reaches fleet-ops (board lead). @all broadcasts to everyone.

## Parameters

- `message` (string) — Your message to the team.
- `mention` (string, optional) — Agent to tag (e.g., "architect", "lead", "all").

## Chain Operations

```
fleet_chat(message, mention)
├── CONTEXT: ctx.agent_name (sender identity)
├── FORMAT: "[{agent}] @{mention} {message}"
├── TAGS: ["chat", "from:{agent}"]
│   ├── mention="all"  → tag "mention:all"
│   ├── mention="lead" → tag "mention:fleet-ops"
│   └── mention=name   → tag "mention:{name}"
├── mc.post_memory(board_id, content, tags, source)
│   └── Persisted in board memory for agent discovery
├── IRC: notify #fleet "[{agent}] @{mention} {message[:80]}"
└── RETURN: {ok, posted_by, mention}
```

## Who Uses It

| Role | When | Why |
|------|------|-----|
| ALL agents | Any time | Team communication |
| Engineer | During work | Ask architect for design guidance |
| PM | Sprint coordination | Coordinate task assignments |
| QA | After review | Share test findings |
| Fleet-ops | Heartbeat | Broadcast decisions or directives |
| Idle agents | Between tasks | Request new work assignments |

## Relationships

- READS FROM: ctx.agent_name (sender identity)
- STORES: board memory with chat + mention tags
- DISCOVERED BY: fleet_read_context (chat_messages field filters by @mention)
- IRC: mirrors to #fleet channel (truncated to 80 chars)
- CONNECTS TO: fleet_request_input (structured version for specific role requests)
- CONNECTS TO: fleet_escalate (when chat needs human attention)
- MENTION ROUTING: "lead" resolves to fleet-ops, "all" broadcasts to everyone
- EVENTS: none emitted (communication layer, not workflow)
