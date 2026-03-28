# IRC Message Format Reference
#
# These are the standard formats for fleet IRC messages.
# Keep them short — IRC is for awareness, detail goes in MC/GitHub.
# Every message MUST include a URL when one exists.

# ─── Task Events ────────────────────────────────────────────────────

# Task created
[{agent}] 📋 TASK CREATED: {title} — {task_url}

# Task dispatched to agent
[{agent}] 🚀 DISPATCHED: {title} — {task_url}

# Task accepted (agent started work)
[{agent}] ▶️ STARTED: {title} — {task_url}

# Task blocked
[{agent}] 🚫 BLOCKED: {title} — {reason} — {task_url}

# Task completed (PR ready)
[{agent}] ✅ PR READY: {title} — {pr_url} | Compare: {compare_url}

# ─── PR Events ──────────────────────────────────────────────────────

# PR merged
[fleet] 🔀 MERGED: {title} — {pr_url}

# PR merge failed
[fleet] ❌ MERGE FAILED: {title} — {pr_url}

# Task auto-closed (PR was merged)
[fleet] ✅ TASK DONE: {title} — {task_url}

# ─── Alerts (posted to #alerts channel) ─────────────────────────────

# Critical alert
🔴 [{agent}] CRITICAL: {title} — {url}

# High severity alert
🟠 [{agent}] HIGH: {title} — {url}

# Medium severity alert
🟡 [{agent}] MEDIUM: {title} — {url}

# ─── Reviews (posted to #reviews channel) ────────────────────────────

# QA check passed
[qa-engineer] ✅ TESTS PASS: {branch} — {N}/{total} passing — {compare_url}

# QA check failed
[qa-engineer] ❌ TESTS FAIL: {branch} — {failures} failures — {compare_url}

# Architect review approved
[architect] ✅ REVIEW OK: {branch} — {compare_url}

# Architect review needs changes
[architect] 🔄 CHANGES NEEDED: {branch} — {details} — {compare_url}

# ─── System Events ──────────────────────────────────────────────────

# Fleet online
[fleet] 🟢 Fleet online — MC: http://localhost:3000 | IRC: #fleet

# Sync completed
[fleet] 🔄 Sync: {actions} actions — {details}

# Daily digest
[fleet] 📊 Daily digest: {tasks_done} done, {prs_merged} merged, {blockers} blockers — {digest_url}