"""Shared fixtures for cross-system integration tests."""

from fleet.core.models import Task, TaskCustomFields, TaskStatus


def make_task(
    task_id: str = "T-100",
    title: str = "Test task",
    story_points: int = 3,
    task_type: str = "task",
    complexity: str = "medium",
    agent_name: str = "worker",
) -> Task:
    """Create a Task with common defaults for integration testing."""
    return Task(
        id=task_id,
        board_id="board-1",
        title=title,
        status=TaskStatus.IN_PROGRESS,
        custom_fields=TaskCustomFields(
            story_points=story_points,
            task_type=task_type,
            complexity=complexity,
            agent_name=agent_name,
        ),
    )


SAMPLE_SESSION_JSON = {
    "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
    "context_window": {
        "context_window_size": 1_000_000,
        "used_percentage": 42,
        "remaining_percentage": 58,
        "total_input_tokens": 150_000,
        "total_output_tokens": 45_000,
        "current_usage": {
            "input_tokens": 8500,
            "output_tokens": 1200,
            "cache_creation_input_tokens": 5000,
            "cache_read_input_tokens": 2000,
        },
    },
    "cost": {
        "total_cost_usd": 0.15,
        "total_duration_ms": 180_000,
        "total_api_duration_ms": 2300,
        "total_lines_added": 256,
        "total_lines_removed": 31,
    },
    "rate_limits": {
        "five_hour": {"used_percentage": 23.5},
        "seven_day": {"used_percentage": 41.2},
    },
    "workspace": {"current_dir": "/home/user/project"},
    "exceeds_200k_tokens": False,
}
