# System 9: Standards Library

**Source:** `fleet/core/standards.py`, `fleet/core/plan_quality.py`, `fleet/core/pr_hygiene.py`
**Status:** 🔨 Standards defined, compliance checking exists. Not injected into agent context.
**Design docs:** `fleet-elevation/17`, `standards-and-discipline.md` (M44-47)

---

## Purpose

Defines what "done right" looks like for every artifact type. Each artifact has required fields, quality criteria, and examples. Standards are checked by the artifact tracker and referenced by the teaching system for adapted lessons.

## Key Concepts

### Standard Definition (standards.py:18-35)

```python
@dataclass
class Standard:
    artifact_type: str           # analysis_document, plan, pull_request, etc.
    description: str
    required_fields: list[RequiredField]  # name, description, required bool
    quality_criteria: list[str]
    positive_example: str
    negative_example: str
```

### ComplianceResult (standards.py:38-55)

```python
missing_fields: list[str]    # required fields not present
failed_criteria: list[str]   # quality criteria not met
compliant: bool              # True if nothing missing and nothing failed
score: int                   # 0-100, each missing item deducts 15 points
```

### Artifact Types (standards.py:60+)

Registered standards include:
- `task` — requires: title, requirement_verbatim, description, acceptance_criteria, task_type, task_stage, task_readiness
- `analysis_document` — requires: scope, findings, implications
- `plan` — requires: requirement_reference, target_files, steps
- `pull_request` — requires: description, changelog, diff summary
- `completion_claim` — requires: summary, acceptance_criteria_met

### Plan Quality (plan_quality.py)

Checks plans reference verbatim, specify target files, map acceptance criteria.

### PR Hygiene (pr_hygiene.py)

Checks PR body quality, conventional commits, changelog presence.

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Artifact Tracker** | Checks artifacts against standards → completeness | Standards → Tracker |
| **Methodology** | Readiness suggested by completeness | Tracker → Methodology |
| **Doctor** | Incomplete artifacts detected as laziness | Standards → Doctor |
| **Teaching** | Lessons reference standard requirements | Standards → Teaching |
| **MCP Tools** | Artifact tools check completeness on update | Standards → MCP |
| **Skill Enforcement** | Required tools per task type | Enforcement → Standards |

## What's Needed

- [ ] Standards injected into agent context based on current artifact type (AR-14)
- [ ] More artifact type standards (investigation_document, bug, security_assessment)
- [ ] Phase-dependent quality bars (POC = basic, production = comprehensive)
