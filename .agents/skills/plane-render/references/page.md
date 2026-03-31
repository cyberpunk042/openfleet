# Page Content Template

Use when creating or updating a Plane page (`description_html` field).
Suitable for: architecture decision records (ADRs), requirements docs,
runbooks, design docs, and cross-reference reference pages.

---

## Architecture Decision Record (ADR)

```html
<h1>{ADR-NNN}: {Short Decision Title}</h1>
<p><strong>Status:</strong> {Proposed | Accepted | Deprecated | Superseded by <a href="{url}">ADR-NNN</a>}</p>
<p><strong>Date:</strong> {YYYY-MM-DD}</p>
<p><strong>Author:</strong> {agent_name}</p>

<h2>Context</h2>
<p>{What situation or problem prompted this decision? What constraints exist?}</p>

<h2>Decision</h2>
<p>{The decision made. Be direct: "We will use X because Y."}</p>

<h2>Options Considered</h2>
<table>
  <thead>
    <tr><th>Option</th><th>Pros</th><th>Cons</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>{Option A — chosen}</td>
      <td><ul><li>{pro}</li></ul></td>
      <td><ul><li>{con}</li></ul></td>
    </tr>
    <tr>
      <td>{Option B}</td>
      <td><ul><li>{pro}</li></ul></td>
      <td><ul><li>{con}</li></ul></td>
    </tr>
  </tbody>
</table>

<h2>Consequences</h2>
<ul>
  <li><strong>Positive:</strong> {outcome}</li>
  <li><strong>Negative/Trade-off:</strong> {outcome}</li>
  <li><strong>Risks:</strong> {risk and mitigation}</li>
</ul>

<h2>References</h2>
<ul>
  <li><a href="{url}">{label}</a></li>
</ul>

<hr>
<p><sub>Page maintained by {agent_name} · Last updated {YYYY-MM-DD}</sub></p>
```

---

## Requirements Document

```html
<h1>{Feature or System Name} — Requirements</h1>
<p><strong>Version:</strong> {v1.0}</p>
<p><strong>Status:</strong> {Draft | Under Review | Approved}</p>
<p><strong>Owner:</strong> {agent_name or team}</p>

<h2>Overview</h2>
<p>{What this document covers and why the feature/system exists.}</p>

<h2>Functional Requirements</h2>
<table>
  <thead>
    <tr><th>ID</th><th>Requirement</th><th>Priority</th></tr>
  </thead>
  <tbody>
    <tr><td>FR-01</td><td>{requirement statement}</td><td>Must Have</td></tr>
    <tr><td>FR-02</td><td>{requirement statement}</td><td>Should Have</td></tr>
  </tbody>
</table>

<h2>Non-Functional Requirements</h2>
<ul>
  <li><strong>Performance:</strong> {e.g. p99 latency &lt; 200ms}</li>
  <li><strong>Security:</strong> {e.g. all endpoints require auth token}</li>
  <li><strong>Reliability:</strong> {e.g. 99.9% uptime}</li>
</ul>

<h2>Out of Scope</h2>
<ul>
  <li>{explicitly excluded item}</li>
</ul>

<h2>Open Questions</h2>
<ul>
  <li>{unresolved question — @mention owner if applicable}</li>
</ul>

<h2>Cross-References</h2>
<ul>
  <li><a href="{url}">{related issue / ADR / PR}</a></li>
</ul>

<hr>
<p><sub>Page maintained by {agent_name} · Last updated {YYYY-MM-DD}</sub></p>
```

---

## Runbook / Operational Guide

```html
<h1>{Process Name} Runbook</h1>
<p><strong>Applies to:</strong> {system or component}</p>
<p><strong>Owner:</strong> {agent_name or team}</p>

<h2>Overview</h2>
<p>{What this runbook is for and when to use it.}</p>

<h2>Prerequisites</h2>
<ul>
  <li>{tool or access required}</li>
  <li>{env var or credential}</li>
</ul>

<h2>Steps</h2>
<ol>
  <li>
    <p><strong>{Step title}</strong></p>
    <pre><code>{command or action}</code></pre>
    <p>Expected output: {what success looks like}</p>
  </li>
  <li>
    <p><strong>{Step title}</strong></p>
    <pre><code>{command or action}</code></pre>
  </li>
</ol>

<h2>Troubleshooting</h2>
<table>
  <thead><tr><th>Symptom</th><th>Cause</th><th>Fix</th></tr></thead>
  <tbody>
    <tr><td>{symptom}</td><td>{likely cause}</td><td>{remediation}</td></tr>
  </tbody>
</table>

<h2>Rollback</h2>
<ol>
  <li>{rollback step}</li>
</ol>

<hr>
<p><sub>Page maintained by {agent_name} · Last updated {YYYY-MM-DD}</sub></p>
```

---

## Rules

- Use `&lt;` and `&gt;` for literal angle brackets in text.
- Use `&amp;` for literal ampersands in text.
- Keep headings hierarchical: `<h1>` for page title, `<h2>` for sections, `<h3>` for subsections.
- Prefer tables for comparisons and requirements; prefer lists for items without attributes.
- Every page must end with the `<sub>` footer showing author and date.
