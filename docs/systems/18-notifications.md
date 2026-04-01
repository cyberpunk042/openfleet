# Notifications — Multi-Channel Routing & Cross-References

> **3 files. 536 lines. Routes events to the right channel with the right priority.**
>
> When something happens in the fleet, the notification system decides
> WHO sees it, WHERE they see it, and HOW urgent it looks. IRC for
> real-time fleet awareness. ntfy for PO mobile alerts. Cross-references
> automatically link related items across surfaces so everything is
> connected and navigable. URL templates resolve project-specific links.

---

## 1. Why It Exists

Without notification routing:
- Every event goes to every channel at the same priority
- Task completion notification looks the same as a security alert
- PO gets spammed with info-level events on mobile
- Related items across surfaces aren't linked (PR merged but Plane
  issue doesn't know, task completed but IRC doesn't show the PR URL)

The notification system classifies, routes, deduplicates, and
cross-references — making fleet activity visible without noise.

### PO Requirement (Verbatim)

> "always cross reference, like when updating a task on Plane you can
> say it in the internal chat naturally"

---

## 2. How It Works

### 2.1 Notification Classification

```
Event arrives
  ↓
Classify by type:
  ├── task_done, pr_merged, sprint_milestone → INFO
  │   → ntfy progress topic (quiet, in history)
  │
  ├── review_needed, escalation → IMPORTANT
  │   → ntfy review topic (prominent notification)
  │
  └── security_alert, agent_stuck, blocker → URGENT
      → ntfy alert topic + Windows toast (immediate attention)
```

Three levels: INFO, IMPORTANT, URGENT. Each routes to different ntfy
topics with different notification behavior on PO's phone.

### 2.2 Deduplication

```
NotificationRouter(cooldown_seconds=300)

Same event type + same source within 5 minutes → suppressed
Prevents: agent heartbeating every 30s → 120 notifications/hour
```

### 2.3 Admonition Tags

Visual classification in ntfy:

| Event Type | Tags | Visual |
|-----------|------|--------|
| task_done | ✅ white_check_mark | Green check |
| pr_merged | 🚀 rocket | Rocket |
| review_needed | 👀 eyes, review | Eyes |
| escalation | 🚨 rotating_light | Red siren |
| security_alert | 🔒 lock, security | Lock |
| agent_stuck | ⚠️ warning, agent | Warning |
| blocker | 🚫 no_entry, blocker | Stop sign |
| digest | 📰 newspaper, daily | Newspaper |

### 2.4 Cross-References

When an event happens on one surface, auto-create references on others:

```
Task completed with PR
  → Plane issue gets: "PR merged: {url}"
  
Plane issue created
  → Board memory: "New Plane issue: {title} ({url})"
  
PR merged
  → OCMC task comment: "PR merged: {url}"
  
Agent @mentioned in Plane
  → IRC cross-post with link

Sprint started in Plane
  → IRC #sprint: announcement with link
```

### 2.5 URL Resolution

Config-driven URL templates (config/url-templates.yaml):

```
task_url: "http://localhost:8000/boards/{board_id}/tasks/{task_id}"
pr_url: "https://github.com/{org}/{repo}/pull/{pr_number}"
plane_issue_url: "https://plane.example.com/{workspace}/issues/{issue_id}"
irc_url: "http://localhost:9000/#/channel/{channel}"
```

`UrlResolver` fills templates with project-specific values.

---

## 3. File Map

```
fleet/core/
├── notification_router.py  Classify, route, deduplicate      (varies)
├── cross_refs.py           Auto-link across surfaces          (varies)
└── urls.py                 Config-driven URL templates         (varies)
```

Total: **536 lines** across 3 modules.

---

## 4. Per-File Documentation

### notification_router.py

| Class | Purpose |
|-------|---------|
| `NotificationLevel` | Enum: INFO, IMPORTANT, URGENT |
| `Notification` | title, message, level, event_type, source_agent, click_url, tags, dedup_key |
| `NotificationRouter` | Classify events → level. Route to ntfy topic. Cooldown-based dedup. |

### cross_refs.py

| Function | What It Does |
|----------|-------------|
| Auto-generates cross-references when events occur on any surface. Task→Plane, PR→Task, Sprint→IRC. |

### urls.py

| Class | Purpose |
|-------|---------|
| `UrlResolver` | Load URL templates from config. Fill with project/task/PR IDs. Resolve to full URLs. |

---

## 5. Consumers

| Layer | Module | How It Uses It |
|-------|--------|---------------|
| **Orchestrator** | `orchestrator.py` | NotificationRouter for wake notifications, health alerts |
| **MCP Tools** | `tools.py` | fleet_alert, fleet_escalate, fleet_notify_human route through notifications |
| **Event Bus** | `event_chain.py` | CHANNEL + NOTIFY surface events use notification routing |
| **Storm** | `storm_integration.py` | WARNING+ → IRC #alerts + ntfy PO |

---

## 6. Design Decisions

### Why 3 levels, not 5?

INFO/IMPORTANT/URGENT maps to ntfy's topic model. Each topic has
different notification behavior on PO's phone. More levels would
require more ntfy topics and more configuration. Three covers:
background awareness, active attention, and drop-everything urgency.

### Why cooldown-based dedup, not event-ID based?

Event-ID dedup would suppress exact duplicates but not similar events.
Cooldown-based (same type + source within 300s) catches the common
case: agent heartbeating repeatedly, storm indicators re-firing,
health checks re-detecting the same stuck task.

### Why auto cross-reference, not manual?

Manual cross-referencing is the first thing agents skip when
under pressure. Automated cross-refs ensure every PR links to its
task, every task completion appears on Plane, every sprint start
hits IRC — regardless of agent behavior.

---

## 7. IRC Channels

```
#fleet      — general fleet activity, task updates, sprint progress
#alerts     — critical alerts, security findings, storm warnings
#reviews    — PR reviews, approval notifications
#sprint     — sprint milestones, velocity updates
#gates      — PO gate requests (phase advancement)
#contributions — cross-agent contribution postings
```

The Lounge (web IRC client on localhost:9000) gives the PO
persistent visibility with link previews and search.

---

## 8. What's Needed

- The Lounge deployment (M92-96)
- IRC channel creation and configuration
- Cross-reference automation live test
- Daily digest generation (fleet-ops or governance agent)
- ntfy topic configuration per notification level

## 9. Test Coverage: **30+ tests**
