"""Notification routing — classify events and route to appropriate channels.

Determines whether an event is info/important/urgent and routes to:
- ntfy (all events, classified by topic)
- IRC (all events, existing behavior)
- Windows toast (urgent only)

Handles deduplication to prevent notification spam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class NotificationLevel(str, Enum):
    """Notification priority level — drives routing."""

    INFO = "info"             # ntfy progress only — quiet, in history
    IMPORTANT = "important"   # ntfy review — prominent notification
    URGENT = "urgent"         # ntfy alert + Windows toast — immediate attention


# Admonition tags for visual classification in ntfy
ADMONITION_TAGS = {
    "task_done": ["white_check_mark"],
    "pr_merged": ["rocket"],
    "sprint_milestone": ["tada", "sprint"],
    "sprint_complete": ["trophy", "sprint"],
    "review_needed": ["eyes", "review"],
    "escalation": ["rotating_light", "escalation"],
    "security_alert": ["lock", "security"],
    "agent_stuck": ["warning", "agent"],
    "agent_offline": ["red_circle", "agent"],
    "blocker": ["no_entry", "blocker"],
    "suggestion": ["bulb", "suggestion"],
    "digest": ["newspaper", "daily"],
    "infrastructure": ["wrench", "infra"],
}


@dataclass
class Notification:
    """A classified notification ready for routing."""

    title: str
    message: str
    level: NotificationLevel
    event_type: str = ""        # task_done, pr_merged, escalation, etc.
    source_agent: str = ""      # Who generated this
    click_url: str = ""         # URL to open on click
    tags: list[str] = field(default_factory=list)
    dedup_key: str = ""         # For deduplication (empty = no dedup)


class NotificationRouter:
    """Routes notifications based on event type and classification rules.

    Also handles deduplication — won't send the same notification twice
    within a cooldown period.
    """

    def __init__(self, cooldown_seconds: int = 300) -> None:
        self._cooldown = cooldown_seconds
        self._sent: dict[str, datetime] = {}  # dedup_key → last sent

    def classify(
        self,
        event_type: str,
        title: str,
        message: str,
        source_agent: str = "",
        url: str = "",
        severity: str = "",
    ) -> Notification:
        """Classify an event into a notification with proper level and tags.

        Args:
            event_type: Type of event (task_done, escalation, security_alert, etc.)
            title: Notification title
            message: Body text
            source_agent: Agent that generated the event
            url: Click URL
            severity: For alerts — "critical", "high", "medium", "low"
        """
        level = self._determine_level(event_type, severity)
        tags = ADMONITION_TAGS.get(event_type, []).copy()
        if source_agent:
            tags.append(source_agent)

        return Notification(
            title=title,
            message=message,
            level=level,
            event_type=event_type,
            source_agent=source_agent,
            click_url=url,
            tags=tags,
            dedup_key=f"{event_type}:{title[:50]}",
        )

    def should_send(self, notification: Notification, now: Optional[datetime] = None) -> bool:
        """Check if notification should be sent (dedup + cooldown)."""
        if not notification.dedup_key:
            return True

        now = now or datetime.now()
        last_sent = self._sent.get(notification.dedup_key)
        if last_sent and (now - last_sent).total_seconds() < self._cooldown:
            return False

        return True

    def mark_sent(self, notification: Notification, now: Optional[datetime] = None) -> None:
        """Record that a notification was sent (for dedup tracking)."""
        if notification.dedup_key:
            self._sent[notification.dedup_key] = now or datetime.now()

        # Cleanup old entries (keep last 1000)
        if len(self._sent) > 1000:
            cutoff = (now or datetime.now()) - timedelta(hours=24)
            self._sent = {
                k: v for k, v in self._sent.items()
                if v > cutoff
            }

    def _determine_level(self, event_type: str, severity: str) -> NotificationLevel:
        """Determine notification level from event type and severity."""
        # Urgent events — need immediate human attention
        urgent_events = {
            "escalation",
            "infrastructure",
        }
        if event_type in urgent_events:
            return NotificationLevel.URGENT

        # Severity-based for alerts
        if severity in ("critical", "high"):
            return NotificationLevel.URGENT
        if severity == "medium":
            return NotificationLevel.IMPORTANT

        # Important events — human should see soon
        important_events = {
            "review_needed",
            "blocker",
            "agent_offline",
            "agent_stuck",
        }
        if event_type in important_events:
            return NotificationLevel.IMPORTANT

        # Info events — in ntfy history, no interruption
        return NotificationLevel.INFO