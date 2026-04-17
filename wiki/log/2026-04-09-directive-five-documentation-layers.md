---
title: "Directive: Five Documentation Layers"
type: note
domain: log
note_type: directive
status: active
created: 2026-04-09
updated: 2026-04-09
tags: [directive, documentation, layers, wiki, docs, code-docs, smart-docs, specs, standard, PO]
sources:
  - id: src-research-wiki-directive
    type: documentation
    project: devops-solutions-research-wiki
    path: wiki/log/2026-04-09-directive-docs-layers-old-models.md
    title: "Documentation Layers + Old Model Tolerance"
confidence: medium
---

# Directive: Five Documentation Layers

## Summary

PO directive establishing five distinct documentation layers that must not be conflated: **wiki knowledge** (synthesized, structured, evolving — the second brain's core), **public docs** (user-facing reference, old model in OpenFleet — migrate incrementally), **code docs** (inline docstrings + WHY comments alongside source), **smart docs** (documentation files distributed through src/ explaining subsystems), and **specs & plans** (temporary execution artifacts in docs/superpowers/). The LLM Wiki IS the standard for all ecosystem projects; old models are tolerated during transition but realigned toward wiki/ structure over time.

## PO Directive (verbatim)

> "there is also the nuance between wiki and public docs and code docs (like there is in this project /home/jfortin/devops-control-plane/, you can see some docs, considered potential smart docs, can be throughout the code / src or whatnot + the JSDoc or equivalent / headers and annotations and parameters comments and whatnot and inner comment.) it needs to be clear what is what."

> "The reality that some agent will conflate or that some project have an old model but if the second brain is attached then its one of our project so we should align with the new model and just tolerate the old models and possibly even do cleaning / refactoring."

## The Five Layers

1. **Wiki knowledge** (wiki/) — the second brain's core. Synthesized, structured, evolving. Frontmatter, relationships, quality gates. Knowledge compounds here.
2. **Public docs** (docs/) — user-facing documentation, READMEs, guides. For humans consuming the project. Old model in OpenFleet — tolerate, align incrementally.
3. **Code docs** — inline in source: docstrings, type hints, parameter annotations, comments explaining WHY. Lives with the code.
4. **Smart docs** — documentation files distributed throughout src/ explaining subsystems alongside code. Aggregated code docs. Not in wiki/, not in docs/ — alongside the code they describe.
5. **Specs and plans** (docs/superpowers/) — execution track artifacts. Temporary. Serve the build process, not the knowledge base. Archive after work completes.

## Standard

The LLM Wiki IS the standard for ALL projects in the ecosystem. No regression. If a project doesn't have wiki/ yet, it gets wiki/. Old model is tolerated during transition, not kept as permanent alternative. Align incrementally.

## Artifact → Layer Mapping

| Artifact | Layer | Location |
|----------|-------|----------|
| PO directives | wiki knowledge | wiki/log/ (verbatim) |
| Analysis findings | wiki knowledge | wiki/domains/{domain}/ |
| Design decisions | wiki knowledge | wiki/domains/{domain}/ |
| Architecture reference | public docs (old model) | docs/ — migrate to wiki/ over time |
| System reference | public docs (old model) | docs/systems/ — migrate over time |
| Implementation code | code docs | fleet/ with docstrings + comments |
| Subsystem explanation | smart docs | README.md alongside code |
| Implementation spec | specs (temporary) | docs/superpowers/specs/ |
| Implementation plan | specs (temporary) | docs/superpowers/plans/ |
| Session notes | wiki knowledge | wiki/log/ |
| Knowledge synthesis | wiki knowledge | wiki/domains/ |

## Relationships

- FEEDS INTO: [[Wiki Structure Gaps — LLM Wiki Model Alignment]]
