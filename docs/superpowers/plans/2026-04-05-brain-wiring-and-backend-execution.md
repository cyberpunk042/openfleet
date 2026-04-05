# Brain Wiring & Backend Execution — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing heartbeat brain evaluator into the orchestrator, gate heartbeats via OpenArms before_dispatch hook, connect backend routing to actual execution, and add OpenRouter models.

**Architecture:** Orchestrator (Python) evaluates agents every cycle and writes `.brain-decision.json` per workspace. OpenArms `before_dispatch` hook reads these files and gates Claude calls. Backend routing decisions drive actual dispatch to LocalAI/OpenRouter/Claude.

**Tech Stack:** Python 3.11+ (orchestrator), TypeScript (OpenArms plugin), httpx (API clients)

**Spec:** `docs/superpowers/specs/2026-04-05-brain-wiring-and-backend-execution.md`

---

## File Structure

**Create:**
- `fleet/core/brain_writer.py` — writes brain decisions to agent workspaces
- `extensions/fleet-heartbeat-gate/openarms.plugin.json` — OpenArms plugin manifest
- `extensions/fleet-heartbeat-gate/index.ts` — before_dispatch hook implementation

**Modify:**
- `fleet/cli/orchestrator.py` — add brain evaluation step
- `fleet/infra/mc_client.py` — add `post_board_memory()` method
- `fleet/core/backend_router.py` — add OpenRouter Qwen3.6 Plus model
- `fleet/cli/dispatch.py` — wire routing decision to actual backend execution
- `gateway/executor.py` — support non-Claude execution paths

---

### Task 1: Brain Decision Writer

Write the module that evaluates agents and writes decision files to their workspaces.

**Files:**
- Create: `fleet/core/brain_writer.py`

- [ ] **Step 1: Create brain_writer.py**

```python
"""Brain decision writer — evaluates agents and writes .brain-decision.json.

The orchestrator calls write_brain_decisions() every cycle. For each agent
where brain_evaluates is True, it runs the heartbeat gate and writes the
decision to the agent's workspace. The OpenArms before_dispatch hook
reads these files to gate Claude calls.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fleet.core.agent_lifecycle import AgentState, FleetLifecycle
from fleet.core.heartbeat_gate import (
    HeartbeatDecision,
    HeartbeatEvaluation,
    evaluate_agent_heartbeat,
)

logger = logging.getLogger(__name__)

DECISION_FILENAME = ".brain-decision.json"


def write_brain_decisions(
    lifecycle: FleetLifecycle,
    now: datetime,
    tasks: list,
    agents: list,
    board_memory: list,
    fleet_dir: str,
) -> dict[str, HeartbeatEvaluation]:
    """Evaluate all agents needing heartbeat and write decision files.

    Returns dict of agent_name → HeartbeatEvaluation for reporting.
    """
    results: dict[str, HeartbeatEvaluation] = {}

    for agent_state in lifecycle.agents_needing_heartbeat(now):
        if not agent_state.brain_evaluates:
            continue

        # Build inputs for the brain evaluator
        agent_name = agent_state.name
        agent_role = agent_name  # role matches name in our fleet

        # Mentions: board memory entries that mention this agent
        mentions = [
            m for m in board_memory
            if f"@{agent_name}" in str(m.get("content", ""))
        ]

        # Assigned tasks for this agent
        assigned = [
            t for t in tasks
            if (t.custom_fields.agent_name if hasattr(t, 'custom_fields') and t.custom_fields else t.get("agent_name", "")) == agent_name
        ]

        # Directives targeted at this agent
        directives = [
            m for m in board_memory
            if "directive" in str(m.get("tags", []))
            and agent_name in str(m.get("content", ""))
        ]

        # Contributions pending
        contributions = [
            t for t in tasks
            if (t.custom_fields.contribution_target if hasattr(t, 'custom_fields') and t.custom_fields else t.get("contribution_target", "")) == agent_name
            and (t.status if hasattr(t, 'status') else t.get("status", "")) == "inbox"
        ]

        # Events since last heartbeat (simplified — use all recent events)
        events = []

        evaluation = evaluate_agent_heartbeat(
            agent_name=agent_name,
            agent_role=agent_role,
            mentions=mentions,
            assigned_tasks=assigned,
            directives=directives,
            contributions_pending=contributions,
            events_since_last=events,
            consecutive_heartbeat_ok=agent_state.consecutive_heartbeat_ok,
        )

        # Write decision file to agent workspace
        _write_decision(fleet_dir, agents, agent_name, evaluation)
        results[agent_name] = evaluation

        # Update lifecycle state
        if evaluation.decision == HeartbeatDecision.SILENT:
            agent_state.record_heartbeat_ok()
        else:
            agent_state.mark_heartbeat_sent(now)

    return results


def _write_decision(
    fleet_dir: str,
    agents: list,
    agent_name: str,
    evaluation: HeartbeatEvaluation,
) -> None:
    """Write .brain-decision.json to agent's workspace."""
    # Find workspace for this agent
    workspace = None
    for a in agents:
        name = a.name if hasattr(a, 'name') else a.get("name", "")
        if name == agent_name:
            # Workspace is workspace-mc-{agent.id}
            agent_id = a.id if hasattr(a, 'id') else a.get("id", "")
            workspace = os.path.join(fleet_dir, f"workspace-mc-{agent_id}")
            break

    if not workspace or not os.path.isdir(workspace):
        logger.warning("No workspace found for %s", agent_name)
        return

    decision_path = os.path.join(workspace, DECISION_FILENAME)
    try:
        data = {
            "decision": evaluation.decision.value,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "reasons": [
                {"trigger": r.trigger, "details": r.details, "urgency": r.urgency}
                for r in evaluation.reasons
            ],
        }
        if evaluation.model_override:
            data["model_override"] = evaluation.model_override
        if evaluation.effort_override:
            data["effort_override"] = evaluation.effort_override

        with open(decision_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Failed to write brain decision for %s: %s", agent_name, e)
```

