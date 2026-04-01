# System 8: MCP Tools

**Source:** `fleet/mcp/tools.py` (2200+ lines), `fleet/mcp/server.py`, `fleet/mcp/context.py`
**Status:** 🔨 25 tools registered, stage gating implemented. Not all chains complete.
**Design docs:** `fleet-elevation/24`, `agents/_template/MC_WORKFLOW.md`

---

## Purpose

The 25 MCP tools are what agents can DO. Each tool handles infrastructure automatically — the agent provides semantic input, the tool does the rest. Event chains propagate across surfaces. Stage gating prevents work tools outside work stage.

## All 25 Tools (tools.py)

### Task Operations
| Tool | Purpose | Stage Gate |
|------|---------|-----------|
| `fleet_read_context` | Load task + project + board memory | Any |
| `fleet_task_accept` | Accept task with plan | Any |
| `fleet_task_progress` | Report progress | Any |
| `fleet_commit` | Git commit (conventional format) | **WORK only** |
| `fleet_task_complete` | Complete → push → PR → review → approval | **WORK only** |
| `fleet_task_create` | Create task/subtask | Any |

### Communication
| Tool | Purpose | Chain |
|------|---------|-------|
| `fleet_chat` | Post to board memory | → @mention routing → IRC |
| `fleet_alert` | Post alert | → board memory → IRC #alerts → ntfy |
| `fleet_escalate` | Escalate to PO | → board memory → ntfy PO → IRC #alerts |
| `fleet_notify_human` | Direct notification | → ntfy with priority |
| `fleet_pause` | Report blocker | → board memory → IRC |

### Review
| Tool | Purpose | Chain |
|------|---------|-------|
| `fleet_approve` | Approve/reject task | → status → event → IRC → agent notified |

### Fleet Awareness
| Tool | Purpose |
|------|---------|
| `fleet_agent_status` | Check agent statuses |
| `fleet_task_context` | Get assembled task context |
| `fleet_heartbeat_context` | Get assembled heartbeat context |

### Plane Integration
| Tool | Purpose |
|------|---------|
| `fleet_plane_status` | Check Plane project status |
| `fleet_plane_sprint` | Get current sprint |
| `fleet_plane_sync` | Sync OCMC ↔ Plane |
| `fleet_plane_create_issue` | Create Plane issue |
| `fleet_plane_comment` | Comment on Plane issue |
| `fleet_plane_update_issue` | Update Plane issue |
| `fleet_plane_list_modules` | List Plane modules |

### Artifact Management
| Tool | Purpose | Chain |
|------|---------|-------|
| `fleet_artifact_create` | Create structured artifact | → Plane HTML (transpose) → completeness |
| `fleet_artifact_update` | Update artifact field | → Plane HTML → completeness → readiness |
| `fleet_artifact_read` | Read artifact from Plane | ← Plane HTML (reverse transpose) |

## Stage Gating (tools.py:130-171)

```python
WORK_ONLY_TOOLS = {"fleet_commit", "fleet_task_complete"}
```

`_check_stage_allowed()` returns error + emits `fleet.methodology.protocol_violation` event if work tools called outside work stage. This IS enforcement — the tool call fails.

## Review Gates (tools.py:21-60)

`_build_review_gates()` creates reviewer requirements per task type:
- Code tasks → QA required
- Epic/story → Architect required
- Security/blocker → DevSecOps required
- Fleet-ops always final gate

## Tools NOT Yet Implemented (from design docs)

- `fleet_contribute` — post contribution to another agent's task
- `fleet_request_input` — request missing contribution from PM
- `fleet_gate_request` — request PO gate approval

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Methodology** | Stage gating enforces protocol | Methodology → MCP |
| **Events** | Every tool emits event chains | MCP → Events |
| **Transpose** | Artifact tools use transpose for HTML | MCP → Transpose |
| **Standards** | Artifact completeness checked against standards | Standards → MCP |
| **Plane** | 7 Plane tools talk to Plane API | MCP → Plane |
| **Notifications** | Alert/escalate tools route to IRC/ntfy | MCP → Notifications |
| **Context Assembly** | Context tools use assembly functions | Context → MCP |
| **Skill Enforcement** | Required tools tracked per task type | Enforcement → MCP |

## What's Needed

- [ ] `fleet_contribute` tool (CRITICAL — blocks contribution flow)
- [ ] `fleet_request_input` tool
- [ ] Complete event chains for all tools
- [ ] Artifact tool integration with transpose layer
