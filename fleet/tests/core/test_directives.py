"""Tests for fleet.core.directives — PO directive parsing."""

import pytest
from fleet.core.directives import (
    parse_directives,
    format_directive_for_agent,
    Directive,
)


class MockMemoryEntry:
    def __init__(self, id="m1", content="", tags=None, source="human", created_at=None):
        self.id = id
        self.content = content
        self.tags = tags or []
        self.source = source
        self.created_at = created_at


class TestParseDirectives:
    def test_basic_directive(self):
        entries = [
            MockMemoryEntry(
                content="PM: start working on AICP Stage 1",
                tags=["directive", "to:project-manager", "from:human"],
            ),
        ]
        directives = parse_directives(entries)
        assert len(directives) == 1
        assert directives[0].target_agent == "project-manager"
        assert "AICP Stage 1" in directives[0].content

    def test_urgent_directive(self):
        entries = [
            MockMemoryEntry(
                content="All agents: stop and report status",
                tags=["directive", "to:all", "urgent"],
            ),
        ]
        directives = parse_directives(entries)
        assert directives[0].urgent is True
        assert directives[0].target_agent == "all"

    def test_skip_non_directive(self):
        entries = [
            MockMemoryEntry(content="Just a chat message", tags=["chat"]),
            MockMemoryEntry(content="A directive", tags=["directive", "to:pm"]),
        ]
        directives = parse_directives(entries)
        assert len(directives) == 1

    def test_skip_processed(self):
        entries = [
            MockMemoryEntry(
                content="Already handled",
                tags=["directive", "to:pm", "processed"],
            ),
        ]
        directives = parse_directives(entries)
        assert len(directives) == 0

    def test_no_target_agent(self):
        entries = [
            MockMemoryEntry(content="Fleet-wide", tags=["directive"]),
        ]
        directives = parse_directives(entries)
        assert directives[0].target_agent is None

    def test_dict_entries(self):
        entries = [
            {
                "id": "m1",
                "content": "Do the thing",
                "tags": ["directive", "to:architect"],
                "source": "human",
                "created_at": "2026-03-30T12:00:00",
            },
        ]
        directives = parse_directives(entries)
        assert len(directives) == 1
        assert directives[0].target_agent == "architect"


class TestFormatDirective:
    def test_normal(self):
        d = Directive(id="m1", content="Start AICP", target_agent="pm", source="human")
        text = format_directive_for_agent(d)
        assert "DIRECTIVE" in text
        assert "human" in text
        assert "Start AICP" in text

    def test_urgent(self):
        d = Directive(id="m1", content="Stop now", target_agent="all", source="human", urgent=True)
        text = format_directive_for_agent(d)
        assert "URGENT" in text