- [ ] **Step 2: Commit**

```bash
git add fleet/core/brain_writer.py
git commit -m "feat: brain decision writer — evaluates agents, writes .brain-decision.json to workspaces"
```

---

### Task 2: Wire Brain Evaluation into Orchestrator

**Files:**
- Modify: `fleet/cli/orchestrator.py`
- Modify: `fleet/infra/mc_client.py`

- [ ] **Step 1: Add post_board_memory to MCClient**

In `fleet/infra/mc_client.py`, after the `heartbeat_agent` method, add:

```python
    async def post_board_memory(self, board_id: str, content: str, tags: list[str] | None = None) -> bool:
        """Post an entry to board memory (activity log).

        Used for heartbeat activity reporting.
        """
        try:
            resp = await self._client.post(
                f"/api/v1/boards/{board_id}/memory",
                json={
                    "content": content,
                    "tags": tags or [],
                },
            )
            return resp.status_code in (200, 201)
        except Exception:
            return False
```

- [ ] **Step 2: Add brain evaluation step to orchestrator**

In `fleet/cli/orchestrator.py`, after the fleet lifecycle update (around line 272) and BEFORE step 0 (`_refresh_agent_contexts`), add:

```python
    # Brain evaluation — evaluate idle/sleeping agents, write decision files, report to MC
    try:
        from fleet.core.brain_writer import write_brain_decisions
        brain_results = write_brain_decisions(
            lifecycle=_fleet_lifecycle,
            now=now,
            tasks=tasks,
            agents=agents,
            board_memory=[],  # TODO: pass board memory when available in cycle
            fleet_dir=os.environ.get("FLEET_DIR", str(Path(__file__).resolve().parent.parent.parent)),
        )
        for agent_name, evaluation in brain_results.items():
            decision = evaluation.decision.value
            if decision == "silent":
                # Touch last_seen_at for silent agents
                agent = agent_name_map.get(agent_name)
                if agent:
                    try:
                        await mc.heartbeat_agent(agent.id)
                    except Exception:
                        pass
                # Report to board
                try:
                    await mc.post_board_memory(
                        board_id,
                        f"Heartbeat received from {agent_name}. (silent)",
                        tags=["heartbeat", "silent", agent_name],
                    )
                except Exception:
                    pass
            elif decision == "strategic":
                try:
                    model = evaluation.model_override or "opus"
                    await mc.post_board_memory(
                        board_id,
                        f"Heartbeat received from {agent_name}. (strategic: {model})",
                        tags=["heartbeat", "strategic", agent_name],
                    )
                except Exception:
                    pass
            # WAKE decisions: no reporting here — the actual heartbeat will report when it runs
        if brain_results:
            silent_count = sum(1 for e in brain_results.values() if e.decision.value == "silent")
            wake_count = sum(1 for e in brain_results.values() if e.decision.value != "silent")
            state.notes.append(f"Brain: {silent_count} silent, {wake_count} wake")
    except Exception as e:
        logger.warning("Brain evaluation failed: %s", e)
```

