# System 6: Agent Lifecycle

**Source:** `fleet/core/agent_lifecycle.py` (100+ lines), `fleet/core/agent_roles.py`
**Status:** 🔨 Data structures exist, content-aware transitions implemented, brain evaluation NOT implemented
**Design docs:** `fleet-elevation/23`

---

## Purpose

Manages agent state transitions: ACTIVE → IDLE → DROWSY → SLEEPING → OFFLINE. Content-aware: agents that report HEARTBEAT_OK 2-3 times transition to DROWSY/SLEEPING. The brain can then evaluate deterministically (free) instead of making Claude calls.

## Key Concepts

### States (agent_lifecycle.py:22-41)

```
ACTIVE  — Working on task. Full sessions. Cost: normal.
IDLE    — No work. Still real heartbeats. Cost: reduced.
DROWSY  — 2-3 HEARTBEAT_OK. Brain can evaluate. Cost: minimal.
SLEEPING — Brain evaluates (free). Zero Claude calls. Cost: $0.
OFFLINE — Extended absence. Slow wake. Cost: $0.
```

### Transition Thresholds (agent_lifecycle.py:44-51)

**Content-aware (priority):**
- DROWSY after 2 consecutive HEARTBEAT_OK
- SLEEPING after 3 consecutive HEARTBEAT_OK

**Time-based (fallback):**
- IDLE after 10min without work
- SLEEPING after 30min idle
- OFFLINE after 4h sleeping

### Heartbeat Intervals (agent_lifecycle.py:54-61)

- ACTIVE: 0 (agent drives own work)
- IDLE: 30min
- DROWSY: 60min
- SLEEPING: 2h
- OFFLINE: 2h

### AgentState Fields (agent_lifecycle.py:64-77)

```python
name, status, last_active_at, last_heartbeat_at,
last_task_completed_at, current_task_id,
consecutive_heartbeat_ok,  # content-aware counter
last_heartbeat_data_hash   # detect if context changed
```

### PO Requirement (fleet-elevation/23, Verbatim)

> "the agent need to be able to do silent heartbeat when they deem after a while that there is nothing new from the heartbeat, (2-3..) then it relay the work to the brain"

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Orchestrator** | Updates lifecycle states each cycle | Orchestrator → Lifecycle |
| **Effort Profiles** | Heartbeat intervals per status | Profiles → Lifecycle |
| **Budget** | Budget pressure → more agents sleeping | Budget → Lifecycle |
| **Storm** | Storm can force agents sleeping | Storm → Lifecycle |
| **Doctor** | Pruned agents → regrow fresh | Doctor → Lifecycle |
| **Gateway** | Gateway fires heartbeats at configured intervals | Gateway → Lifecycle |

## What's Needed

- [ ] Brain-evaluated heartbeats (DROWSY/SLEEPING agents get deterministic eval, not Claude call)
- [ ] Wake triggers per role (what would make each agent care — fleet-elevation/23)
- [ ] Strategic Claude call matrix (model/effort/session per situation)
- [ ] Cost tracking per lifecycle state
