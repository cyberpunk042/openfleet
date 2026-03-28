"""Tests for agent memory structure initialization."""

import os
import tempfile

from fleet.core.memory_structure import MEMORY_FILES, initialize_agent_memory


def test_initialize_creates_all_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        created = initialize_agent_memory(tmpdir)
        assert created == len(MEMORY_FILES)

        memory_dir = os.path.join(tmpdir, ".claude", "memory")
        for filename in MEMORY_FILES:
            assert os.path.isfile(os.path.join(memory_dir, filename))


def test_initialize_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        first = initialize_agent_memory(tmpdir)
        second = initialize_agent_memory(tmpdir)
        assert first == len(MEMORY_FILES)
        assert second == 0  # Already existed


def test_memory_files_have_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        initialize_agent_memory(tmpdir)
        memory_dir = os.path.join(tmpdir, ".claude", "memory")

        for filename, template in MEMORY_FILES.items():
            filepath = os.path.join(memory_dir, filename)
            with open(filepath) as f:
                content = f.read()
            assert len(content) > 0
            assert content == template