# Semgrep MCP Server

**Type:** External MCP Server
**Package:** semgrep (pip, --mcp mode)
**Transport:** command (semgrep --mcp)
**Tools:** scan, rule management, custom rules
**Auth:** Optional Semgrep token (free tier available)
**Installed for:** devsecops-expert

## What It Does

Static analysis security scanning across 30+ programming languages. Finds security vulnerabilities, bugs, and anti-patterns using pattern-matching rules. Supports custom rules for fleet-specific patterns. Free tier includes community rules covering OWASP Top 10.

## Fleet Use Case

DevSecOps (Cyberpunk-Zero) runs Semgrep scans on code changes during investigation and review stages. Custom rules can encode fleet-specific security requirements — e.g., "no raw SQL queries in MCP tools", "fleet_commit must include LaborStamp".

## Relationships

- INSTALLED FOR: devsecops-expert
- INSTALLED VIA: pip install semgrep (setup-mcp-deps.sh or system)
- CONNECTS TO: fleet-security-audit skill (Semgrep provides the scan data)
- CONNECTS TO: security-guidance plugin (complementary — guidance checks patterns, Semgrep does deep analysis)
- CONNECTS TO: /security-review command (Semgrep results feed into security review)
- CONNECTS TO: fleet_alert tool (critical findings → alert)
- CONNECTS TO: fleet_contribute tool (security_requirement based on scan findings)
