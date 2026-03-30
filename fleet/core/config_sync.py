"""Config sync — keep IaC YAML configs in sync with live Plane state.

When the Plane watcher detects changes, this module updates the
DSPD config YAML files so that a rebuild recovers to current state.
Optionally commits changes to git.

> "We will also need to make it so that we can keep the IaC definition
> in sync as the plane evolve as the agent works, so that if we restart
> it will pick up where we left approximately or even perfectly."

This runs as part of the monitor daemon (300s cycle).
Not every change needs a git commit — batch changes and commit
periodically (e.g., every 5 minutes if changes detected).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigSync:
    """Syncs live Plane state to DSPD config files."""

    def __init__(self) -> None:
        fleet_dir = os.environ.get("FLEET_DIR", ".")
        self._fleet_dir = Path(fleet_dir)
        self._dspd_dir = self._fleet_dir.parent / "devops-solution-product-development"
        self._last_sync = ""
        self._changes_pending = False

    def export_and_commit(self) -> dict:
        """Export Plane state and commit if changes detected.

        Returns dict with export results and git status.
        """
        result = {"exported": False, "committed": False, "error": ""}

        if not self._dspd_dir.exists():
            result["error"] = "DSPD directory not found"
            return result

        export_script = self._dspd_dir / "scripts" / "plane_export.py"
        if not export_script.exists():
            result["error"] = "plane-export-state.sh not found"
            return result

        # Run export
        try:
            env = os.environ.copy()
            env["PROJECT_DIR"] = str(self._dspd_dir)
            # Source .plane-config
            plane_config = self._dspd_dir / ".plane-config"
            if plane_config.exists():
                with open(plane_config) as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, val = line.split("=", 1)
                            env[key] = val

            export_py = self._dspd_dir / "scripts" / "plane_export.py"
            proc = subprocess.run(
                ["python3", str(export_py)],
                cwd=str(self._dspd_dir),
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            if proc.returncode == 0:
                result["exported"] = True
            else:
                result["error"] = proc.stderr[:200]
                return result
        except Exception as e:
            result["error"] = str(e)
            return result

        # Check git status in DSPD repo
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self._dspd_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if status.stdout.strip():
                # Changes detected — commit
                files_changed = [
                    line.split()[-1]
                    for line in status.stdout.strip().split("\n")
                    if line.strip()
                ]

                # Commit config files + state file when meaningful changes exist
                config_files = [
                    f for f in files_changed
                    if f.startswith("config/")
                    or f.endswith(".yaml")
                    or f.endswith(".yml")
                ]
                state_files = [f for f in files_changed if ".plane-state" in f]

                # Check if state file has meaningful changes (not just timestamp)
                if state_files and not config_files:
                    try:
                        import subprocess as _sp
                        diff = _sp.run(
                            ["git", "diff", ".plane-state.json"],
                            cwd=str(self._dspd_dir),
                            capture_output=True, text=True, timeout=5,
                        )
                        diff_lines = [
                            l for l in diff.stdout.split("\n")
                            if l.startswith("+") and not l.startswith("+++")
                            and "exported_at" not in l
                        ]
                        # If there are changes beyond just the timestamp
                        if len(diff_lines) > 0:
                            config_files = state_files
                    except Exception:
                        pass
                else:
                    config_files.extend(state_files)

                if config_files:
                    subprocess.run(
                        ["git", "add"] + config_files,
                        cwd=str(self._dspd_dir),
                        timeout=10,
                    )
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    subprocess.run(
                        ["git", "commit", "-m",
                         f"sync: Plane state export ({ts})\n\n"
                         f"Auto-synced by fleet config sync daemon.\n"
                         f"Files: {', '.join(config_files[:5])}\n\n"
                         f"Co-Authored-By: Fleet Config Sync <fleet@openclaw.ai>"],
                        cwd=str(self._dspd_dir),
                        capture_output=True,
                        timeout=10,
                    )
                    result["committed"] = True
                    result["files"] = config_files

                    # Push (best effort)
                    subprocess.run(
                        ["git", "push", "origin", "main"],
                        cwd=str(self._dspd_dir),
                        capture_output=True,
                        timeout=30,
                    )

        except Exception as e:
            result["error"] = f"git: {e}"

        return result