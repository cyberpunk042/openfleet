# Labor Attribution and Provenance System

## Severity: STRATEGIC
## Status: DESIGN
## Created: 2026-03-31

Every artifact produced by the fleet must carry a **labor stamp** — a complete
record of what produced it, how, and at what confidence level. This is not
optional metadata; it is a requirement for observability, scalability, and
trust in a multi-model, multi-backend fleet.

---

## Part 1: PO Requirements (Verbatim)

> "the agents are going to explain the source of their labor, the model, the
> effort, the skills used, etc.. (include the training notion based on the
> source and parameters) we need to evolve and make things observable and
> clean and scalable."

> "the LocalAI work will also need to be flagged as trainee's work like any
> other variant in what was used to generates the artifacts. making sure that
> when the agents leave their marks we know what produced it."

> "Just like we want to use methodologies and skills — Not an always in, more
> like a use case strategy logic decision."

---

## Part 2: Current State — What's Missing

### What Exists Today

| Component | What It Does | Gap |
|-----------|-------------|-----|
| `model_selection.py` | Selects model+effort before dispatch | **Never records** what was actually used |
| `TaskCustomFields.model` | Stores model override for dispatch | Input only — not output provenance |
| `comment.py` templates | Posts `<sub>agent_name</sub>` footer | Zero model/effort/backend metadata |
| `pr.py` templates | Lists `Agent: {agent_name}` in refs | No model, skills, confidence, duration |
| `artifact_tracker.py` | Tracks completeness against standards | No provenance — who produced it, how |
| `effort_profiles.py` | Controls what's allowed (full/minimal) | Not recorded on output artifacts |
| `budget_monitor.py` | Reads Claude quota % | Not linked to per-task cost recording |

### The Broken Chain

```
model_selection.py → ModelConfig(opus, high, reason)
         ↓
dispatch passes to Claude Code session (env vars)
         ↓
agent runs... does work... calls fleet_task_complete()
         ↓
completion comment: "✅ Completed" + summary + agent_name
         ↓
PR body: "Agent: software-engineer"
         ↓
WHERE IS THE MODEL? THE EFFORT? THE SKILLS? THE COST?
→ NOWHERE. The chain is broken at completion.
```

---

## Part 3: Labor Attribution Data Model

### LaborStamp

Every artifact (task completion, PR, commit, board memory, contribution)
carries a `LaborStamp`:

```python
@dataclass
class LaborStamp:
    """Complete provenance record for any fleet-produced artifact."""

    # WHO
    agent_name: str                  # e.g., "software-engineer"
    agent_role: str                  # e.g., "worker" or "driver"

    # WHAT PRODUCED IT
    backend: str                     # "claude-code", "localai", "openrouter", "direct"
    model: str                       # "opus-4-6", "sonnet-4-6", "hermes-3b", "qwen3-8b"
    model_version: str               # Full model ID for reproducibility
    effort: str                      # "low", "medium", "high", "max"

    # HOW
    skills_used: list[str]           # ["feature-implement", "foundation-testing"]
    tools_called: list[str]          # MCP tools invoked during the work
    session_type: str                # "fresh", "compact", "continue"

    # CONFIDENCE
    confidence_tier: str             # "expert", "standard", "trainee", "community", "hybrid"
    confidence_reason: str           # Why this tier (e.g., "localai/hermes-3b = trainee tier")

    # COST
    duration_seconds: int            # Wall clock time
    estimated_tokens: int            # Approximate token usage
    estimated_cost_usd: float        # Approximate cost in USD

    # ITERATION
    iteration: int                   # Which attempt (1 = first, 2 = after rejection, etc.)
    previous_attempt_id: str | None  # Link to prior attempt if this is a retry

    # TIMESTAMP
    timestamp: str                   # ISO 8601
```

### Confidence Tiers

| Tier | When | Review Requirements |
|------|------|---------------------|
| **expert** | Claude opus | fleet-ops standard review |
| **standard** | Claude sonnet or haiku | fleet-ops standard review |
| **trainee** | LocalAI (any model) | fleet-ops review + adversarial challenge |
| **community** | OpenRouter free tier, other free models | fleet-ops review + adversarial challenge + human sign-off |
| **hybrid** | Multiple backends used in one task | Highest scrutiny tier of any component used |

Confidence tier is **derived automatically** from `backend` + `model`:

```python
def derive_confidence_tier(backend: str, model: str) -> tuple[str, str]:
    """Derive confidence tier from backend and model.

    Returns (tier, reason).
    """
    if backend == "claude-code" and "opus" in model:
        return "expert", f"cloud/{model}"
    if backend == "claude-code":
        return "standard", f"cloud/{model}"
    if backend == "localai":
        return "trainee", f"local/{model} — quality unvalidated at scale"
    if backend == "openrouter":
        return "community", f"free-tier/{model} — best-effort, must verify"
    if backend == "direct":
        return "standard", "deterministic/no-LLM — rule-based output"
    return "community", f"unknown/{backend}/{model}"
```

