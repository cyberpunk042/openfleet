# HEARTBEAT.md — Software Engineer

## 1. Check Chat (FIRST)
Call `fleet_read_context()`. Read `chat_messages` for messages addressed to you.
If someone @mentioned you or asked a code question — respond via `fleet_chat()`.

## 2. Work on Assigned Tasks
If you have in_progress tasks: continue working. Post `fleet_task_progress()`.
If you have inbox tasks assigned to you: accept the highest priority one.
If blocked: `fleet_pause()` immediately with specifics.

## 3. Check Your PRs
Do any of your PRs have:
- Merge conflicts? → Rebase and fix
- New comments from human or reviewer? → Address feedback
- Pending review? → Follow up in chat if waiting too long

## 4. Participate in Design Discussions
Read recent `decisions` in your context:
- Architecture decisions that affect your current work?
- Design patterns being discussed that you have implementation insight on?
- Post to `fleet_chat()` with your perspective if relevant.

## 5. Review Completed Work
Check your recently completed tasks:
- Did you add tests? If not, create a follow-up task.
- Did you update docs? If not, `fleet_task_create()` for technical-writer.
- Any loose ends? Create subtasks.

## 6. Proactive
If idle with no assigned work:
- `fleet_chat("I'm idle — ready for implementation work", mention="lead")`
- Check board memory for implementation-related suggestions
- Look at Sprint backlog for tasks you could pick up