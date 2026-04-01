# Transpose Layer — Object ↔ Rich HTML

> **2 files. 573 lines. Agents work with dicts. Plane shows rich HTML. Transpose converts between them.**
>
> The transpose layer is the bridge between agent-friendly structured
> objects and human-readable rich HTML on Plane. When an agent calls
> `fleet_artifact_update("findings", ...)`, the tool updates the object,
> the transpose layer renders it as rich HTML, and Plane shows a
> formatted document. When the agent reads back, transpose reverses:
> HTML → object. Content OUTSIDE artifact markers is NEVER touched —
> the PO can add manual notes alongside fleet artifacts.

### PO Requirement (Verbatim)

> "TRANSPOSE.... YOU HAVE DATA e.g. JSON AND IT TRANSPOSE INTO A
> FUCKING RICH HTML...... and in reverse"

---

## 1. Why It Exists

Agents think in structured data. Humans read formatted documents.
Without transpose:
- Agent would need to generate HTML (expensive, error-prone, inconsistent)
- Or Plane would show raw JSON (unreadable to humans)
- Or separate human and agent views (out of sync)

Transpose solves all three: agents update structured fields, humans
see rich HTML, both look at the same Plane issue, both can coexist.

```
AGENT SIDE                    TRANSPOSE                   HUMAN SIDE (Plane)
┌──────────────┐                                         ┌──────────────────┐
│ {            │              to_html()                  │ ## Analysis       │
│   "title":   │  ─────────────────────────────────►     │                  │
│   "findings":│                                         │ **Scope:** ...    │
│   "scope":   │                                         │                  │
│ }            │                                         │ ### Findings      │
└──────────────┘              from_html()                │ - Finding 1...   │
                  ◄─────────────────────────────────     │ - Finding 2...   │
                                                         │                  │
                                                         │ *PO's notes here*│
                                                         │ (untouched)      │
                                                         └──────────────────┘
```

---

## 2. How It Works

### 2.1 Object → HTML (to_html)

```
Agent calls fleet_artifact_create("analysis_document", "Title")
  ↓
Tool creates initial object: {"title": "Title", "scope": "", ...}
  ↓
to_html("analysis_document", object)
  ↓
1. Look up renderer for "analysis_document" (7 renderers registered)
  ↓
2. Render object fields as rich HTML:
   - Title → <h2>
   - Scope → <p><strong>Scope:</strong> ...</p>
   - Findings → <h3>Findings</h3> + per-finding blocks with code refs
   - Options → <table> with Pros/Cons columns
   - Steps → <ol> ordered list
  ↓
3. Embed object as hidden JSON data blob:
   <span class="fleet-data" data-type="analysis_document"
         style="display:none">{json}</span>
  ↓
4. Wrap in artifact markers:
   <span class="fleet-artifact-start" data-type="analysis_document">
   {data blob}
   {rendered HTML}
   <span class="fleet-artifact-end">
  ↓
5. Send to Plane via API → human sees formatted document
```

### 2.2 HTML → Object (from_html)

```
Agent calls fleet_artifact_read()
  ↓
Tool fetches Plane issue description_html
  ↓
from_html(html_content)
  ↓
1. Regex finds <span class="fleet-data" ...>{json}</span>
  ↓
2. HTML-unescape the JSON string
  ↓
3. json.loads() → structured object dict
  ↓
4. Return to agent as dict (ready for updates)
```

**Key:** The data blob (hidden `fleet-data` span) IS the source of truth.
The visible HTML is a RENDERING of that data. On update: read data blob →
modify object → re-render. The visible HTML is always regenerated from
the object, never parsed.

### 2.3 Update Flow

```
Agent calls fleet_artifact_update("findings", append=True, value={...})
  ↓
Tool calls update_artifact(html_content, {"findings": [new_finding]})
  ↓
1. from_html() extracts current object from data blob
  ↓
2. Merge updates:
   - List fields: APPEND (obj["findings"].extend(new))
   - Non-list fields: REPLACE (obj["scope"] = new_value)
  ↓
3. to_html() re-renders full artifact
  ↓
4. Regex replaces old artifact section in HTML
   (content OUTSIDE artifact markers is preserved)
  ↓
5. Updated HTML sent to Plane
```

