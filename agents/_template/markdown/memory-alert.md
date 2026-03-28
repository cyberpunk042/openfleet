# Board Memory Alert Template
#
# Used when an agent detects a security, quality, or architecture concern.
# Tags REQUIRED: alert, {severity}, {project or fleet}

## ⚠️ {severity}: {title}

**Project:** {project_name}
**Found by:** {agent_name}
**Severity:** {critical / high / medium / low}
**Category:** {security / quality / architecture / workflow / tooling}

### Details

{description with specific evidence — file paths as GitHub links, error messages, CVE IDs}

### Recommended Action

{what should be done — specific, actionable}

### References

- {clickable links to relevant files, issues, CVEs, documentation}

---

<sub>Tags: `alert`, `{severity}`, `{category}`, `project:{project}`</sub>