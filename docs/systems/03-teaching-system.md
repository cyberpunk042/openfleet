# System 3: Teaching System

**Source:** `fleet/core/teaching.py` (80+ lines)
**Status:** ✅ Live verified (VERIFICATION-MATRIX.md)
**Design docs:** `teaching-system/01-overview.md`, `fleet-elevation/20`

---

## Purpose

Delivers adapted lessons when the immune system detects disease. Lessons are adapted to the specific disease + task + agent. Comprehension is verified through practice exercises. Key PO insight: "seeing the pattern does not break the pattern, it's forging the right path multiple times that does."

## Key Concepts

### Lesson Structure (teaching.py:58-67)

```python
@dataclass
class Lesson:
    disease: DiseaseCategory      # What disease this treats
    agent_name: str               # Which agent
    task_id: str                  # On which task
    content: str                  # Lesson text injected into context
    exercise: PracticeExercise    # Agent must complete to demonstrate comprehension
    attempt: int = 0              # Current attempt number
    max_attempts: int = 3         # Max tries before prune
    outcome: LessonOutcome        # comprehension_verified / no_change / in_progress
```

### Lesson Templates (teaching.py:71-77)

Templates with `{placeholders}` adapted per disease:
- `lesson_template` — the instruction text
- `exercise_template` — what the agent must do
- `verification_hint_template` — what correct response contains

### Lesson Outcomes (teaching.py:43-47)

- `COMPREHENSION_VERIFIED` — agent demonstrated understanding
- `NO_CHANGE` — agent didn't learn, escalate to prune
- `IN_PROGRESS` — still attempting

### Delivery Flow

1. Doctor detects disease → creates Intervention with `TRIGGER_TEACHING`
2. Orchestrator calls `adapt_lesson(disease, agent, task, context)`
3. Lesson adapted from template with specific context
4. `format_lesson_for_injection(lesson)` prepares text
5. `inject_content(session_key, lesson_text)` via gateway client
6. Agent autocompletes from lesson before continuing work
7. Orchestrator checks: did comprehension improve?
8. If no change after max_attempts → prune

## Connections to Other Systems

| System | Connection | Direction |
|--------|-----------|-----------|
| **Doctor** | Doctor triggers teaching when disease detected | Doctor → Teaching |
| **Orchestrator** | Orchestrator manages lesson injection and outcome tracking | Orchestrator → Teaching |
| **Gateway** | Lessons injected via `inject_content()` | Teaching → Gateway |
| **Agent Lifecycle** | Teaching failure → prune → agent regrows fresh | Teaching → Lifecycle |
| **Events** | Teaching events emitted (lesson_delivered, comprehension_result) | Teaching → Events |

## What's Needed

- [ ] More lesson templates (only basic templates exist)
- [ ] Comprehension verification logic (agent response analysis)
- [ ] Teaching history per agent (track lessons over time)
- [ ] Integration with contribution flow diseases
