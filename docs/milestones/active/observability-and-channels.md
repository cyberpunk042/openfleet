# Workstream 3: Observability & Channels

## Goal

The human leader can SEE agent conversations in real-time, not just task results.
Multiple observation surfaces: MC dashboard, OpenClaw Control UI, and a persistent
external channel (IRC/Discord) for continuous visibility.

## What Exists

### Mission Control (Task-Level)
- **Board memory chat**: `make chat MSG="..."` → agents see it
- **Task comments**: agents post progress, visible in MC dashboard
- **Activity events**: audit trail of all actions
- **SSE streams**: real-time feeds (approvals, memory, comments)
- **Dashboard**: http://localhost:3000

### OpenClaw Control UI (Session-Level)
- **Web UI**: http://localhost:18789 (built-in, served by gateway)
- **WebSocket chat**: real-time agent conversations in browser
- **Session list**: see all agent sessions
- **Live streaming**: watch agent thinking, tool calls, responses as they happen

### OpenClaw Gateway Events (Programmatic)
- **WebSocket subscriptions**: `sessions.subscribe`, `sessions.messages.subscribe`
- **Agent events**: `agent.event` (start, tool use, thinking, completion)
- **Broadcast to connected clients**: any WS client can subscribe
- **Drop-if-slow**: backpressure handling for slow clients

### OpenClaw Channels (External Messaging)
- **13 built-in**: Discord, Slack, Telegram, IRC, Signal, iMessage, LINE, etc.
- **Plugin-based**: each channel is a loadable plugin with adapters
- **Bidirectional**: inbound (external → agent) + outbound (agent → external)
- **Session routing**: messages route to agent sessions via channel/peer bindings

## Key Distinction

| Surface | What You See | Persistence | Real-time |
|---------|-------------|-------------|-----------|
| MC Dashboard | Task status, comments, activity | Yes (DB) | SSE polling |
| MC Board Memory | Human↔agent chat | Yes (DB) | SSE polling |
| OpenClaw Control UI | Full agent conversations | Session files | WebSocket |
| OpenClaw Channel | Agent messages on external platform | Platform-dependent | Platform-native |

**MC** = task orchestration and results.
**Control UI** = live agent session observation.
**Channels** = persistent external messaging surface.

## What's Needed

### M53: OpenClaw Control UI Setup

**Scope:** Make the Control UI accessible and useful for fleet observation.

**Tasks:**
1. Document how to access the Control UI (http://localhost:18789)
2. Verify all MC-provisioned agent sessions are visible in the UI
3. Test: dispatch a task, watch the agent work in real-time in Control UI
4. Document the UI features: session list, chat, agent switching
5. Add `make control-ui` target that opens the URL

**Why first:** This is FREE — already running, just needs documentation. Gives
immediate real-time visibility into agent work with zero setup.

### M54: WebSocket Event Monitor

**Scope:** CLI tool to monitor gateway events in real-time.

**Tasks:**
1. Create `scripts/ws-monitor.sh` (Python WS client):
   - Connect to gateway, subscribe to `sessions.subscribe`
   - Print agent events as they happen (tool calls, responses, errors)
   - Filter by agent name or session key
2. Add `make watch` target: `make watch` or `make watch AGENT=architect`
3. This gives terminal-based real-time observation without a browser

### M55: Channel Setup for Persistent Observation

**Scope:** Set up an external channel so agent conversations persist outside MC/OpenClaw.

**Options evaluated:**

**Option A: Discord**
- Pro: Rich UI, threads, reactions, mobile app, team visibility
- Pro: Built-in OpenClaw channel, well-supported
- Con: Requires Discord bot token + server
- Con: External service dependency

**Option B: IRC (local)**
- Pro: Fully local, no external dependency
- Pro: Built-in OpenClaw channel
- Con: Needs local IRC daemon (miniircd or similar)
- Con: Limited UI compared to Discord

**Option C: Slack**
- Pro: Professional, team-friendly
- Con: Requires Slack workspace + app
- Con: API rate limits

**Recommendation:** Start with **Discord** for team/external visibility (if the user
has a Discord server), or **IRC** for fully local operation. Both are built-in.

**Tasks (for chosen channel):**
1. Configure channel in `~/.openclaw/openclaw.json`:
   ```json
   "channels": {
     "<channel>": {
       "accounts": [{
         "id": "fleet",
         // channel-specific config
       }]
     }
   }
   ```
2. Set up agent routing bindings:
   `openclaw agents bind <agent> --channel <channel> --target <channel-target>`
3. Script: `scripts/configure-channel.sh <discord|irc>` — non-interactive setup
4. Add to setup.sh as optional step
5. Test: dispatch task → see conversation in external channel

### M56: Unified Observation Dashboard

**Scope:** Single view that combines MC tasks + OpenClaw sessions + channel activity.

**Tasks:**
1. Create `scripts/dashboard.sh` — combines:
   - Fleet status (agents, tasks)
   - Active agent sessions (from gateway WS)
   - Recent channel messages (if channel configured)
   - Board memory chat entries
2. Or: build a simple web page that embeds MC + Control UI in iframes
3. Add `make dashboard` target

**This is lower priority** — individual surfaces work first.

## What We DON'T Need to Build

- Custom channel plugin (OpenClaw has 13 built-in)
- Custom WebSocket server (gateway already has subscriptions)
- Custom dashboard framework (MC + Control UI already exist)

## Verification

- [ ] Control UI shows agent sessions and conversations
- [ ] `make watch` streams agent events in terminal
- [ ] External channel configured and receiving agent messages
- [ ] Human can send message in channel → agent receives it
- [ ] `make dashboard` or equivalent shows unified view