### Training Notion

> "include the training notion based on the source and parameters"

The `confidence_tier` IS the training notion:
- **trainee** means: "this was produced by a model that is still being
  evaluated for reliability in this domain. Treat its output like work
  from a junior team member — review more carefully, verify assumptions,
  check edge cases."
- **community** means: "this was produced by a free model with unknown
  reliability characteristics. Treat as a draft requiring validation."
- The fleet can track over time whether trainee-tier work passes review
  at the same rate as expert-tier work. If LocalAI achieves consistent
  approval rates, the PO can promote it from trainee to standard for
  specific task types.

---

## Part 4: Where the Stamp Appears

### 4.1 Task Custom Fields (MC)

New custom fields on `TaskCustomFields`:

```python
# Labor attribution fields — set on task completion
labor_backend: Optional[str] = None       # Backend that produced the work
labor_model: Optional[str] = None         # Model that produced the work
labor_effort: Optional[str] = None        # Effort level used
labor_confidence: Optional[str] = None    # Confidence tier
labor_skills: Optional[list] = None       # Skills used
labor_cost_usd: Optional[float] = None    # Estimated cost
labor_duration_s: Optional[int] = None    # Duration in seconds
labor_iteration: int = 1                  # Attempt number
```

### 4.2 Task Completion Comment

Updated `format_complete()` in `comment.py`:

```markdown
## ✅ Completed

**PR:** [url](url)
**Branch:** `feat/task-12345678`
**Commits:** 3

### Summary
Implemented the authentication middleware with JWT validation...

### Labor Attribution
| | |
|---|---|
| **Agent** | software-engineer |
| **Backend** | claude-code |
| **Model** | opus-4-6 |
| **Effort** | high |
| **Confidence** | expert (cloud/opus-4-6) |
| **Skills** | feature-implement, foundation-testing |
| **Duration** | 12m 34s |
| **Est. Cost** | ~$0.67 |
| **Iteration** | 1 of 1 |

---
<sub>software-engineer · opus-4-6 · expert</sub>
```

### 4.3 PR Body

Updated `format_pr_body()` in `pr.py` — add a Labor Attribution section:

```markdown
## 🔗 References

| | |
|---|---|
| **Task** | [12345678](task_url) |
| **Agent** | software-engineer |
| **Model** | opus-4-6 (expert) |
| **Effort** | high |
| **Skills** | feature-implement, foundation-testing |
| **Cost** | ~$0.67 · 12m 34s |
| **Branch** | [`feat/task-12345678`](compare_url) |

---
<sub>Generated by OpenClaw Fleet · opus-4-6 · expert tier</sub>
```

### 4.4 Git Commits

The `Co-Authored-By` footer already exists. Add model attribution:

```
feat(auth): implement JWT validation middleware

Refs: TASK-12345678
Co-Authored-By: software-engineer <agent@openclaw.fleet>
Model: opus-4-6 (expert)
```

### 4.5 Board Memory

When posting to board memory, include the tier:

```
[completion] software-engineer completed auth middleware (opus-4-6/expert, ~$0.67)
```

### 4.6 Event Bus

New event type `fleet.labor.recorded`:

```json
{
  "type": "fleet.labor.recorded",
  "source": "fleet/orchestrator",
  "data": {
    "task_id": "12345678-...",
    "agent_name": "software-engineer",
    "labor_stamp": { ... full LaborStamp ... }
  }
}
```

---

## Part 5: How the Stamp Gets Populated

The stamp is NOT populated by the agent (agents can't be trusted to
self-report accurately). It is populated by the **infrastructure**:

### Step 1: Dispatch Records Intent

When the brain dispatches a task, it records the `ModelConfig` selection:

```python
# In orchestrator dispatch:
model_config = select_model_for_task(task, agent_name)
# Store in dispatch context — available to fleet_task_complete later
dispatch_record = {
    "model": model_config.model,
    "effort": model_config.effort,
    "reason": model_config.reason,
    "backend": "claude-code",  # or "localai" in Stage 2+
    "dispatched_at": now_iso(),
    "skills": task_skills,  # from skill_enforcement.py
}
```

### Step 2: Session Tracks Execution

The gateway/session tracks:
- Start time, end time → duration
- Token usage (from Claude API response or LocalAI response)
- Tools called (from MCP server logs)
- Session type (fresh/compact/continue)

### Step 3: Completion Assembles the Stamp

