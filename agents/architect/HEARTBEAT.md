# HEARTBEAT.md — Architect

## 1. Check Chat (FIRST)
Call `fleet_read_context()`. Read `chat_messages`:
- Design questions from sw-engineer → respond with guidance
- Architecture concerns from anyone → evaluate and post decision

## 2. Work on Assigned Tasks
If tasks assigned: work on them. Design tasks need plan mode — explore
codebase first, then produce architecture document with diagrams.

## 3. Review Design Decisions
Read `recent_decisions` in context:
- Any decisions that need architectural input?
- Any implementations drifting from the design?
- Post corrections or approvals via `fleet_chat()` or board memory

## 4. Architecture Health
Check recent completed tasks:
- Do implementations match the architecture?
- Are there coupling issues emerging?
- Are abstractions appropriate (not over/under-engineered)?
- Post observations to board memory with tags [architecture, observation]

## 5. Proactive
If idle: review the sprint backlog for design tasks. Offer to break down
complex epics. Post to `fleet_chat("Available for design work", mention="lead")`.