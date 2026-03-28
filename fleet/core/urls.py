"""Fleet URL resolver — generates cross-reference URLs from config.

Pure domain logic. Takes config data (projects, templates) and produces URLs.
No external dependencies. No file I/O (config loading is in infra/).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fleet.core.models import Project


@dataclass
class ResolvedUrls:
    """All URLs for a fleet artifact."""

    task: Optional[str] = None
    board: Optional[str] = None
    pr: Optional[str] = None
    compare: Optional[str] = None
    tree: Optional[str] = None
    commits: list[dict] = None  # [{sha, url}]
    files: list[dict] = None  # [{path, url}]

    def __post_init__(self):
        if self.commits is None:
            self.commits = []
        if self.files is None:
            self.files = []


class UrlResolver:
    """Resolves URLs from projects and templates config."""

    def __init__(
        self,
        projects: dict[str, Project],
        templates: dict,
        board_id: str = "",
    ):
        self._projects = projects
        self._templates = templates
        self._board_id = board_id

    def resolve(
        self,
        *,
        project: str,
        task_id: str = "",
        branch: str = "",
        pr_number: int = 0,
        files: Optional[list[str]] = None,
        commits: Optional[list[str]] = None,
    ) -> ResolvedUrls:
        """Resolve all URLs for a given context."""
        proj = self._projects.get(project)
        if not proj:
            return ResolvedUrls()

        gh = self._templates.get("github", {})
        mc = self._templates.get("mc", {})

        urls = ResolvedUrls()

        # MC URLs
        if task_id and self._board_id:
            urls.task = mc.get("task", "").format(
                board_id=self._board_id, task_id=task_id
            )
            urls.board = mc.get("board", "").format(board_id=self._board_id)

        # GitHub URLs
        if branch:
            urls.compare = gh.get("compare", "").format(
                owner=proj.owner, repo=proj.repo, branch=branch
            )
            urls.tree = gh.get("tree", "").format(
                owner=proj.owner, repo=proj.repo, branch=branch
            )

        if pr_number:
            urls.pr = gh.get("pr", "").format(
                owner=proj.owner, repo=proj.repo, pr_number=pr_number
            )

        # File URLs
        if files and branch:
            file_tmpl = gh.get("file", "")
            urls.files = [
                {
                    "path": f,
                    "url": file_tmpl.format(
                        owner=proj.owner, repo=proj.repo,
                        branch=branch, path=f,
                    ),
                }
                for f in files
            ]

        # Commit URLs
        if commits:
            commit_tmpl = gh.get("commit", "")
            urls.commits = [
                {
                    "sha": sha,
                    "short": sha[:7],
                    "url": commit_tmpl.format(
                        owner=proj.owner, repo=proj.repo, sha=sha,
                    ),
                }
                for sha in commits
            ]

        return urls

    def task_url(self, task_id: str) -> str:
        """Shorthand: get MC task URL."""
        mc = self._templates.get("mc", {})
        return mc.get("task", "").format(
            board_id=self._board_id, task_id=task_id
        )

    def pr_url(self, project: str, pr_number: int) -> str:
        """Shorthand: get GitHub PR URL."""
        proj = self._projects.get(project)
        if not proj:
            return ""
        gh = self._templates.get("github", {})
        return gh.get("pr", "").format(
            owner=proj.owner, repo=proj.repo, pr_number=pr_number
        )

    def file_url(self, project: str, branch: str, path: str) -> str:
        """Shorthand: get GitHub file URL."""
        proj = self._projects.get(project)
        if not proj:
            return ""
        gh = self._templates.get("github", {})
        return gh.get("file", "").format(
            owner=proj.owner, repo=proj.repo, branch=branch, path=path
        )