When `fleet_task_complete()` runs, it:
1. Reads the dispatch record
2. Reads the session metrics
3. Derives the confidence tier
4. Assembles the full `LaborStamp`
5. Writes it to: task custom fields, comment, PR, board memory, event bus

### Step 4: Review Checks the Stamp

When fleet-ops reviews:
- If `confidence_tier` is `trainee` or `community` → **adversarial challenge
  required** (see iterative validation milestone)
- If `confidence_tier` is `expert` or `standard` → standard review
- The review comment includes whether the confidence tier was appropriate:
  "Trainee-tier work passed review — consider promoting for this task type"

---

## Part 6: Milestones

### M-LA01: LaborStamp Data Model
- Define `LaborStamp` dataclass in `fleet/core/models.py`
- Define `derive_confidence_tier()` function
- Add labor custom fields to `TaskCustomFields`
- Add tests for tier derivation logic
- **Status:** ⏳ PENDING

### M-LA02: Dispatch Records Intent
- Modify orchestrator dispatch to record `dispatch_record` per task
- Store in session context (available to MCP tools)
- Record: model, effort, backend, skills, dispatch time
- **Status:** ⏳ PENDING

### M-LA03: Session Metrics Collection
- Track per-session: start time, end time, tools called, token estimate
- Make metrics available to `fleet_task_complete()` via context
- **Status:** ⏳ PENDING

### M-LA04: Stamp Assembly in fleet_task_complete
- Assemble full `LaborStamp` from dispatch record + session metrics
- Write to task custom fields
- Include in completion comment (updated template)
- Include in PR body (updated template)
- Post to board memory with tier tag
- Emit `fleet.labor.recorded` event
- **Status:** ⏳ PENDING

### M-LA05: Updated Comment and PR Templates
- Update `fleet/templates/comment.py` — add Labor Attribution section
- Update `fleet/templates/pr.py` — add model/tier to references
- Update `fleet/templates/commit.py` (if exists) — add Model footer
- Update board memory posting format
- Tests for all template changes
- **Status:** ⏳ PENDING

### M-LA06: Confidence-Aware Review Gates
- fleet-ops review logic checks `confidence_tier`
- trainee/community → require adversarial challenge (cross-ref: iterative
  validation milestone)
- expert/standard → standard review
- Track approval rates per confidence tier over time
- **Status:** ⏳ PENDING

### M-LA07: Labor Analytics
- Aggregate labor stamps across tasks: cost per agent, cost per model,
  cost per confidence tier, approval rate per tier
- Surface in fleet-ops monitoring
- Feed into budget mode decisions (cross-ref: budget mode milestone)
- **Status:** ⏳ PENDING

### M-LA08: Heartbeat Labor Stamps
- Even heartbeats get minimal labor stamps (agent, model, cost, duration)
- Track heartbeat cost trends — detect when heartbeats are too expensive
- Cross-ref: catastrophic drain prevention
- **Status:** ⏳ PENDING

---

## Part 7: Cross-References

| Related Milestone | Relationship |
|-------------------|-------------|
| Budget Mode System | Labor stamps feed cost data into budget mode decisions |
| Multi-Backend Router | Router determines backend → stamp records what was chosen |
| Iterative Validation | Confidence tier determines review depth |
| Model Upgrade Path | New models get new tier mappings |
| Storm Prevention | Labor stamps detect cost anomalies per agent |
| Fleet Elevation Doc 17 | Standards framework — labor stamp is a new artifact standard |
| Fleet Elevation Doc 19 | Flow validation — stamp is a new quality gate input |
| Fleet Elevation Doc 23 | Agent lifecycle — stamps track cost-per-state transitions |
| Catastrophic Drain Investigation | Stamps would have detected void work immediately |

---

## Part 8: Why This Matters

The catastrophic drain of March 2026 happened because **nobody could tell
what was producing tokens or why**. 2,123 MCP sessions with zero attribution.
If every session had carried a labor stamp, the drain would have been:
- **Detectable**: "2,123 heartbeat stamps in 1 hour, all costing $0.15 each"
- **Attributable**: "Gateway heartbeats, not orchestrator dispatch"
- **Preventable**: "Heartbeat cost trend anomaly detected at session #50"

As the fleet expands to multiple backends (LocalAI, OpenRouter, future models),
attribution becomes even more critical. Without it, you cannot:
- Know what produced a buggy PR
- Compare quality across models
- Prove that LocalAI offload is working
- Detect when a free model produces garbage
- Budget accurately for the fleet
- Trust any artifact without checking its source

> The labor stamp is the fleet's provenance chain. Without it, the fleet
> is a black box. With it, every artifact is traceable, auditable, and
> trustworthy — or explicitly flagged as needing verification.