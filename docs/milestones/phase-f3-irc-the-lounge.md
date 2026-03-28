# Phase F3: IRC + The Lounge — Human's Window into the Fleet

> "we are also going to need to explore the lounge repo and site (https://thelounge.chat/) and see how to setup this so I can talk with the publish AI messages and where we would for instance warn me about important CVE or security issue in general or bug or suggestion or fix or blocking or issue and so on..."

> "all the logic that is needed and that the Agent would need to logically use and we would probably need one agent that will keep order in all this and offer feature like backup of the IRC and stuff like this revolving around its SRP evolutions."

## Problem Statement

The human currently has no persistent, rich, real-time interface to the fleet.
MC dashboard is async and requires clicking through tasks. The WS monitor is a
raw terminal tool. There's no place where the human can SEE everything happening,
GET ALERTED about important things, and INTERACT with agents naturally.

IRC is connected (miniircd + fleet-bot) but the human needs a web client to
actually use it. CLI IRC clients (irssi/weechat) are not the answer for a
modern workflow.

## Design Principle

**The Lounge is the human's command center.** Open a browser tab, see everything.

## Research: The Lounge

Source: https://thelounge.chat/ | https://github.com/thelounge/thelounge

### What it is
- Modern web-based IRC client
- Self-hosted, runs as a Node.js server
- Persistent connections (stays connected when browser closes)
- Mobile-responsive
- File upload support
- Link previews (URLs show previews inline)
- Search across history
- Multiple channel support with notifications
- User management (multiple users can connect)
- Themes and customization

### Install options
1. **npm**: `npm install -g thelounge` → `thelounge start`
2. **Docker**: `docker run -d -p 9000:9000 thelounge/thelounge`
3. **Debian/Ubuntu**: apt package available

