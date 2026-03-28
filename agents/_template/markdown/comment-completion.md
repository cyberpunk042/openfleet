# Task Completion Comment Template
#
# Used when an agent completes a task and moves to review.
# All URLs must be resolved using fleet-urls skill.

## ✅ Completed

**PR:** [{pr_title}]({pr_url})
**Branch:** [`{branch}`]({compare_url})

### 📊 Changes

| File | Change |
|------|--------|
| [`{path}`]({file_url}) | {what changed} |

### 📝 Summary

{2-3 sentences: what was done, why, and the result}

### 📋 Commits ({commit_count})

| SHA | Message |
|-----|---------|
| [`{sha_short}`]({commit_url}) | {commit_message} |

---

<sub>{agent_name} · [{task_short}]({task_url})</sub>