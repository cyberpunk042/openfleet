"""Transpose layer — bidirectional object ↔ rich HTML.

The agent works with structured objects (dicts). Plane shows rich HTML.
This module converts between the two worlds.

Object → HTML: render a structured artifact object as rich HTML for Plane
HTML → Object: parse rich HTML with markers back into the structured object

Uses HTML comment markers to make rich HTML machine-parseable:
  <!-- fleet:artifact:start type="analysis_document" -->
  <!-- fleet:field:title -->
  <!-- fleet:artifact:end -->

The agent NEVER touches HTML. Tools call this module.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from typing import Any, Optional


# ─── Markers ────────────────────────────────────────────────────────────

ARTIFACT_START = '<!-- fleet:artifact:start type="{type}" -->'
ARTIFACT_END = '<!-- fleet:artifact:end -->'
FIELD_MARKER = '<!-- fleet:field:{name} -->'
ARTIFACT_DATA = '<!-- fleet:data:{data} -->'

# ─── Object → HTML Renderers ───────────────────────────────────────────


def _render_field(name: str, content_html: str) -> str:
    return f'{FIELD_MARKER.format(name=name)}\n{content_html}'


def _escape(text: str) -> str:
    return html.escape(str(text)) if text else ""


def _render_list(items: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    li = "".join(f"<li>{_escape(item)}</li>" for item in items)
    return f"<{tag}>{li}</{tag}>"


def _render_code_list(items: list[str]) -> str:
    li = "".join(f"<li><code>{_escape(item)}</code></li>" for item in items)
    return f"<ul>{li}</ul>"


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{_escape(h)}</th>" for h in headers)
    thead = f"<thead><tr>{th}</tr></thead>"
    body_rows = ""
    for row in rows:
        td = "".join(f"<td>{_escape(cell)}</td>" for cell in row)
        body_rows += f"<tr>{td}</tr>"
    return f"<table>{thead}<tbody>{body_rows}</tbody></table>"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ─── Artifact Renderers ────────────────────────────────────────────────

_RENDERERS: dict[str, callable] = {}


def _register_renderer(artifact_type: str):
    def decorator(fn):
        _RENDERERS[artifact_type] = fn
        return fn
    return decorator


@_register_renderer("analysis_document")
def _render_analysis(obj: dict) -> str:
    parts = [f"<h2>Analysis: {_escape(obj.get('title', ''))}</h2>"]

    if obj.get("scope"):
        parts.append(_render_field("scope",
            f"<p><strong>Scope:</strong> {_escape(obj['scope'])}</p>"))

    if obj.get("current_state"):
        parts.append(_render_field("current_state",
            f"<p><strong>Current State:</strong> {_escape(obj['current_state'])}</p>"))

    findings = obj.get("findings", [])
    if findings:
        parts.append(_render_field("findings", "<h3>Findings</h3>"))
        for i, f in enumerate(findings):
            finding_html = f"<p><strong>{_escape(f.get('title', ''))}</strong></p>"
            finding_html += f"<p>{_escape(f.get('finding', ''))}</p>"
            if f.get("files"):
                finding_html += f"<p>Files: {', '.join(f'<code>{_escape(fp)}</code>' for fp in f['files'])}</p>"
            if f.get("implications"):
                finding_html += f"<p><em>Implications:</em> {_escape(f['implications'])}</p>"
            parts.append(finding_html)

    if obj.get("open_questions"):
        parts.append(_render_field("open_questions",
            "<h3>Open Questions</h3>" + _render_list(obj["open_questions"])))

    parts.append(f"<p><em>Analysis stage — {_timestamp()}</em></p>")
    return "\n".join(parts)


@_register_renderer("investigation_document")
def _render_investigation(obj: dict) -> str:
    parts = [f"<h2>Investigation: {_escape(obj.get('title', ''))}</h2>"]

    if obj.get("scope"):
        parts.append(_render_field("scope",
            f"<p><strong>Scope:</strong> {_escape(obj['scope'])}</p>"))

    if obj.get("findings"):
        parts.append(_render_field("findings",
            f"<h3>Findings</h3><p>{_escape(obj['findings'])}</p>"))

    options = obj.get("options", [])
    if options:
        rows = [[o.get("name", ""), o.get("pros", ""), o.get("cons", "")] for o in options]
        parts.append(_render_field("options",
            "<h3>Options</h3>" + _render_table(["Option", "Pros", "Cons"], rows)))

    if obj.get("sources"):
        parts.append(_render_field("sources",
            "<h3>Sources</h3>" + _render_list(obj["sources"])))

    if obj.get("recommendations"):
        parts.append(_render_field("recommendations",
            f"<h3>Recommendations</h3><blockquote>{_escape(obj['recommendations'])}</blockquote>"))

    parts.append(f"<p><em>Investigation stage — {_timestamp()}</em></p>")
    return "\n".join(parts)


@_register_renderer("plan")
def _render_plan(obj: dict) -> str:
    parts = [f"<h2>Plan: {_escape(obj.get('title', ''))}</h2>"]

    if obj.get("requirement_reference"):
        parts.append(_render_field("requirement_reference",
            f"<blockquote><strong>Verbatim Requirement:</strong><br/>"
            f"{_escape(obj['requirement_reference'])}</blockquote>"))

    if obj.get("approach"):
        parts.append(_render_field("approach",
            f"<p><strong>Approach:</strong> {_escape(obj['approach'])}</p>"))

    if obj.get("target_files"):
        parts.append(_render_field("target_files",
            "<p><strong>Target Files:</strong></p>" + _render_code_list(obj["target_files"])))

    if obj.get("steps"):
        parts.append(_render_field("steps",
            "<h3>Steps</h3>" + _render_list(obj["steps"], ordered=True)))

    if obj.get("acceptance_criteria_mapping"):
        mapping = obj["acceptance_criteria_mapping"]
        rows = [[k, v] for k, v in mapping.items()]
        parts.append(_render_field("acceptance_criteria_mapping",
            "<h3>Acceptance Criteria</h3>" + _render_table(["Criterion", "How Met"], rows)))

    parts.append(f"<p><em>Reasoning stage — {_timestamp()}</em></p>")
    return "\n".join(parts)


@_register_renderer("progress_update")
def _render_progress(obj: dict) -> str:
    parts = ["<h3>Progress Update</h3>"]
    parts.append(f"<p>{_escape(obj.get('what_was_done', ''))}</p>")

    if obj.get("what_is_next"):
        parts.append(f"<p><strong>Next:</strong> {_escape(obj['what_is_next'])}</p>")
    if obj.get("blockers"):
        parts.append(f"<p><strong>Blockers:</strong> {_escape(obj['blockers'])}</p>")

    rb = obj.get("readiness_before", 0)
    ra = obj.get("readiness_after", 0)
    if ra > rb:
        parts.append(f"<p><strong>Readiness:</strong> {rb}% → {ra}%</p>")

    parts.append(f"<p><em>{_timestamp()}</em></p>")
    return "\n".join(parts)


@_register_renderer("bug")
def _render_bug(obj: dict) -> str:
    parts = [f"<h2>Bug: {_escape(obj.get('title', ''))}</h2>"]

    if obj.get("steps_to_reproduce"):
        steps = obj["steps_to_reproduce"]
        if isinstance(steps, list):
            parts.append(_render_field("steps_to_reproduce",
                "<h3>Steps to Reproduce</h3>" + _render_list(steps, ordered=True)))
        else:
            parts.append(_render_field("steps_to_reproduce",
                f"<h3>Steps to Reproduce</h3><p>{_escape(steps)}</p>"))

    if obj.get("expected_behavior"):
        parts.append(_render_field("expected_behavior",
            f"<p><strong>Expected:</strong> {_escape(obj['expected_behavior'])}</p>"))
    if obj.get("actual_behavior"):
        parts.append(_render_field("actual_behavior",
            f"<p><strong>Actual:</strong> {_escape(obj['actual_behavior'])}</p>"))
    if obj.get("environment"):
        parts.append(_render_field("environment",
            f"<p><strong>Environment:</strong> {_escape(obj['environment'])}</p>"))
    if obj.get("impact"):
        parts.append(_render_field("impact",
            f"<p><strong>Impact:</strong> {_escape(obj['impact'])}</p>"))
    if obj.get("evidence"):
        parts.append(_render_field("evidence",
            f"<h3>Evidence</h3><pre><code>{_escape(obj['evidence'])}</code></pre>"))

    return "\n".join(parts)


@_register_renderer("completion_claim")
def _render_completion(obj: dict) -> str:
    parts = ["<h2>Completion Claim</h2>"]

    if obj.get("pr_url"):
        parts.append(f'<p><strong>PR:</strong> <a href="{_escape(obj["pr_url"])}">{_escape(obj["pr_url"])}</a></p>')

    if obj.get("summary"):
        parts.append(f"<p>{_escape(obj['summary'])}</p>")

    checks = obj.get("acceptance_criteria_check", [])
    if checks:
        rows = []
        for c in checks:
            met = "✓" if c.get("met") else "✗"
            rows.append([c.get("criterion", ""), met, c.get("evidence", "")])
        parts.append(_render_field("acceptance_criteria_check",
            "<h3>Acceptance Criteria</h3>" + _render_table(["Criterion", "Met", "Evidence"], rows)))

    if obj.get("files_changed"):
        parts.append(_render_field("files_changed",
            "<p><strong>Files Changed:</strong></p>" + _render_code_list(obj["files_changed"])))

    parts.append(f"<p><em>{_timestamp()}</em></p>")
    return "\n".join(parts)


@_register_renderer("pull_request")
def _render_pr(obj: dict) -> str:
    parts = [f"<h2>PR: {_escape(obj.get('title', ''))}</h2>"]

    if obj.get("description"):
        parts.append(f"<p>{_escape(obj['description'])}</p>")
    if obj.get("changes"):
        parts.append(f"<p><strong>Changes:</strong> {_escape(obj['changes'])}</p>")
    if obj.get("testing"):
        parts.append(f"<p><strong>Testing:</strong> {_escape(obj['testing'])}</p>")
    if obj.get("task_reference"):
        parts.append(f"<p><strong>Task:</strong> {_escape(obj['task_reference'])}</p>")

    return "\n".join(parts)


# ─── Public API ─────────────────────────────────────────────────────────


def to_html(artifact_type: str, obj: dict) -> str:
    """Transpose a structured object to rich HTML for Plane.

    Args:
        artifact_type: The artifact type (analysis_document, plan, etc.)
        obj: The structured object with the artifact's data.

    Returns:
        Rich HTML string with fleet markers for reverse transposition.
    """
    renderer = _RENDERERS.get(artifact_type)
    if not renderer:
        # Fallback: render as formatted JSON
        return (
            f"<h2>{_escape(artifact_type)}</h2>"
            f"<pre><code>{_escape(json.dumps(obj, indent=2))}</code></pre>"
        )

    # Embed the object data as a hidden JSON blob for reverse transposition
    data_json = json.dumps(obj, separators=(",", ":"))
    data_marker = ARTIFACT_DATA.format(data=_escape(data_json))

    body = renderer(obj)
    return (
        f"{ARTIFACT_START.format(type=artifact_type)}\n"
        f"{data_marker}\n"
        f"{body}\n"
        f"{ARTIFACT_END}"
    )


def from_html(html_content: str) -> Optional[dict]:
    """Transpose rich HTML back to a structured object.

    Extracts the embedded JSON data from fleet markers.

    Args:
        html_content: Rich HTML from Plane issue description.

    Returns:
        The structured object dict, or None if no artifact found.
    """
    # Look for the data marker
    pattern = re.compile(
        r'<!-- fleet:data:(.*?) -->',
        re.DOTALL,
    )
    match = pattern.search(html_content or "")
    if not match:
        return None

    try:
        data_str = html.unescape(match.group(1))
        return json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        return None


def get_artifact_type(html_content: str) -> Optional[str]:
    """Extract the artifact type from rich HTML.

    Args:
        html_content: Rich HTML from Plane issue description.

    Returns:
        The artifact type string, or None if no artifact found.
    """
    pattern = re.compile(r'<!-- fleet:artifact:start type="(\w+)" -->')
    match = pattern.search(html_content or "")
    return match.group(1) if match else None


def update_artifact(
    html_content: str,
    updates: dict,
) -> str:
    """Update an artifact embedded in HTML.

    Reads the object, applies updates, re-renders.

    Args:
        html_content: Current rich HTML with embedded artifact.
        updates: Dict of field updates to merge into the object.

    Returns:
        Updated rich HTML.
    """
    obj = from_html(html_content)
    artifact_type = get_artifact_type(html_content)

    if obj is None or artifact_type is None:
        return html_content  # nothing to update

    # Merge updates
    for key, value in updates.items():
        if isinstance(value, list) and isinstance(obj.get(key), list):
            # Append to list fields
            obj[key].extend(value)
        else:
            obj[key] = value

    # Re-render
    new_artifact_html = to_html(artifact_type, obj)

    # Replace the old artifact section
    pattern = re.compile(
        re.escape(ARTIFACT_START.format(type=artifact_type))
        + r'.*?'
        + re.escape(ARTIFACT_END),
        re.DOTALL,
    )

    if pattern.search(html_content):
        return pattern.sub(new_artifact_html, html_content)
    else:
        return new_artifact_html + "\n" + html_content