### Configuration
- Default port: 9000
- Config at `~/.thelounge/config.js` or `/etc/thelounge/config.js`
- Pre-configure networks (IRC servers) so the human doesn't have to
- Pre-configure channels (#fleet, #alerts, #reviews)
- Can set password protection for the web UI

### Why The Lounge and not raw IRC client
- **Link previews**: when agents post GitHub URLs, the human sees PR titles inline
- **Persistent**: stays connected even when browser is closed
- **Search**: find past messages about a specific task or project
- **Mobile**: check fleet status from phone
- **Modern**: not a terminal from 1995

## Architecture

### Components

```
Human (browser)
    ↓ http://localhost:9000
The Lounge (web IRC client)
    ↓ IRC protocol
miniircd (local IRC server, port 6667)
    ↑ IRC protocol
OpenClaw Gateway (fleet-bot)
    ↑ send RPC
Fleet scripts (notify-irc.sh)
    ↑ called by
dispatch-task.sh, fleet-sync.sh, create-task.sh, agents
```

### Channels

| Channel | Purpose | Who posts | Who reads |
|---------|---------|-----------|-----------|
| #fleet | General fleet activity — task events, agent status, human interaction | All agents, fleet scripts | Human (primary) |
| #alerts | Security, critical issues, blockers — high-priority only | Agents (alert skill) | Human (notifications on) |
| #reviews | PR ready, review results, merge events | Agents (PR skill), fleet-sync | Human (when reviewing) |

**Why multiple channels:**
- #fleet would get noisy with everything — alerts get buried
- #alerts has notifications ALWAYS ON — critical things never missed
- #reviews is the human's PR review queue — check it when reviewing

### Human → Agent Interaction via IRC

The human types in #fleet:
```
<human> @architect what's the status of the NNRT architecture?
```

**How agents see this:**
- OpenClaw gateway monitors #fleet for messages
- Messages from non-bot users are routed to the appropriate agent session
- If @mentioned, routes to that specific agent
- If not @mentioned, routes to the lead agent
- Agent responds in #fleet

**This requires:**
- IRC channel monitoring in OpenClaw (already built into the IRC channel plugin)
- Agent routing bindings (bind agents to IRC channel/account)
- Agents configured to respond to IRC messages

This is a CORE feature of OpenClaw's channel system — we're using it as designed.

## Milestones

### M92: Research and Validate The Lounge

**Tasks:**
1. Install The Lounge locally (Docker or npm)
2. Verify it connects to miniircd on localhost:6667
3. Verify it can join #fleet and see messages from fleet-bot
4. Verify link previews work for GitHub URLs
5. Verify search works across channel history
6. Document the setup for the fleet

**Output:** Working The Lounge instance with validated features.

### M93: Script The Lounge Installation in setup.sh

**Tasks:**
1. Add The Lounge to setup.sh (Docker preferred for isolation)
2. Pre-configure: connect to localhost:6667, join #fleet, #alerts, #reviews
3. Create a default user (fleet-admin or similar)
4. Make idempotent (don't recreate if already running)
5. Add to Makefile: `lounge-up`, `lounge-down`, `lounge-open`
6. Add to docker-compose.yaml if Docker approach

**The Lounge config template:**
```javascript
module.exports = {
    public: false,          // require login
    port: 9000,
    reverseProxy: false,
    defaults: {
        name: "Fleet IRC",
        host: "host.docker.internal",  // or localhost if not Docker
        port: 6667,
        tls: false,
        channels: "#fleet,#alerts,#reviews",
        nick: "human",
    },
};
```

### M94: Multiple IRC Channels Setup

**Tasks:**
1. Configure miniircd to support multiple channels (it does by default)
2. Configure fleet-bot to join #fleet, #alerts, #reviews
3. Update notify-irc.sh to accept --channel parameter
4. Fleet scripts route messages to the right channel:
   - Task events → #fleet
   - Alerts → #alerts
   - PR events → #reviews
5. Update agent skills to post to the right channel based on message type

### M95: Agent IRC Message Format Standard

**Tasks:**
1. Define the exact format for each event type (already drafted in M82 templates)
2. Implement in fleet-irc skill
3. Ensure all URLs are full and clickable
4. Ensure The Lounge renders link previews for GitHub/MC URLs
5. Test with real events — does the output look good in The Lounge?

### M96: IRC Operations Agent

> "one agent that will keep order in all this and offer feature like backup of the IRC"

**This agent's SRP:** IRC channel operations and fleet communication health.

**Responsibilities:**
- IRC log backup (periodic export of channel history)
- Channel health monitoring (is fleet-bot connected? are messages flowing?)
- Message cleanup (remove noise, pin important messages if IRC supports it)
- Daily digest: summarize day's activity in #fleet
- Weekly report: summarize week's fleet output
- Notification routing: ensure alerts reach #alerts, PRs reach #reviews
- IRC configuration management: channel topics, modes

**Note:** This could be a role of the governance agent rather than a separate agent.
The user said "SRP evolutions" — so it starts as a responsibility and may evolve
into its own agent if the scope grows.

## Open Questions for Discussion

1. **Docker vs npm for The Lounge?** Docker is isolated but adds to docker-compose.
   npm is simpler but requires Node.js (already installed for OpenClaw).

2. **Authentication for The Lounge?** Password-protect the web UI or leave open
   (localhost only)?

3. **Should agents respond in IRC directly?** Or should IRC→agent flow through
   MC board memory? Direct is more fluid. Board memory is more traceable.
   Could do both: agent responds in IRC AND posts to board memory.

4. **IRC log persistence:** miniircd doesn't persist logs. Options:
   - The Lounge persists its own log (client-side)
   - Fleet agent periodically exports logs
   - Replace miniircd with a logging-capable IRCd (like ergochat)
   - Or just rely on The Lounge's built-in log persistence

5. **Scale:** If the fleet grows to 20+ agents, will #fleet get too noisy?
   May need per-project channels eventually: #nnrt, #aicp, #fleet-ops

## Verification

- [ ] The Lounge accessible at http://localhost:9000
- [ ] Pre-connected to miniircd with #fleet, #alerts, #reviews
- [ ] Fleet-bot messages visible in The Lounge
- [ ] GitHub URL previews render in The Lounge
- [ ] Human can type in #fleet and an agent responds
- [ ] Alerts appear in #alerts with notifications
- [ ] PR events appear in #reviews
- [ ] IRC logs persist across The Lounge restarts
- [ ] All installed and configured by setup.sh (no manual steps)