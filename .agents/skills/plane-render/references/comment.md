# Comment Template

Use when posting a comment to a Plane issue (`comment_html` field).
Covers: progress update, acceptance, completion, blocker, review decision.

---

## Progress Update

```html
<h3>Update</h3>
<ul>
  <li>{net-new fact, artifact, or decision — one line each}</li>
</ul>

<h3>Evidence</h3>
<ul>
  <li>{link, command output, file path, or metric}</li>
</ul>

<h3>Next</h3>
<ul>
  <li>{next concrete action 1}</li>
  <li>{next concrete action 2 if needed}</li>
</ul>

<p><sub>{agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

---

## Acceptance (starting work)

```html
<h3>▶️ Accepted</h3>
<p><strong>Plan:</strong> {1-2 sentence approach}</p>
<p><strong>Scope:</strong> {files or areas to touch}</p>
<p><strong>Risks:</strong> {top 1-2 risks or "none identified"}</p>

<p><sub>{agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

---

## Completion

```html
<h3>✅ Complete</h3>
<p>{1-2 sentences: what was done and why it satisfies acceptance criteria}</p>

<h3>Artifacts</h3>
<ul>
  <li><a href="{pr_url}">PR #{pr_number}</a></li>
  <li><a href="{branch_url}">Branch: {branch_name}</a></li>
</ul>

<h3>Files Changed</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><a href="{file_url}">{file_path}</a></td><td>{what changed}</td></tr>
  </tbody>
</table>

<p><sub>{agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

---

## Blocker

```html
<h3>🚫 Blocked</h3>
<p><strong>Reason:</strong> {specific blocker — one sentence}</p>
<p><strong>Impact:</strong> {what cannot proceed}</p>
<p><strong>Needed:</strong> {exact ask — from whom, what decision or action}</p>

<p><sub>{agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

---

## Review Decision

```html
<h3>🔍 Review: {Approved | Changes Requested | Rejected}</h3>
<p><strong>Summary:</strong> {1-2 sentence verdict}</p>

<h3>Findings</h3>
<ul>
  <li><strong>{severity}:</strong> {finding and location}</li>
</ul>

<h3>Required Changes</h3>
<ol>
  <li>{specific change required — or "None" if approved}</li>
</ol>

<p><sub>{agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

---

## Rules

- **Never post** "still working" keepalive comments — only post net-new value.
- **Every comment must end** with the `<sub>` agent/task footer.
- **All URLs must be `<a href>`** — resolve with fleet-urls skill.
- Keep content **scannable**: 5 seconds to understand the update.
