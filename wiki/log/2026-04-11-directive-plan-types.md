---
title: "Directive: Plan Types — Design Plan vs Operations Plan"
type: note
domain: log
note_type: directive
status: active
created: 2026-04-11
updated: 2026-04-11
tags: [directive, plans, methodology, reasoning-stage, quality, PO]
confidence: medium
sources: []
---

# Directive: Plan Types — Design Plan vs Operations Plan

## Summary

PO directive distinguishing two fundamentally different artifacts that both get called "plan": a **Design Plan** (the real plan — what we deliver and how we reach there: architecture, rationale, data flow, component connections, constraints, traceability) versus an **Operations Plan** (a personal TODO list — sequential steps, mechanical, useful only for handing brainless work to cheap models). The methodology's "produce a plan in reasoning stage" always means a Design Plan. An Operations Plan is never a plan deliverable.

## PO Directive (verbatim)

> "you really understand what is written ? do it then but we need to do something about it, you cannot go on and always create trash plan like this... we are going to need a high standard plan document that must always be respected I feel... Its as if what you wrote is a sequence of operation instead of a plan... like a cookbook... maybe we need to differenciate between multiple type of plans now that I think about it... its like what you did is an execution plan. like you the operations from bug to bugfix but this would never work with a feature.. if this was a feature.. all this would just be trash written all over the code that is entirely random and disconnected and no tracability of what was done and why and in which sequence....."

> "Normally we dont do document for operation plan, you just do it before doing a job so that its mechanical and sequencial but it virtually useless. what add value are design plan.... we just need to make create that operations plan are not real plan they are just a personal TODO list basically... it must just be clear that its not what we ask when we ask for a plan...."

> "the only moment I could see a usefullness for this kind of plan is when you want to give a brainless job to an AI that cannot reason to save some cost and/or test if a cheap or free model can do some things... clearly the methodology is not about this but about the development and engineering pipeline..."

> "its like if I ask you a spec document and you give me a table with specs instead of a full fledge spec document or if I ask a requirements document but all there is a list of requirements...."

> "A plan is not what you do... the plan is what we deliver and how we reach there..."

## Interpretation

### Design plan (the real plan)

What the methodology means by "produce a plan in reasoning stage." Describes WHAT we deliver and HOW we reach there. Architecture, rationale, how components connect, data flow, constraints, traceability to the verbatim requirement. The file changes are a CONSEQUENCE of the design, not the plan itself.

Analogy: a spec document is not a table of specs. A requirements document is not a list of requirements. A plan is not a list of steps.

### Operations plan (personal TODO list)

Not a real plan. A mechanical, sequential checklist — what to change, in what order. Virtually useless as a document. You do it mentally before doing a job but you don't write it down as a deliverable.

One use case: handing brainless work to a cheap/free model that can't reason. The operations plan IS the reasoning the model can't do, externalized as a checklist. This is a Lightweight tier concern, not a methodology concern.

### What this means

When the methodology says "produce a plan" in reasoning stage, it means a DESIGN PLAN. An operations plan (TODO list) should never be presented as a plan deliverable. The methodology is about the development and engineering pipeline, not about step-by-step instructions.

Operations plans don't need documents — they're personal working notes. Design plans are the artifact the reasoning stage produces and the PO reviews.

## Relationships

- FEEDS INTO: [[Plan: Context Injection Pipeline Blocker Fixes]]
- FEEDS INTO: [[Plan: TK-01 Golden Path — 200+ Lines of High-Value Output]]
