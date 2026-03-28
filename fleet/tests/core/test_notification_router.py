"""Tests for notification routing and classification."""

from datetime import datetime, timedelta

from fleet.core.notification_router import (
    NotificationLevel,
    NotificationRouter,
)


def test_classify_task_done():
    router = NotificationRouter()
    n = router.classify("task_done", "S1-1 completed", "Details")
    assert n.level == NotificationLevel.INFO
    assert "white_check_mark" in n.tags


def test_classify_escalation_is_urgent():
    router = NotificationRouter()
    n = router.classify("escalation", "Needs human", "Agent stuck")
    assert n.level == NotificationLevel.URGENT
    assert "rotating_light" in n.tags


def test_classify_security_alert_critical():
    router = NotificationRouter()
    n = router.classify("security_alert", "CVE found", "Details", severity="critical")
    assert n.level == NotificationLevel.URGENT


def test_classify_security_alert_medium():
    router = NotificationRouter()
    n = router.classify("security_alert", "Minor issue", "Details", severity="medium")
    assert n.level == NotificationLevel.IMPORTANT


def test_classify_blocker_is_important():
    router = NotificationRouter()
    n = router.classify("blocker", "Tests fail", "Details")
    assert n.level == NotificationLevel.IMPORTANT


def test_classify_digest_is_info():
    router = NotificationRouter()
    n = router.classify("digest", "Daily digest", "Summary")
    assert n.level == NotificationLevel.INFO


def test_source_agent_added_to_tags():
    router = NotificationRouter()
    n = router.classify("task_done", "Done", "Details", source_agent="devops")
    assert "devops" in n.tags


def test_dedup_blocks_duplicate():
    router = NotificationRouter(cooldown_seconds=60)
    n = router.classify("task_done", "S1-1 done", "Details")
    now = datetime.now()

    assert router.should_send(n, now) is True
    router.mark_sent(n, now)
    assert router.should_send(n, now) is False


def test_dedup_allows_after_cooldown():
    router = NotificationRouter(cooldown_seconds=60)
    n = router.classify("task_done", "S1-1 done", "Details")
    past = datetime.now() - timedelta(seconds=61)

    router.mark_sent(n, past)
    assert router.should_send(n) is True


def test_dedup_different_events_allowed():
    router = NotificationRouter(cooldown_seconds=60)
    n1 = router.classify("task_done", "S1-1 done", "Details")
    n2 = router.classify("task_done", "S1-2 done", "Details")
    now = datetime.now()

    router.mark_sent(n1, now)
    assert router.should_send(n2, now) is True