# System 03: Teaching — Adapted Lessons, Injection, Comprehension

**Type:** Fleet System
**ID:** S03
**Files:** teaching.py (485 lines)
**Total:** 485 lines — one focused module
**Tests:** 25+

## What This System Does

The treatment arm of the immune system. When the doctor detects a disease, the teaching system creates an adapted lesson SPECIFIC to the disease + task + agent context, injects it into the agent's session via the gateway, and verifies comprehension through a practice exercise. If the agent can't demonstrate understanding after 3 attempts, it gets pruned (session killed, fresh start).

Detection without correction is surveillance, not medicine. Teaching adds the middle path between "ignore" and "kill."

## How It Works — The Teaching Pipeline

```
Doctor detects disease
  ↓
Doctor creates Intervention(action=TRIGGER_TEACHING)
  ↓
Orchestrator calls adapt_lesson(disease, agent, task, context)
  ↓
Teaching finds template for this disease category
  ↓
Template filled with SPECIFIC context:
  {requirement_verbatim} → actual PO words
  {current_stage} → the stage the agent is in
  {what_agent_did} → actual tool calls or actions that triggered detection
  {agent_plan} → what the agent planned to do
  ↓
Lesson + exercise generated
  ↓
format_lesson_for_injection(lesson) → injectable text
  ↓
Orchestrator calls inject_content(session_key, text) via gateway WebSocket
  ↓
Agent receives lesson in their context
  ↓
Agent MUST complete exercise before continuing work
  ↓
evaluate_response(lesson, agent_response):
  ├── COMPREHENSION_VERIFIED → agent continues with corrected understanding
  └── NO_CHANGE → retry (up to 3 attempts) → PRUNE
```

## Lesson Templates (8 of 11 diseases)

Each template is tailored to the specific disease. Not generic advice — specific to what went wrong.

| Disease | What the Lesson Says | Exercise Requires |
|---------|---------------------|-------------------|
| DEVIATION | "Your plan doesn't match the requirement" | Map each requirement term to specific file/line |
| LAZINESS | "You addressed X but missed Y" | List ALL required items, acknowledge what was missed |
| CONFIDENT_BUT_WRONG | "You were building X when requirement says Y" | Write single sentence using ONLY PO's words |
| PROTOCOL_VIOLATION | "You're in {stage}, protocol allows {X}, you did {Y}" | Identify stage, rules, violation, correct alternative |
| ABSTRACTION | "PO said X, you interpreted as Y" | Process PO's words LITERALLY, word by word |
| CODE_WITHOUT_READING | "You modified {file} without reading it" | List every function in the file, show correct signature |
| SCOPE_CREEP | "You also did {extra} — nobody asked for that" | Separate in-scope from out-of-scope work |
| COMPRESSION | "PO described {large}, you compressed to {small}" | List every component without summarizing |

**3 diseases have NO template:** cascading_fix, context_contamination, not_listening → generic fallback lesson.

## Comprehension Evaluation

Intentionally SIMPLE heuristic (not LLM — would cost tokens and could be gamed):

```
4 indicators checked:
  1. References requirement or verbatim (knows what was asked)
  2. Acknowledges mistake ("should have", "instead", "mistake")
  3. Response has substance (>100 chars, not just "I understand")
  4. Doesn't just parrot the lesson back

Score: 2+ of 4 → COMPREHENSION_VERIFIED
       <2     → NO_CHANGE → retry or prune
```

Templates are DETERMINISTIC, FREE, INSTANT — no LLM involved. This is intentional: LLM lessons would cost tokens, be gameable, and be non-deterministic.

## Key PO Insight

"Seeing the pattern does not break the pattern, it's forging the right path multiple times that does."

The exercise FORCES the agent to produce output demonstrating understanding. This output then becomes part of the agent's context, influencing subsequent behavior. The act of writing the correct answer is what changes behavior — not just reading the lesson.

## Data Classes

- **DiseaseCategory** — 11 enum values (one per disease type)
- **LessonOutcome** — COMPREHENSION_VERIFIED, NO_CHANGE, IN_PROGRESS
- **PracticeExercise** — exercise instruction + verification hint
- **Lesson** — adapted lesson: disease, agent, task, content, exercise, attempt (0-based), max_attempts (3), outcome
- **LessonTemplate** — template with {placeholders}: disease, description, lesson_template, exercise_template, verification_hint_template
- **LessonRecord** — persisted: agent, task, disease, attempt, outcome, timestamp

## Key Functions

| Function | What It Does |
|----------|-------------|
| `adapt_lesson(disease, agent, task_id, context)` | Finds template, fills placeholders with context dict, returns adapted Lesson |
| `format_lesson_for_injection(lesson)` | Formats as injectable text with headers, attempt counter, prune warning |
| `evaluate_response(lesson, agent_response)` | Checks 4 indicators, returns COMPREHENSION_VERIFIED or NO_CHANGE |

## LessonTracker

Persistent tracker per agent: records every lesson attempt, outcome, timestamp. Emits events: comprehension_verified, comprehension_failed, practice_attempted. This history feeds the doctor's cumulative pattern detection.

## Relationships

- TRIGGERED BY: doctor.py (TRIGGER_TEACHING intervention)
- USES: gateway_client.py inject_content (delivers lesson to agent session)
- CONSUMED BY: orchestrator.py (orchestrator calls adapt_lesson + format + inject)
- CONNECTS TO: S02 immune system (doctor detects → teaching treats)
- CONNECTS TO: S04 event bus (teaching events emitted: lesson_injected, comprehension_verified)
- CONNECTS TO: S15 challenge (challenge_analytics.teaching_signals → feed teaching for repeated failures)
- CONNECTS TO: S07 orchestrator (Step 2 — doctor report → teaching intervention → inject via gateway)
- CONNECTS TO: agent_lifecycle.py (prune after 3 failed attempts → fresh session)
- CONNECTS TO: gateway_client.py (inject_content for lessons, prune_agent for failures)
- INDEPENDENT OF: agent awareness (agents don't know about teaching templates — they just see the lesson)
- NOT YET IMPLEMENTED: 3 missing templates (cascading_fix, context_contamination, not_listening), advanced comprehension evaluation (keyword extraction, structural comparison)

## For LightRAG Entity Extraction

Key entities: DiseaseCategory (11 types), Lesson, LessonTemplate, PracticeExercise, LessonOutcome, LessonTracker, LessonRecord.

Key relationships: Doctor TRIGGERS teaching. Teaching ADAPTS lesson from template. Orchestrator INJECTS lesson via gateway. Agent COMPLETES exercise. Evaluator VERIFIES comprehension. Failure ESCALATES to prune. LessonTracker RECORDS history. Challenge analytics FEEDS teaching signals.