### 2.4 Coexistence with PO Content

```html
<!-- PO writes notes HERE — untouched by transpose -->
<p>My thoughts on this task...</p>

<!-- Fleet artifact section -->
<span class="fleet-artifact-start" data-type="plan">artifact:start</span>
<span class="fleet-data" data-type="plan">{json}</span>
<h2>Plan: Add Fleet Controls</h2>
<blockquote>Verbatim Requirement: "Add controls to header..."</blockquote>
<p><strong>Approach:</strong> ...</p>
<span class="fleet-artifact-end">artifact:end</span>

<!-- PO writes more notes HERE — also untouched -->
<p>Additional context: ...</p>
```

The regex that replaces artifacts only touches content between
`fleet-artifact-start` and `fleet-artifact-end`. Everything else
is preserved verbatim.

### 2.5 Artifact Completeness

After transpose renders, the artifact tracker checks completeness:

```
ArtifactCompleteness:
  artifact_type: "plan"
  total_required: 6        (title, requirement_reference, approach,
                            target_files, steps, criteria_mapping)
  filled_required: 4       (title ✓, requirement_reference ✓,
                            approach ✓, target_files ✓)
  missing_required: ["steps", "acceptance_criteria_mapping"]
  required_pct: 67%        (4/6)
  overall_pct: 57%         (4/7 including optional)
  is_complete: False
  suggested_readiness: 50  (60-75% completeness → readiness 70)
```

Readiness mapping (artifact_tracker.py:58-76):
```
required_pct     → suggested_readiness
    0%           →  0
   <25%          → 10
   <40%          → 20
   <60%          → 50
   <75%          → 70
   <90%          → 80
   <100%         → 90
   100% req      → 90 (check optional)
   100% + ≥90%   → 95
```

---

## 3. File Map

```
fleet/core/
├── transpose.py       Object↔HTML, 7 renderers, markers, update   (396 lines)
└── artifact_tracker.py Completeness checking, readiness suggestion  (177 lines)
```

Total: **573 lines** across 2 modules.

---

## 4. Per-File Documentation

### 4.1 `transpose.py` — Bidirectional Conversion (396 lines)

#### HTML Markers

| Marker | Purpose |
|--------|---------|
| `fleet-artifact-start` | Start of artifact section, `data-type` identifies type |
| `fleet-artifact-end` | End of artifact section |
| `fleet-data` | Hidden JSON blob — source of truth for the object |

All use `<span>` with `style="display:none"` because Plane strips HTML comments.

#### Registered Renderers (7)

| Type | Renders As |
|------|-----------|
| `analysis_document` | h2 title, scope paragraph, findings with code refs, open questions list |
| `investigation_document` | h2 title, scope, findings, options TABLE (name/pros/cons), sources, recommendations blockquote |
| `plan` | h2 title, verbatim BLOCKQUOTE, approach, target files CODE list, ORDERED steps, criteria TABLE |
| `progress_update` | h3 update, what done, what next, blockers, readiness change |
| `bug` | h2 title, ORDERED steps to reproduce, expected/actual, environment, impact, evidence CODE block |
| `completion_claim` | h2, PR link, summary, criteria TABLE (criterion/met/evidence), files code list |
| `pull_request` | h2 title, description, changes, testing, task reference |

#### Public Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `to_html(artifact_type, obj)` | 278-308 | Look up renderer. Embed JSON data blob. Wrap in markers. Return rich HTML. Fallback: formatted JSON if no renderer. |
| `from_html(html_content)` | 311-335 | Extract fleet-data span via regex. HTML-unescape. JSON parse. Return dict or None. |
| `get_artifact_type(html_content)` | 338-349 | Extract data-type from fleet-artifact-start span. Return type string or None. |
| `update_artifact(html_content, updates)` | 352-397 | Read object → merge updates (append lists, replace scalars) → re-render → regex replace in HTML. Preserves content outside artifact markers. |

#### Helper Functions