Also add the import at the top of the file:

```python
from pathlib import Path
```

- [ ] **Step 3: Commit**

```bash
git add fleet/cli/orchestrator.py fleet/infra/mc_client.py
git commit -m "feat: wire brain evaluation into orchestrator cycle, report silent/strategic heartbeats to MC"
```

---

### Task 3: OpenArms Heartbeat Gate Plugin

Create a plugin for the OpenArms gateway that reads `.brain-decision.json` and gates Claude calls.

**Files:**
- Create: `extensions/fleet-heartbeat-gate/openarms.plugin.json`
- Create: `extensions/fleet-heartbeat-gate/index.ts`

- [ ] **Step 1: Create plugin manifest**

```json
{
  "name": "fleet-heartbeat-gate",
  "version": "1.0.0",
  "description": "Gates heartbeat Claude calls using brain decisions from the fleet orchestrator",
  "hooks": {
    "before_dispatch": true
  }
}
```

Save to `extensions/fleet-heartbeat-gate/openarms.plugin.json`.

- [ ] **Step 2: Create the hook implementation**

```typescript
// extensions/fleet-heartbeat-gate/index.ts
//
// Reads .brain-decision.json from agent workspace before each heartbeat.
// If decision is "silent", returns handled=true to skip the Claude call.

import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

interface BrainDecision {
  decision: "silent" | "wake" | "strategic";
  agent: string;
  timestamp: string;
  reasons: Array<{ trigger: string; details: string; urgency: string }>;
  model_override?: string;
  effort_override?: string;
}

const DECISION_FILENAME = ".brain-decision.json";
const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

function readBrainDecision(workspaceDir: string): BrainDecision | null {
  const path = join(workspaceDir, DECISION_FILENAME);
  if (!existsSync(path)) return null;

  try {
    const raw = readFileSync(path, "utf-8");
    const data = JSON.parse(raw) as BrainDecision;

    // Check staleness — if decision is older than 5 min, ignore it (let Claude run)
    if (data.timestamp) {
      const age = Date.now() - new Date(data.timestamp).getTime();
      if (age > STALE_THRESHOLD_MS) return null;
    }

    return data;
  } catch {
    return null;
  }
}

export default function register(api: any) {
  api.registerHook(
    "before_dispatch",
    async (event: any, ctx: any) => {
      // Only gate heartbeats, not regular messages
      if (ctx.trigger !== "heartbeat") {
        return { handled: false };
      }

      // Resolve agent workspace directory
      const workspaceDir = ctx.agentDir || ctx.workspaceDir;
      if (!workspaceDir) {
        return { handled: false };
      }

      const decision = readBrainDecision(workspaceDir);
      if (!decision) {
        // No decision file or stale — let Claude run normally
        return { handled: false };
      }

      if (decision.decision === "silent") {
        // Brain says: nothing needs attention. Skip Claude call.
        return {
          handled: true,
          text: "HEARTBEAT_OK",
        };
      }

      // WAKE or STRATEGIC — let Claude run
      // For STRATEGIC, model/effort overrides are applied via HEARTBEAT.md context
      return { handled: false };
    },
    { name: "fleet-heartbeat-gate" },
  );
}
```

- [ ] **Step 3: Add plugin installation to setup**

In `scripts/apply-patches.sh` or a new script, copy the plugin to the OpenArms extensions directory:

```bash
# Copy fleet heartbeat gate plugin to openarms
OPENARMS_EXT="${HOME}/.openarms/extensions/fleet-heartbeat-gate"
if [[ -d "$FLEET_DIR/extensions/fleet-heartbeat-gate" ]]; then
    mkdir -p "$OPENARMS_EXT"
    cp -r "$FLEET_DIR/extensions/fleet-heartbeat-gate/"* "$OPENARMS_EXT/"
    echo "  Fleet heartbeat gate plugin installed"
fi
```

