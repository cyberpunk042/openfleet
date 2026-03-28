"""Behavioral security — detect suspicious agent behavior and human directives.

Cyberpunk-Zero's behavioral analysis layer:
- Scans task content for dangerous patterns
- Scans code diffs for suspicious operations
- Analyzes human directives for red flags
- Can set security_hold on tasks (blocks approval processing)

Even human requests get flagged if suspicious — not blocked, but flagged
with an urgent ntfy notification asking the human to confirm intent.

The compromised agent investigator ensures that no harmful task, directive,
or code modification passes through the fleet without scrutiny.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SecurityFinding:
    """A suspicious pattern detected by behavioral analysis."""

    category: str          # credential_exfil, db_destruction, security_disable, etc.
    severity: str          # critical, high, medium, low
    title: str
    evidence: str          # What was found
    recommendation: str    # What to do about it
    should_hold: bool = False  # Should set security_hold on the task


@dataclass
class SecurityScan:
    """Result of a behavioral security scan."""

    findings: list[SecurityFinding] = field(default_factory=list)
    scanned_content: str = ""

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def critical_findings(self) -> list[SecurityFinding]:
        return [f for f in self.findings if f.severity == "critical"]

    @property
    def should_hold(self) -> bool:
        return any(f.should_hold for f in self.findings)

    @property
    def max_severity(self) -> str:
        if not self.findings:
            return "none"
        severities = ["critical", "high", "medium", "low"]
        for s in severities:
            if any(f.severity == s for f in self.findings):
                return s
        return "low"


# Suspicious patterns with severity and category
SUSPICIOUS_PATTERNS: list[tuple[str, str, str, str, bool]] = [
    # (pattern, category, severity, title, should_hold)

    # Credential exfiltration
    (r"(token|key|secret|password|credential).*?(send|post|curl|fetch|upload|transmit)",
     "credential_exfil", "critical", "Potential credential exfiltration", True),
    (r"(curl|wget|requests\.post|fetch).*?(token|key|secret|api_key)",
     "credential_exfil", "critical", "Sending credentials to external endpoint", True),

    # Database destruction
    (r"(drop|truncate)\s+(table|database|collection|schema)",
     "db_destruction", "critical", "Database destruction command", True),
    (r"delete\s+from\s+\w+\s*(where\s+1|$)",
     "db_destruction", "high", "Potential mass delete without conditions", True),

    # Security control disabling
    (r"(disable|remove|skip|bypass)\s*(all\s+)?(security|auth|approval|review|verification)",
     "security_disable", "critical", "Disabling security controls", True),
    (r"--no-verify|--force|--skip-checks",
     "security_disable", "high", "Bypassing safety checks", False),

    # External network access to unknown hosts
    (r"(curl|wget|requests)\s+https?://(?!github\.com|localhost|127\.0\.0\.1|192\.168\.)",
     "external_comms", "medium", "External network request to unknown host", False),

    # Permission escalation
    (r"chmod\s+777",
     "permission_escalation", "high", "Setting world-writable permissions", False),
    (r"sudo\s+",
     "permission_escalation", "medium", "Sudo usage", False),

    # Sensitive file modification
    (r"(\.env|credentials|secrets|\.ssh|\.gnupg)\s*(=|:|modify|write|update|delete)",
     "sensitive_files", "high", "Modifying sensitive files", False),

    # Supply chain
    (r"pip\s+install\s+(?!-r|--requirement).*(?!pytest|ruff|httpx|pyyaml|websockets)",
     "supply_chain", "medium", "Installing unvetted package", False),
]


def scan_text(text: str, context: str = "task") -> SecurityScan:
    """Scan text content for suspicious patterns.

    Args:
        text: Content to scan (task description, code diff, human message).
        context: Where this text came from ("task", "diff", "directive").

    Returns:
        SecurityScan with any findings.
    """
    if not text:
        return SecurityScan()

    findings: list[SecurityFinding] = []
    text_lower = text.lower()

    for pattern, category, severity, title, should_hold in SUSPICIOUS_PATTERNS:
        try:
            if re.search(pattern, text_lower):
                evidence = _extract_evidence(text, pattern)
                findings.append(SecurityFinding(
                    category=category,
                    severity=severity,
                    title=title,
                    evidence=evidence,
                    recommendation=_get_recommendation(category, context),
                    should_hold=should_hold,
                ))
        except re.error:
            continue

    return SecurityScan(findings=findings, scanned_content=text[:200])


def scan_task(title: str, description: str = "") -> SecurityScan:
    """Scan a task's content for suspicious patterns."""
    combined = f"{title}\n{description}"
    return scan_text(combined, context="task")


def scan_diff(diff_content: str) -> SecurityScan:
    """Scan a code diff for suspicious patterns."""
    return scan_text(diff_content, context="diff")


def scan_directive(human_message: str) -> SecurityScan:
    """Scan a human directive for suspicious patterns.

    Even human requests get flagged — not blocked, but flagged
    with a recommendation to confirm intent.
    """
    scan = scan_text(human_message, context="directive")

    # For human directives, adjust recommendations
    for finding in scan.findings:
        finding.recommendation = (
            f"Human requested: {finding.title}. "
            f"Confirm intent before proceeding. "
            f"Original: {finding.recommendation}"
        )
        # Don't auto-hold human directives — just flag
        finding.should_hold = False

    return scan


def _extract_evidence(text: str, pattern: str) -> str:
    """Extract the matching portion of text as evidence."""
    try:
        match = re.search(pattern, text.lower())
        if match:
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            return f"...{text[start:end]}..."
    except Exception:
        pass
    return text[:100]


def _get_recommendation(category: str, context: str) -> str:
    """Get a recommendation based on finding category and context."""
    recommendations = {
        "credential_exfil": "Block immediately. Verify no credentials were leaked. Rotate affected keys.",
        "db_destruction": "Block. Verify this is intentional and targeted. Require manual confirmation.",
        "security_disable": "Block. Security controls must not be disabled without explicit human approval.",
        "external_comms": "Review the target URL. Verify it's a known, trusted endpoint.",
        "permission_escalation": "Review necessity. Use minimum required permissions.",
        "sensitive_files": "Review the changes carefully. Ensure no secrets are exposed.",
        "supply_chain": "Verify the package is legitimate. Check for known vulnerabilities.",
    }
    return recommendations.get(category, "Review the finding and assess risk.")