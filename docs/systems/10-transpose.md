# System 10: Transpose Layer

**Source:** `fleet/core/transpose.py`, `fleet/core/artifact_tracker.py`
**Status:** 🔨 Code exists. Artifact tools use it. Not live tested with real agents.
**Design docs:** `transpose-layer.md` (T01-T07)

---

## Purpose

Bidirectional conversion between structured objects (dicts) and rich HTML for Plane. Agent works with simple objects. Plane shows rich formatted content. Content outside artifact markers is NEVER touched — PO can add manual notes.

### PO Requirement (Verbatim)

> "TRANSPOSE.... YOU HAVE DATA e.g. JSON AND IT TRANSPOSE INTO A FUCKING RICH HTML...... and in reverse"

## Key Concepts

### Object → HTML (transpose.py)

Takes structured dict → renders as rich HTML with fleet markers:
```html
<span class="fleet-artifact-start" data-type="analysis_document">artifact:start</span>
<span class="fleet-data" data-type="analysis_document">{json_data}</span>
<!-- visual rendering here -->
<span class="fleet-artifact-end">artifact:end</span>
```

The data blob (`fleet-data` span) is the source of truth. Visual HTML is a RENDERING.

### HTML → Object (transpose.py)

Reverse: parse Plane HTML with markers → extract object for agent to continue working.

### Artifact Tracker (artifact_tracker.py)

Checks artifact against its standard:
```python
ArtifactCompleteness:
    required_pct: int       # % of required fields filled
    overall_pct: int        # % of all fields filled
    missing_required: list  # what's still needed
    suggested_readiness: int  # maps completeness to valid readiness
    is_complete: bool       # all required fields present
```

Readiness mapping (artifact_tracker.py:58-76):
- 0% → 0, <25% → 10, <40% → 20, <60% → 50, <75% → 70, <90% → 80, <100% → 90, 100% required + 90% optional → 95

### Progressive Work Pattern

```
Cycle 1: Agent creates artifact → 2/5 fields → completeness 40% → readiness 20
Cycle 2: Agent updates artifact → 4/5 fields → completeness 80% → readiness 80
Cycle 3: Agent completes artifact → 5/5 fields → completeness 100% → readiness 90
PO confirms → readiness 99 → WORK stage unlocked
```

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **MCP Tools** | fleet_artifact_create/update/read use transpose | MCP → Transpose |
| **Standards** | Completeness checked against standard definitions | Standards → Tracker |
| **Methodology** | Suggested readiness feeds readiness decisions | Tracker → Methodology |
| **Plane** | HTML rendered to/from Plane issue descriptions | Transpose ↔ Plane |
| **Context Assembly** | Artifact completeness included in task context | Tracker → Context |

## What's Needed

- [ ] T01-T07 milestones implementation (design exists)
- [ ] More artifact type renderers
- [ ] Live test: agent creates artifact → Plane shows rich HTML → agent continues
