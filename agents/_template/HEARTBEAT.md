# HEARTBEAT.md — Worker Agent

On each heartbeat, check for work, check chat, report status.

## Tasks

### 1. Check Internal Chat

Call `fleet_read_context()`. Check `chat_messages` for messages addressed to you.
If someone @mentioned you — respond via `fleet_chat()`.

### 2. Check Assignments

Call `fleet_agent_status()`. Look for tasks assigned to you in inbox status.
If you have assigned work: call `fleet_task_accept()` to start.

### 3. Report Status

If you have an in_progress task:
- Post a progress update via `fleet_task_progress()`
- If blocked: use `fleet_pause()` to escalate

If idle with no work:
- Use `fleet_chat("I'm idle, ready for work", mention="lead")` to request assignment
- Then HEARTBEAT_OK

## Rules

- Check chat FIRST — someone may be waiting for your response
- Accept and start tasks promptly when assigned
- If stuck, pause immediately — don't spin
- HEARTBEAT_OK means no work and no chat messages pending