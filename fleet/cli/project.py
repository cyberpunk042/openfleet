"""Fleet project management — add, list, check projects.

Usage:
  python -m fleet project add <name> <path> [--desc "..."]
  python -m fleet project list
  python -m fleet project check <name>
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from fleet.infra.config_loader import ConfigLoader
from fleet.infra.gh_client import GHClient


async def _add_project(name: str, local_path: str, description: str = "") -> int:
    """Add a project to the fleet — handles git init, remote creation, push."""
    gh = GHClient()
    loader = ConfigLoader()
    fleet_dir = str(loader.fleet_dir)
    path = Path(local_path).resolve()

    print(f"Adding project: {name}")
    print(f"  Path: {path}")

    # 1. Check folder exists
    if not path.exists():
        print(f"  Creating directory...")
        path.mkdir(parents=True, exist_ok=True)

    # 2. Check git
    if not (path / ".git").exists():
        print(f"  Initializing git...")
        ok, _ = await gh._run(["git", "init", "-b", "main"], cwd=str(path))
        if not ok:
            print("  ERROR: git init failed")
            return 1

    # 3. Check if there's anything to commit
    _, status = await gh._run(["git", "status", "--porcelain"], cwd=str(path))
    if status.strip():
        print(f"  Staging uncommitted files...")
        await gh._run(["git", "add", "-A"], cwd=str(path))
        await gh._run(["git", "commit", "-m", f"feat: initial {name} project"], cwd=str(path))

    # 4. Check remote
    _, remotes = await gh._run(["git", "remote", "-v"], cwd=str(path))
    has_remote = "origin" in remotes

    if not has_remote:
        print(f"  Creating GitHub repo...")
        # Derive owner from gh auth
        ok, owner = await gh._run(["gh", "api", "user", "--jq", ".login"])
        owner = owner.strip() if ok else "cyberpunk042"

        repo_name = path.name  # use folder name as repo name
        ok, output = await gh._run([
            "gh", "repo", "create", f"{owner}/{repo_name}",
            "--public", "--source", str(path), "--push",
        ], cwd=str(path))

        if ok:
            print(f"  GitHub repo: https://github.com/{owner}/{repo_name}")
        else:
            # Repo might already exist, just add remote
            print(f"  Adding remote...")
            await gh._run([
                "git", "remote", "add", "origin",
                f"https://github.com/{owner}/{repo_name}.git",
            ], cwd=str(path))
            await gh._run(["git", "push", "-u", "origin", "main"], cwd=str(path))
    else:
        # Remote exists, check if pushed
        _, push_status = await gh._run(
            ["git", "log", "--oneline", "origin/main..HEAD"], cwd=str(path)
        )
        if push_status.strip():
            print(f"  Pushing unpushed commits...")
            await gh._run(["git", "push", "origin", "main"], cwd=str(path))
        print(f"  Remote: already configured")

    # 5. Get GitHub owner/repo from remote
    _, remote_url = await gh._run(["git", "remote", "get-url", "origin"], cwd=str(path))
    remote_url = remote_url.strip()
    owner_repo = ""
    if "github.com" in remote_url:
        parts = remote_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        owner_repo = parts

    # 6. Update fleet config
    import yaml
    projects_path = os.path.join(fleet_dir, "config", "projects.yaml")
    with open(projects_path) as f:
        cfg = yaml.safe_load(f)

    if name not in cfg.get("projects", {}):
        cfg.setdefault("projects", {})[name] = {
            "description": description or f"{name} project",
            "repo": f"https://github.com/{owner_repo}" if owner_repo else "",
        }
        with open(projects_path, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
        print(f"  Added to config/projects.yaml")
    else:
        print(f"  Already in config/projects.yaml")

    # 7. Update URL templates
    url_path = os.path.join(fleet_dir, "config", "url-templates.yaml")
    with open(url_path) as f:
        url_cfg = yaml.safe_load(f)

    if owner_repo and name not in url_cfg.get("projects", {}):
        owner, repo = owner_repo.split("/", 1) if "/" in owner_repo else ("", "")
        url_cfg.setdefault("projects", {})[name] = {
            "owner": owner,
            "repo": repo,
        }
        with open(url_path, "w") as f:
            yaml.dump(url_cfg, f, default_flow_style=False, sort_keys=False)
        print(f"  Added to config/url-templates.yaml")

    print(f"\n  Project '{name}' ready.")
    print(f"  Dispatch: fleet create \"task\" --agent X --project {name} --dispatch")
    return 0


async def _list_projects() -> int:
    """List all registered projects."""
    loader = ConfigLoader()
    projects = loader.load_projects()
    print(f"Projects ({len(projects)}):")
    for name, proj in projects.items():
        local = " (local)" if proj.local else ""
        gh = f" → https://github.com/{proj.owner}/{proj.repo}" if proj.owner else ""
        print(f"  {name:25s} {proj.description[:40]}{local}{gh}")
    return 0


async def _check_project(name: str) -> int:
    """Check project state: git, remote, pushed."""
    loader = ConfigLoader()
    gh = GHClient()
    fleet_dir = str(loader.fleet_dir)
    projects = loader.load_projects()

    proj = projects.get(name)
    if not proj:
        print(f"Project '{name}' not found")
        return 1

    print(f"Project: {name}")
    print(f"  Description: {proj.description}")
    print(f"  GitHub: https://github.com/{proj.owner}/{proj.repo}" if proj.owner else "  No GitHub")

    # Check clone
    clone_path = os.path.join(fleet_dir, "projects", name)
    if os.path.isdir(clone_path):
        print(f"  Clone: {clone_path}")
        _, branch = await gh._run(["git", "branch", "--show-current"], cwd=clone_path)
        print(f"  Branch: {branch.strip()}")
    else:
        print(f"  Clone: not cloned")

    # Check worktrees
    wt_dir = os.path.join(clone_path, "worktrees")
    if os.path.isdir(wt_dir):
        wts = os.listdir(wt_dir)
        print(f"  Worktrees: {len(wts)}")
        for wt in wts:
            print(f"    {wt}")
    else:
        print(f"  Worktrees: none")

    return 0


def run_project(args: list[str] | None = None) -> int:
    """Entry point for fleet project."""
    argv = args if args is not None else sys.argv[2:]

    if not argv:
        print("Usage: fleet project <add|list|check> [args]")
        return 1

    action = argv[0]

    if action == "list":
        return asyncio.run(_list_projects())

    elif action == "check" and len(argv) > 1:
        return asyncio.run(_check_project(argv[1]))

    elif action == "add" and len(argv) >= 3:
        name = argv[1]
        path = argv[2]
        desc = ""
        if "--desc" in argv:
            idx = argv.index("--desc")
            if idx + 1 < len(argv):
                desc = argv[idx + 1]
        return asyncio.run(_add_project(name, path, desc))

    else:
        print("Usage:")
        print("  fleet project add <name> <path> [--desc '...']")
        print("  fleet project list")
        print("  fleet project check <name>")
        return 1