Add this to `setup.sh` after the gateway starts.

- [ ] **Step 4: Commit**

```bash
git add extensions/fleet-heartbeat-gate/
git commit -m "feat: OpenArms heartbeat gate plugin — reads brain decisions, skips Claude for silent heartbeats"
```

---

### Task 4: Add OpenRouter Qwen3.6 Plus Model

**Files:**
- Modify: `fleet/core/backend_router.py`

- [ ] **Step 1: Add the model to backend definitions**

Read `fleet/core/backend_router.py`. Find the backend definitions (the dict that defines available backends with their capabilities and costs). Add:

```python
    "openrouter-qwen36plus": BackendDef(
        name="openrouter-qwen36plus",
        type="openrouter",
        model_id="qwen/qwen-3.6-plus",
        capabilities=["reasoning", "code", "structured"],
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        confidence_tier="community",
    ),
```

This model is free on OpenRouter and has strong capabilities.

- [ ] **Step 2: Commit**

```bash
git add fleet/core/backend_router.py
git commit -m "feat: add OpenRouter Qwen3.6 Plus as free backend option"
```

---

### Task 5: Wire Backend Routing to Execution

**Files:**
- Modify: `fleet/cli/dispatch.py`
- Modify: `gateway/executor.py`

- [ ] **Step 1: Add non-Claude execution path to executor**

In `gateway/executor.py`, add a function for LocalAI/OpenRouter execution:

```python
def execute_via_openai_compat(
    prompt: str,
    model: str,
    base_url: str,
    api_key: str = "",
    timeout: int = 120,
) -> Dict[str, Any]:
    """Execute via OpenAI-compatible API (LocalAI, OpenRouter).

    Args:
        prompt: The task prompt
        model: Model ID (e.g., "hermes-3b", "qwen/qwen-3.6-plus")
        base_url: API base URL (e.g., "http://localhost:8090/v1")
        api_key: API key (empty for LocalAI)
        timeout: Max seconds

    Returns: dict with 'result', 'usage', 'error'
    """
    import httpx as _httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        r = _httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            return {"result": None, "error": f"API returned {r.status_code}: {r.text[:200]}", "usage": {}}

        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return {
            "result": content,
            "usage": usage,
            "cost_usd": 0,
            "model": model,
            "error": None,
        }
    except Exception as e:
        return {"result": None, "error": str(e), "usage": {}}
```

- [ ] **Step 2: Wire routing decision in dispatch.py**

In `fleet/cli/dispatch.py`, after `route_task()` returns the `RoutingDecision`, add backend switching:

Find where the dispatch actually calls the executor (the `execute_task` call or equivalent). Before it, add:

```python
    # Route to appropriate backend based on routing decision
    if routing.backend == "localai" and localai_available:
        result = execute_via_openai_compat(
            prompt=task_prompt,
            model=routing.model or "hermes-3b",
            base_url="http://localhost:8090/v1",
        )
    elif routing.backend == "openrouter-free":
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        result = execute_via_openai_compat(
            prompt=task_prompt,
            model=routing.model or "qwen/qwen-3.6-plus",
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
        )
    else:
        # Default: Claude Code CLI
        result = execute_task(agent_dir, task_dict, claude_model=model_config.model, timeout=timeout)
```

- [ ] **Step 3: Commit**

```bash
git add fleet/cli/dispatch.py gateway/executor.py
git commit -m "feat: wire backend routing to actual execution — LocalAI and OpenRouter support"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Brain decision writer | `fleet/core/brain_writer.py` (new) |
| 2 | Wire into orchestrator + MC reporting | `orchestrator.py`, `mc_client.py` |
| 3 | OpenArms heartbeat gate plugin | `extensions/fleet-heartbeat-gate/` (new) |
| 4 | Add OpenRouter Qwen3.6 Plus | `backend_router.py` |
| 5 | Wire backend routing to execution | `dispatch.py`, `executor.py` |

**Spec coverage:**
- Part A (brain wiring): Tasks 1, 2, 3
- Part B (backend execution): Tasks 4, 5
- Part C (budget mode): Already implemented, no changes needed
- MC activity reporting: Task 2 (post_board_memory for silent/strategic)
- OpenRouter models: Task 4
