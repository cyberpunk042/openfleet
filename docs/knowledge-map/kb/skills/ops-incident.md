# ops-incident

**Type:** Skill (AICP)
**Location:** devops-expert-local-ai/.claude/skills/ops-incident/SKILL.md
**Invocation:** /ops-incident
**Effort:** max (highest — incidents demand maximum reasoning)
**Allowed tools:** Read, Write, Edit, Bash, Glob, Grep

## Purpose

Incident response: gather diagnostics, identify root cause, propose fix, generate incident report with timeline. Priorities in order: (1) restore service, (2) understand why, (3) prevent recurrence. Document everything.

## Process

1. **Gather:** logs, error messages, metrics, recent changes (`git log`)
2. **Identify:** what broke, when, what changed before it broke
3. **Root cause analysis:** trace from symptom to cause
4. **Propose fix:** specific code/config changes (not vague — actionable)
5. **Generate incident report:** timeline, root cause, fix applied, prevention measures

## Rules (non-negotiable)

- First priority: RESTORE SERVICE (fix before understanding)
- Second priority: understand WHY
- Third priority: prevent recurrence
- Document EVERYTHING, even if it seems obvious

## Output

Incident report with: timeline (what happened when), root cause (traced from symptom), fix (specific changes), prevention (what to change so this can't recur).

## Assigned Roles

| Role | Priority | Why |
|------|----------|-----|
| DevOps | ESSENTIAL | Primary incident responder for infrastructure |
| Engineer | ESSENTIAL | Primary incident responder for application |
| DevSecOps | ESSENTIAL | Security incidents — triage, assess, mitigate |

## Methodology Stages

| Stage | Usage |
|-------|-------|
| work | Active incident response (immediate) |
| investigation | Post-incident root cause analysis |

## Relationships

- TRIGGERED BY: fleet_alert (severity critical/high → incident response)
- TRIGGERED BY: storm system (STORM/CRITICAL severity → incident)
- USES: /debug command (systematic troubleshooting during investigation)
- USES: systematic-debugging skill (Superpowers — 4-phase root cause, if adopted)
- FOLLOWED BY: ops-deploy (deploy the fix)
- FOLLOWED BY: pm-retrospective (post-incident review)
- PRODUCES: incident report (timeline, root cause, prevention)
- CONNECTS TO: incident-cycle composite skill (incident → plan fix → implement → test → deploy → retro)
- CONNECTS TO: storm_monitor.py (incident_report.py generates fleet-specific incident reports)
- CONNECTS TO: fleet_escalate (escalate to PO if incident is beyond agent capability)
- CONNECTS TO: fleet_notify_human (notify PO of incident status)
- CONNECTS TO: crisis-management cycle_phase (only fleet-ops + devsecops active during crisis)
- CONNECTS TO: §50 crisis response playbook (5 documented failure modes)
- HISTORICAL: the March 2026 catastrophe was an incident that led to building storm prevention
