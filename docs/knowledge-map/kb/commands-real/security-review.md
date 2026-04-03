# /security-review

**Type:** Claude Code Built-In Command
**Category:** Git & Code
**Available to:** DevSecOps (primary), Fleet-ops (review), Engineer (pre-submit)

## What It Actually Does

Analyzes the current branch's changes for security vulnerabilities. Reads the diff between the current branch and main, examines each changed file for security patterns: injection vulnerabilities (SQL, command, XSS), authentication bypasses, secret exposure, insecure dependencies, permission issues.

This is NOT the same as running Semgrep or Snyk MCP servers — those are external scanners. /security-review uses Claude's reasoning to analyze the code changes in context, understanding the application logic (not just pattern matching).

## When Fleet Agents Should Use It

**DevSecOps investigation stage:** Security review of a branch before it reaches fleet-ops for approval. DevSecOps runs /security-review → finds issues → posts security_requirement contribution → or sets security_hold if critical.

**Fleet-ops review Step 6 ("Quality Check — Security"):** Part of the 7-step review protocol. Fleet-ops runs /security-review on the PR branch to check for security issues before approving.

**Engineer pre-submit check:** Before calling fleet_task_complete, engineer can run /security-review on their own branch to catch issues before review.

**After dependency changes:** New package added or version bumped. /security-review catches known vulnerable versions, suspicious packages, or supply chain risks.

## What It Looks For

- **Injection:** SQL injection, command injection, XSS, template injection
- **Authentication:** bypassed auth checks, hardcoded credentials, weak token generation
- **Secrets:** API keys, passwords, tokens in code or config
- **Dependencies:** known vulnerable versions, suspicious packages
- **Permissions:** overly broad permissions, missing access controls
- **Data exposure:** PII logging, unmasked sensitive data in responses
- **Configuration:** debug mode in production, insecure defaults

## Relationships

- USED BY: DevSecOps (primary security tool during investigation)
- USED BY: Fleet-ops (review Step 6 — security check)
- USED BY: Engineer (pre-submit self-check)
- CONNECTS TO: behavioral_security.py (fleet's regex-based security scanner — different approach, complementary)
- CONNECTS TO: fleet_alert (security findings → alert with severity)
- CONNECTS TO: security_hold mechanism (critical findings → block approval)
- CONNECTS TO: fleet-security-audit skill (broader audit that includes /security-review)
- CONNECTS TO: Trivy MCP server (container + dependency scanning — different layer)
- CONNECTS TO: Semgrep MCP server (pattern-based SAST — different approach)
- CONNECTS TO: security-guidance plugin (hook monitoring 9 OWASP patterns)
- CONNECTS TO: codex-plugin-cc (adversarial security review from different AI)
- CONNECTS TO: crisis-management cycle_phase (security incidents activate devsecops)
- DIFFERENCE: /security-review = Claude reasoning about code logic. Semgrep = pattern matching. Trivy = dependency/container scanning. behavioral_security.py = regex patterns. All complementary layers.
