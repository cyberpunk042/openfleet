"""Tests for fleet config loader."""

import os
import tempfile
from pathlib import Path

from fleet.infra.config_loader import ConfigLoader


def test_load_projects_from_yaml():
    """Test loading projects from a real config."""
    loader = ConfigLoader()
    projects = loader.load_projects()
    assert "nnrt" in projects
    assert projects["nnrt"].name == "nnrt"


def test_load_url_templates():
    """Test loading URL templates."""
    loader = ConfigLoader()
    templates = loader.load_url_templates()
    assert "github" in templates
    assert "mc" in templates
    assert "pr" in templates["github"]


def test_load_env():
    """Test loading .env file."""
    loader = ConfigLoader()
    env = loader.load_env()
    # .env should have LOCAL_AUTH_TOKEN at minimum
    assert isinstance(env, dict)


def test_fleet_dir_auto_resolve():
    """Test that fleet_dir is correctly resolved from package location."""
    loader = ConfigLoader()
    fleet_dir = loader.fleet_dir
    assert fleet_dir.exists()
    assert (fleet_dir / "config" / "projects.yaml").exists()
    assert (fleet_dir / "fleet" / "__init__.py").exists()


def test_load_tools_md():
    """Test parsing TOOLS.md format."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, dir="/tmp") as f:
        f.write("# TOOLS.md\n\n")
        f.write("- `BASE_URL=http://localhost:8000`\n")
        f.write("- `AUTH_TOKEN=test-token-123`\n")
        f.write("- `BOARD_ID=board-abc`\n")
        tools_dir = os.path.dirname(f.name)
        tools_name = os.path.basename(f.name)

    # ConfigLoader expects TOOLS.md in a directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tools_path = os.path.join(tmpdir, "TOOLS.md")
        with open(tools_path, "w") as f:
            f.write("# TOOLS.md\n\n")
            f.write("- `BASE_URL=http://localhost:8000`\n")
            f.write("- `AUTH_TOKEN=test-token-123`\n")
            f.write("- `BOARD_ID=board-abc`\n")

        loader = ConfigLoader()
        tools = loader.load_tools_md(tmpdir)
        assert tools["BASE_URL"] == "http://localhost:8000"
        assert tools["AUTH_TOKEN"] == "test-token-123"
        assert tools["BOARD_ID"] == "board-abc"


def test_load_tools_md_missing_file():
    """Test TOOLS.md parsing when file doesn't exist."""
    loader = ConfigLoader()
    tools = loader.load_tools_md("/nonexistent/path")
    assert tools == {}