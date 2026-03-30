"""The Doctor — immune system active component.

The doctor observes agents, detects disease, and responds. It is hidden
from agents — they experience consequences but don't see the detection.

The doctor runs as a step in the orchestrator cycle. Each cycle it:
1. Reads all active tasks and agent states
2. Runs detection patterns against each agent's behavior
3. Produces a DoctorReport with findings and interventions
4. The orchestrator uses the report to adjust dispatch and trigger responses

The doctor's toolkit:
- Prune: kill agent session (via gateway sessions.delete)
- Force compact: reduce context (via gateway sessions.compact)
- Trigger teaching: deliver adapted lesson (via teaching system)

The doctor uses:
- Methodology system: knows what SHOULD happen per stage
- Standards library: knows what complete work looks like
- Teaching system: delivers lessons when disease is detected
- Event store: reads agent behavior history
- MC API: reads task state and custom fields
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fleet.core.methodology import Stage
from fleet.core.teaching import DiseaseCategory, LessonOutcome

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Disease severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(str, Enum):
    """Actions the doctor can take."""
    NONE = "none"  # healthy, no action needed
    MONITOR = "monitor"  # flag for increased monitoring
    FORCE_COMPACT = "force_compact"
    TRIGGER_TEACHING = "trigger_teaching"
    PRUNE = "prune"
    ESCALATE_TO_PO = "escalate_to_po"


@dataclass
class Detection:
    """A disease detection finding."""
    agent_name: str
    task_id: str
    disease: DiseaseCategory
    severity: Severity
    signal: str  # what triggered the detection
    evidence: str = ""  # specific evidence
    suggested_action: ResponseAction = ResponseAction.TRIGGER_TEACHING


@dataclass
class Intervention:
    """An action the doctor will take."""
    agent_name: str
    task_id: str
    action: ResponseAction
    reason: str
    disease: Optional[DiseaseCategory] = None
    lesson_context: Optional[dict] = None  # for trigger_teaching


@dataclass
class AgentHealth:
    """Health profile for a single agent."""
    agent_name: str
    correction_count: int = 0  # corrections on current task
    total_lessons: int = 0  # lessons delivered lifetime
    total_prunes: int = 0  # times pruned lifetime
    last_disease: Optional[DiseaseCategory] = None
    last_detection_time: Optional[datetime] = None
    is_in_lesson: bool = False
    is_pruned: bool = False


@dataclass
class DoctorReport:
    """Output of a doctor cycle — consumed by the orchestrator."""
    detections: list[Detection] = field(default_factory=list)
    interventions: list[Intervention] = field(default_factory=list)
    agents_to_skip: list[str] = field(default_factory=list)
    tasks_to_block: list[str] = field(default_factory=list)
    health_profiles: dict[str, AgentHealth] = field(default_factory=dict)

    @property
    def has_findings(self) -> bool:
        return len(self.detections) > 0

    @property
    def has_interventions(self) -> bool:
        return len(self.interventions) > 0


# ─── Detection Functions ────────────────────────────────────────────────


def detect_protocol_violation(
    agent_name: str,
    task_id: str,
    task_stage: Optional[str],
    tool_calls: list[str],
) -> Optional[Detection]:
    """Detect if agent violated the methodology protocol for its stage.

    Args:
        agent_name: The agent being checked.
        task_id: The task being worked on.
        task_stage: Current methodology stage.
        tool_calls: MCP tools the agent called recently.
    """
    if not task_stage:
        return None

    # Tools that indicate work (code production)
    work_tools = {"fleet_commit", "fleet_task_complete"}
    # Stages where work tools are not allowed
    non_work_stages = {
        Stage.CONVERSATION.value,
        Stage.ANALYSIS.value,
        Stage.INVESTIGATION.value,
    }

    if task_stage in non_work_stages:
        violations = work_tools.intersection(set(tool_calls))
        if violations:
            return Detection(
                agent_name=agent_name,
                task_id=task_id,
                disease=DiseaseCategory.PROTOCOL_VIOLATION,
                severity=Severity.MEDIUM,
                signal=f"Work tools called during {task_stage} stage",
                evidence=f"Tools: {', '.join(violations)}",
                suggested_action=ResponseAction.TRIGGER_TEACHING,
            )

    return None


def detect_laziness(
    agent_name: str,
    task_id: str,
    story_points: Optional[int],
    time_to_complete_minutes: Optional[float],
    acceptance_criteria_total: int = 0,
    acceptance_criteria_met: int = 0,
) -> Optional[Detection]:
    """Detect if agent did partial or lazy work.

    Signals:
    - Completed very fast relative to story points
    - Acceptance criteria partially met
    """
    # Fast completion relative to complexity
    if story_points and time_to_complete_minutes is not None:
        # Rough heuristic: < 2 minutes per story point is suspicious
        expected_min = story_points * 2
        if time_to_complete_minutes < expected_min and story_points >= 3:
            return Detection(
                agent_name=agent_name,
                task_id=task_id,
                disease=DiseaseCategory.LAZINESS,
                severity=Severity.MEDIUM,
                signal="Task completed suspiciously fast",
                evidence=(
                    f"{time_to_complete_minutes:.0f}min for {story_points}SP "
                    f"(expected >={expected_min}min)"
                ),
                suggested_action=ResponseAction.TRIGGER_TEACHING,
            )

    # Partial acceptance criteria
    if acceptance_criteria_total > 0 and acceptance_criteria_met < acceptance_criteria_total:
        ratio = acceptance_criteria_met / acceptance_criteria_total
        if ratio < 0.8:
            return Detection(
                agent_name=agent_name,
                task_id=task_id,
                disease=DiseaseCategory.LAZINESS,
                severity=Severity.MEDIUM if ratio > 0.5 else Severity.HIGH,
                signal="Acceptance criteria partially met",
                evidence=f"{acceptance_criteria_met}/{acceptance_criteria_total} criteria met",
                suggested_action=ResponseAction.TRIGGER_TEACHING,
            )

    return None


def detect_stuck(
    agent_name: str,
    task_id: str,
    minutes_since_last_activity: Optional[float],
    has_commits: bool = False,
    stuck_threshold_minutes: float = 60,
) -> Optional[Detection]:
    """Detect if agent is stuck/spinning with no progress."""
    if minutes_since_last_activity is None:
        return None

    if minutes_since_last_activity > stuck_threshold_minutes and not has_commits:
        return Detection(
            agent_name=agent_name,
            task_id=task_id,
            disease=DiseaseCategory.DEVIATION,  # Using deviation as closest match
            severity=Severity.LOW,
            signal="Agent appears stuck — no progress",
            evidence=f"No activity for {minutes_since_last_activity:.0f} minutes",
            suggested_action=ResponseAction.FORCE_COMPACT,
        )

    return None


def detect_correction_threshold(
    agent_name: str,
    task_id: str,
    correction_count: int,
    threshold: int = 3,
) -> Optional[Detection]:
    """Detect if agent has been corrected too many times on the same task.

    From devops-control-plane: "3 corrections = corrupted. Your MODEL
    is wrong, not your detail."
    """
    if correction_count >= threshold:
        return Detection(
            agent_name=agent_name,
            task_id=task_id,
            disease=DiseaseCategory.CONFIDENT_BUT_WRONG,
            severity=Severity.HIGH,
            signal=f"Agent corrected {correction_count} times (threshold: {threshold})",
            evidence=f"Model is likely wrong, not just detail",
            suggested_action=ResponseAction.PRUNE,
        )

    return None


# ─── Response Decision ──────────────────────────────────────────────────


def decide_response(
    detection: Detection,
    agent_health: AgentHealth,
) -> ResponseAction:
    """Decide the appropriate response for a detection.

    Takes into account the disease, severity, and agent history.
    """
    # Already in a lesson — don't pile on
    if agent_health.is_in_lesson:
        return ResponseAction.NONE

    # 3+ corrections → prune (devops-control-plane three-strike rule)
    if agent_health.correction_count >= 3:
        return ResponseAction.PRUNE

    # Critical severity → prune directly
    if detection.severity == Severity.CRITICAL:
        return ResponseAction.PRUNE

    # High severity + repeat offender → prune
    if detection.severity == Severity.HIGH and agent_health.total_lessons >= 2:
        return ResponseAction.PRUNE

    # Stuck → compact (not sick, just overloaded)
    if detection.suggested_action == ResponseAction.FORCE_COMPACT:
        return ResponseAction.FORCE_COMPACT

    # Default for medium/low → teach
    if detection.severity in (Severity.MEDIUM, Severity.LOW):
        return ResponseAction.TRIGGER_TEACHING

    # High severity, first time → teach
    if detection.severity == Severity.HIGH and agent_health.total_lessons < 2:
        return ResponseAction.TRIGGER_TEACHING

    return detection.suggested_action


def build_intervention(
    detection: Detection,
    action: ResponseAction,
    lesson_context: Optional[dict] = None,
) -> Intervention:
    """Build an intervention from a detection and decided action."""
    return Intervention(
        agent_name=detection.agent_name,
        task_id=detection.task_id,
        action=action,
        reason=f"{detection.disease.value}: {detection.signal}",
        disease=detection.disease,
        lesson_context=lesson_context,
    )


# ─── Doctor Cycle ───────────────────────────────────────────────────────


async def run_doctor_cycle(
    tasks: list,
    agents: list,
    tool_call_history: dict[str, list[str]],
    health_profiles: dict[str, AgentHealth],
    config: Optional[dict] = None,
) -> DoctorReport:
    """Run one doctor observation cycle.

    This is called from the orchestrator every 30s. It checks all active
    agents and tasks for disease signals.

    Args:
        tasks: All tasks from the board.
        agents: All agents.
        tool_call_history: Recent tool calls per agent {agent_name: [tool_names]}.
        health_profiles: Persistent health profiles per agent.
        config: Doctor configuration (thresholds, etc.)

    Returns:
        DoctorReport with detections, interventions, and dispatch guidance.
    """
    report = DoctorReport(health_profiles=health_profiles)
    cfg = config or {}
    correction_threshold = cfg.get("correction_threshold", 3)
    stuck_threshold = cfg.get("stuck_threshold_minutes", 60)

    for task in tasks:
        if task.status.value not in ("inbox", "in_progress"):
            continue

        agent_name = task.custom_fields.agent_name
        if not agent_name:
            continue

        # Get or create health profile
        if agent_name not in health_profiles:
            health_profiles[agent_name] = AgentHealth(agent_name=agent_name)
        health = health_profiles[agent_name]

        # Skip agents already being handled
        if health.is_in_lesson or health.is_pruned:
            report.agents_to_skip.append(agent_name)
            continue

        task_stage = task.custom_fields.task_stage
        tool_calls = tool_call_history.get(agent_name, [])

        # ── Run detection patterns ──────────────────────────────

        detections: list[Detection] = []

        # Protocol violation
        d = detect_protocol_violation(
            agent_name, task.id, task_stage, tool_calls
        )
        if d:
            detections.append(d)

        # Correction threshold
        d = detect_correction_threshold(
            agent_name, task.id, health.correction_count, correction_threshold
        )
        if d:
            detections.append(d)

        # ── Process detections ──────────────────────────────────

        for detection in detections:
            report.detections.append(detection)

            action = decide_response(detection, health)
            if action == ResponseAction.NONE:
                continue

            # Build lesson context for teaching
            lesson_ctx = None
            if action == ResponseAction.TRIGGER_TEACHING:
                lesson_ctx = {
                    "requirement_verbatim": task.custom_fields.requirement_verbatim or "",
                    "current_stage": task_stage or "unknown",
                    "agent_plan": "",  # would come from fleet_task_accept
                    "what_agent_did": ", ".join(tool_calls) if tool_calls else "unknown",
                }

            intervention = build_intervention(detection, action, lesson_ctx)
            report.interventions.append(intervention)

            # Update health profile
            health.last_disease = detection.disease
            health.last_detection_time = datetime.now()

            if action == ResponseAction.PRUNE:
                health.is_pruned = True
                health.total_prunes += 1
                report.agents_to_skip.append(agent_name)
                report.tasks_to_block.append(task.id)
            elif action == ResponseAction.TRIGGER_TEACHING:
                health.is_in_lesson = True
                health.total_lessons += 1
                report.agents_to_skip.append(agent_name)

    return report