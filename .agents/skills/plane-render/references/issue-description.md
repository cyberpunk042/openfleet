# Issue Description Template

Use when creating a new Plane issue via API (`description_html` field).

## Template

```html
<h2>Context</h2>
<p>{1-3 sentences: why this issue exists and what problem it solves}</p>

<h2>Scope</h2>
<ul>
  <li>{area or component affected}</li>
  <li>{another scope item if needed}</li>
</ul>

<h2>Acceptance Criteria</h2>
<ol>
  <li>{measurable outcome 1}</li>
  <li>{measurable outcome 2}</li>
  <li>{measurable outcome 3}</li>
</ol>

<h2>Steps / Approach</h2>
<ol>
  <li>{step 1}</li>
  <li>{step 2}</li>
  <li>{step 3}</li>
</ol>

<h2>References</h2>
<ul>
  <li><a href="{url}">Related task / PR / doc</a></li>
</ul>

<hr>
<p><sub>Created by {agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```

## Placeholder Guide

| Placeholder | What to fill |
|---|---|
| `{1-3 sentences…}` | Business or technical context — the "why" |
| `{area or component}` | e.g. `auth module`, `CI pipeline`, `NNRT core engine` |
| `{measurable outcome}` | Testable, binary — "X works", "Y is documented", "Z passes CI" |
| `{step}` | Implementation steps if known; omit section if exploratory |
| `{url}` | Absolute URL; use fleet-urls skill to resolve |
| `{agent_name}` | Your agent handle |
| `{task_url}` | MC task URL |
| `{task_short_id}` | e.g. `MC-42` |

## Minimal Variant (simple tasks)

When context is obvious and steps are undefined, use the shorter form:

```html
<h2>Context</h2>
<p>{why}</p>

<h2>Acceptance Criteria</h2>
<ol>
  <li>{outcome 1}</li>
  <li>{outcome 2}</li>
</ol>

<hr>
<p><sub>Created by {agent_name} · <a href="{task_url}">{task_short_id}</a></sub></p>
```
