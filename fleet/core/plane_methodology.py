"""Plane methodology integration — read/write methodology fields on Plane issues.

Plane CE doesn't have custom fields. We use a hybrid approach:
- Stage → labels (stage:conversation, stage:work, etc.)
- Readiness → labels (readiness:0, readiness:50, readiness:99, etc.)
- Verbatim requirement → visible section in description_html

Valid readiness values: 0, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99, 100
Strategic checkpoints at 0 (nothing defined), 50 (direction review), 90 (final review).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Valid readiness percentages (not a continuous 0-100 — specific values)
VALID_READINESS = [0, 5, 10, 20, 30, 50, 70, 80, 90, 95, 99, 100]

# Valid stages
VALID_STAGES = ["conversation", "analysis", "investigation", "reasoning", "work"]

# Label prefixes
STAGE_PREFIX = "stage:"
READINESS_PREFIX = "readiness:"

# HTML markers for verbatim requirement in description
VERBATIM_START = '<!-- fleet:requirement_verbatim:start -->'
VERBATIM_END = '<!-- fleet:requirement_verbatim:end -->'


@dataclass
class PlaneMethodologyState:
    """Methodology state extracted from a Plane issue's labels + description."""
    task_stage: Optional[str] = None
    task_readiness: int = 0
    requirement_verbatim: Optional[str] = None


def extract_stage_from_labels(label_names: list[str]) -> Optional[str]:
    """Extract the methodology stage from a list of label names.

    Returns the stage value (e.g., "conversation") or None if no stage label.
    If multiple stage labels exist, returns the last one (most recent).
    """
    stage = None
    for name in label_names:
        if name.startswith(STAGE_PREFIX):
            value = name[len(STAGE_PREFIX):]
            if value in VALID_STAGES:
                stage = value
    return stage


def extract_readiness_from_labels(label_names: list[str]) -> int:
    """Extract the readiness percentage from a list of label names.

    Returns the readiness value (e.g., 50) or 0 if no readiness label.
    If multiple readiness labels exist, returns the highest.
    """
    readiness = 0
    for name in label_names:
        if name.startswith(READINESS_PREFIX):
            try:
                value = int(name[len(READINESS_PREFIX):])
                if value in VALID_READINESS and value > readiness:
                    readiness = value
            except ValueError:
                continue
    return readiness


def extract_verbatim_from_html(description_html: str) -> Optional[str]:
    """Extract the verbatim requirement from issue description HTML.

    Looks for content between the fleet:requirement_verbatim markers.
    Returns the text content or None if not found.
    """
    if not description_html:
        return None
    pattern = re.compile(
        re.escape(VERBATIM_START) + r'\s*(.*?)\s*' + re.escape(VERBATIM_END),
        re.DOTALL,
    )
    match = pattern.search(description_html)
    if match:
        # Strip HTML tags to get plain text
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return text if text else None
    return None


def inject_verbatim_into_html(
    description_html: str,
    verbatim: str,
) -> str:
    """Inject or update the verbatim requirement section in description HTML.

    If the markers already exist, replaces the content between them.
    If not, prepends the section to the description.
    """
    section = (
        f'{VERBATIM_START}\n'
        f'<blockquote><strong>Verbatim Requirement (PO)</strong><br/>\n'
        f'{verbatim}\n'
        f'</blockquote>\n'
        f'{VERBATIM_END}'
    )

    pattern = re.compile(
        re.escape(VERBATIM_START) + r'.*?' + re.escape(VERBATIM_END),
        re.DOTALL,
    )

    if pattern.search(description_html or ''):
        # Replace existing
        return pattern.sub(section, description_html)
    else:
        # Prepend to description
        return section + '\n' + (description_html or '')


def extract_methodology_state(
    label_names: list[str],
    description_html: str = "",
) -> PlaneMethodologyState:
    """Extract full methodology state from a Plane issue."""
    return PlaneMethodologyState(
        task_stage=extract_stage_from_labels(label_names),
        task_readiness=extract_readiness_from_labels(label_names),
        requirement_verbatim=extract_verbatim_from_html(description_html),
    )


def build_label_updates(
    current_label_names: list[str],
    stage: Optional[str] = None,
    readiness: Optional[int] = None,
) -> list[str]:
    """Build an updated label name list with methodology labels replaced.

    Removes old stage/readiness labels and adds new ones.
    Returns the full list of label names (not IDs — caller resolves to IDs).
    """
    # Remove existing methodology labels
    updated = [
        name for name in current_label_names
        if not name.startswith(STAGE_PREFIX) and not name.startswith(READINESS_PREFIX)
    ]

    # Add new stage label
    if stage and stage in VALID_STAGES:
        updated.append(f"{STAGE_PREFIX}{stage}")

    # Add new readiness label
    if readiness is not None:
        # Snap to nearest valid value
        closest = min(VALID_READINESS, key=lambda v: abs(v - readiness))
        updated.append(f"{READINESS_PREFIX}{closest}")

    return updated