| Function | Lines | What It Does |
|----------|-------|-------------|
| `_render_field(name, html)` | 43-44 | Passthrough (for future field-level wrapping) |
| `_escape(text)` | 47-48 | HTML escape |
| `_render_list(items, ordered)` | 51-54 | ul/ol list rendering |
| `_render_code_list(items)` | 57-59 | ul with code elements |
| `_render_table(headers, rows)` | 62-69 | HTML table with thead/tbody |
| `_timestamp()` | 72-73 | Current time formatted |

### 4.2 `artifact_tracker.py` — Completeness Tracking (177 lines)

| Class | Lines | Purpose |
|-------|-------|---------|
| `ArtifactCompleteness` | 23-76 | Tracks: total_required, filled_required, total_optional, filled_optional, missing_required, missing_optional. Properties: required_pct, overall_pct, is_complete, suggested_readiness. |

| Function | Lines | What It Does |
|----------|-------|-------------|
| `check_artifact_completeness(type, obj)` | 79-130 | Check object against standard. For each required field: present and non-empty? Count filled vs total. Return ArtifactCompleteness. |
| `format_completeness_summary(completeness)` | 133-177 | Human-readable summary: "Plan: 4/6 required (67%). Missing: steps, criteria_mapping. Suggested readiness: 50%." |

---

## 5. Dependency Graph

```
transpose.py         ← standalone (html, json, re, datetime)
    ↑
artifact_tracker.py  ← imports get_standard, check_standard from standards
                       imports VALID_READINESS from methodology
```

---

## 6. Consumers

| Layer | Module | What It Imports | How It Uses It |
|-------|--------|----------------|---------------|
| **MCP Tools** | `tools.py` | `to_html, from_html` | fleet_artifact_create/update/read: transpose between agent objects and Plane HTML |
| **MCP Tools** | `tools.py` | `check_artifact_completeness, format_completeness_summary` | After artifact update: check completeness → return suggested readiness |
| **Context Assembly** | `context_assembly.py` | `from_html, get_artifact_type, check_artifact_completeness` | Include artifact data and completeness in task context bundle |

---

## 7. Design Decisions

### Why hidden span for data, not HTML comments?

Plane CE strips HTML comments (`<!-- -->`). The fleet-data span with
`style="display:none"` survives Plane's sanitizer while remaining
invisible to humans. The `class="fleet-data"` enables reliable
regex extraction.

### Why JSON blob as source of truth, not parsed HTML?

Parsing rich HTML back to structured data is fragile — HTML formatting
varies, Plane may modify whitespace, elements might be reordered.
The JSON blob is exact, round-trips perfectly, and is the same data
the agent works with. The visible HTML is just a presentation layer.

### Why append for lists, replace for scalars?

Analysis findings accumulate across cycles. Each cycle adds new
findings (append). But scope is set once and may be corrected
(replace). The merge strategy matches how agents work: they ADD
findings progressively but REPLACE the approach if the plan changes.

### Why 7 renderers and not dynamic?

Each artifact type has different fields and layout. An analysis
document shows findings with code references. A plan shows steps
in ordered list with acceptance criteria table. A bug report shows
steps to reproduce. Dynamic rendering would produce generic output.
Type-specific renderers produce publication-quality output per
the PO's standards.

### Why doesn't the tracker auto-update readiness?

The tracker SUGGESTS readiness. The PM or PO SETS readiness. This
preserves PO authority — the system provides data, the human decides.
Auto-setting readiness would bypass the PO's judgment about whether
the artifact quality is sufficient for its purpose.

---

## 8. Progressive Work Pattern

The transpose layer enables progressive work across multiple
orchestrator cycles:

