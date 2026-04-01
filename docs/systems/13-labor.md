# System 13: Labor Attribution

**Source:** `fleet/core/labor_stamp.py`, `fleet/core/labor_analytics.py`, `fleet/core/heartbeat_stamp.py`
**Status:** 🔨 Unit tests. Stamp assembly exists. Not integrated with real agent completions.
**Design docs:** `labor-attribution-and-provenance.md` (M-LA01-08)

---

## Purpose

Every fleet artifact carries a labor stamp: who produced it, what model, what backend, what effort, what skills, what confidence tier, what cost. Trainee/community tier work gets extra review automatically. Nothing is anonymous.

### PO Requirement (Verbatim)

> "the agents are going to explain the source of their labor, the model, the effort, the skills used"
> "the LocalAI work will also need to be flagged as trainee's work"

## Key Concepts

### LaborStamp (labor_stamp.py:47-87)

```python
# WHO
agent_name, agent_role

# WHAT PRODUCED IT
backend (claude-code, localai, openrouter, direct)
model (opus-4-6, sonnet-4-6, hermes-3b, qwen3-8b)
model_version, effort (low/medium/high/max)

# HOW
skills_used, tools_called, session_type (fresh/compact/continue)

# CONFIDENCE
confidence_tier (expert/standard/trainee/community/hybrid)
confidence_reason

# COST
duration_seconds, estimated_tokens, estimated_cost_usd

# EFFORT (from session telemetry W8)
lines_added, lines_removed, cache_read_tokens

# ITERATION
iteration, challenge_rounds_survived, challenge_types_faced
challenge_skipped, challenge_skip_reason (W2 wiring)

# CONTEXT
budget_mode, fallback_from, fallback_reason, timestamp
```

### Confidence Tier Derivation (labor_stamp.py:14-41)

Automatic from backend + model:
- claude-code + opus → `expert`
- claude-code + sonnet → `standard`
- localai + any → `trainee`
- openrouter-free + any → `community`
- mixed → `hybrid`

`requires_challenge` property: True for trainee, community, hybrid.

### Stamp Assembly (labor_stamp.py:187-228)

`assemble_stamp(dispatch, duration, tokens, tools, session_type, iteration)` — combines dispatch record + session metrics into full LaborStamp. Cost estimated from backend+model.

### Labor Analytics (labor_analytics.py)

AgentCostMetrics, ModelCostMetrics, TierCostMetrics. Per-agent approval rates, per-model costs, per-tier challenge pass rates. Cost by backend, cost by budget mode.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **MCP Tools** | fleet_task_complete assembles stamp | MCP → Stamps |
| **Challenge Engine** | Trainee/community tier triggers challenge | Stamps → Challenge |
| **Budget** | Budget mode recorded in stamp | Budget → Stamps |
| **Session Telemetry** | Real cost/duration from session data (W8) | Telemetry → Stamps |
| **Backend Router** | Routing decision recorded (model, backend, fallback) | Router → Stamps |
| **Events** | Labor events emitted on completion | Stamps → Events |
| **Templates** | Stamp rendered in PR body and task comments | Stamps → Templates |

## What's Needed

- [ ] Live test: real agent completion produces labor stamp
- [ ] Session telemetry feeding real values (not estimates)
- [ ] Stamp appearing in PR body and task comments
- [ ] Analytics dashboard (cost per agent, per model, per tier)