```
Cycle 1: Agent creates analysis artifact
  fleet_artifact_create("analysis_document", "Header Analysis")
  → obj = {"title": "Header Analysis"}
  → HTML rendered with empty fields
  → Plane shows: "Analysis: Header Analysis" (minimal)
  → Completeness: 1/5 = 20% → suggested readiness: 10

Cycle 2: Agent examines codebase
  fleet_artifact_update("scope", "DashboardShell.tsx header section")
  fleet_artifact_update("findings", append=True, value={
    "title": "Flex container",
    "finding": "Header uses flex-1 with room for controls",
    "files": ["DashboardShell.tsx:42"]
  })
  → obj updated with scope + 1 finding
  → HTML re-rendered (scope paragraph + findings section)
  → Completeness: 3/5 = 60% → suggested readiness: 50

Cycle 3: Agent adds implications
  fleet_artifact_update("implications", "Controls can be injected...")
  fleet_artifact_update("current_state", "Header has 3 sections...")
  → obj now has all required fields
  → HTML re-rendered (full document)
  → Completeness: 5/5 = 100% → suggested readiness: 90

PO reviews → confirms → readiness 99 → work unlocked
```

---

## 9. Data Shapes

### Artifact Object (plan type)

```python
{
    "title": "Add Fleet Controls to Header",
    "requirement_reference": "Add fleet controls to the OCMC header bar...",
    "approach": "Inject FleetControlBar component into DashboardShell.tsx",
    "target_files": ["DashboardShell.tsx", "FleetControlBar.tsx"],
    "steps": [
        "Create FleetControlBar component with 3 dropdowns",
        "Import in DashboardShell.tsx",
        "Add to header section after OrgSwitcher"
    ],
    "acceptance_criteria_mapping": {
        "Controls visible in header": "FleetControlBar renders in header",
        "Mode switching works": "Dropdowns update fleet_config"
    }
}
```

### Rendered HTML (plan type)

```html
<span class="fleet-artifact-start" data-type="plan">artifact:start</span>
<span class="fleet-data" data-type="plan">{"title":"Add Fleet Controls..."}</span>
<h2>Plan: Add Fleet Controls to Header</h2>
<blockquote><strong>Verbatim Requirement:</strong><br/>
Add fleet controls to the OCMC header bar...</blockquote>
<p><strong>Approach:</strong> Inject FleetControlBar component...</p>
<p><strong>Target Files:</strong></p>
<ul><li><code>DashboardShell.tsx</code></li><li><code>FleetControlBar.tsx</code></li></ul>
<h3>Steps</h3>
<ol><li>Create FleetControlBar component...</li><li>Import in DashboardShell...</li></ol>
<h3>Acceptance Criteria</h3>
<table>...</table>
<p><em>Reasoning stage — 2026-03-31 15:42</em></p>
<span class="fleet-artifact-end">artifact:end</span>
```

### ArtifactCompleteness

```python
ArtifactCompleteness(
    artifact_type="plan",
    total_required=6,
    filled_required=4,
    total_optional=1,
    filled_optional=0,
    missing_required=["steps", "acceptance_criteria_mapping"],
    missing_optional=["risks"],
    # required_pct = 67%
    # overall_pct = 57%
    # is_complete = False
    # suggested_readiness = 50
)
```

---

## 10. What's Needed

### Missing Renderers

The following contribution types need renderers:
- `security_assessment` — security review findings
- `qa_test_definition` — predefined test criteria
- `ux_spec` — component patterns, interaction flows
- `documentation_outline` — doc plan before implementation
- `compliance_report` — trail verification results

These are contribution artifact types from fleet-elevation/15 that
agents would produce via `fleet_contribute` (when implemented).

### Renderer Quality

Current renderers produce functional HTML. To meet the PO's standard
("high standard content required"), they should be enhanced with:
- Better table styling (borders, alternating rows)
- Code block syntax highlighting
- Collapsible sections for long findings
- Status indicators (✓/✗) for criteria

### Live Test

No artifact has been created → transposed → read back → updated
with a real agent. The round-trip works in unit tests but has never
been tested end-to-end with Plane.

### Test Coverage

| File | Tests | Coverage |
|------|-------|---------|
| `test_transpose.py` | 20+ | All 7 renderers, from_html, update_artifact, marker preservation |
| `test_artifact_tracker.py` | 15+ | Completeness checking, readiness mapping, standard matching |
| **Total** | **35+** | Core logic covered. Missing: Plane round-trip, PO content preservation |
