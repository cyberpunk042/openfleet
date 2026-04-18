---
title: "Architecture"
type: index
domain: architecture
status: active
created: 2026-04-09
updated: 2026-04-17
tags: [architecture, context-injection, tier-rendering, methodology, orchestration, fleet]
confidence: high
sources: []
---

# Architecture

OpenFleet's architecture pages — context injection pipeline, tier rendering, methodology models, orchestrator brain, chain/bus audits, operational modes, plus the analysis → investigation → plan artifact chains from our methodology stages.

## Ecosystem & Scope

- [[Agent Ecosystem Allocation — Skills, Plugins, Packs Per Role]]
- [[Wiki Structure Gaps — LLM Wiki Model Alignment]]
- [[Path-to-Live Reconciliation — Where We Are]]

## Context Injection Pipeline

- [[Context Injection Decision Tree]] — the canonical tree every preembed/heartbeat/task injection follows
- [[Shared Models Integration — LLM Wiki + Methodology in OpenFleet]] — how brain's shared models map to OpenFleet
- [[Methodology Models Rationale]] — why 7 named models, selection rules, protocol adaptations
- [[Tier Rendering Design Rationale]] — why 5 capability tiers drive rendering depth
- [[Operational Modes — Heartbeat vs Task, Injection Levels]] — the mode-vs-mode content ownership split

## Analysis / Investigation / Plan Chain — Context Injection Blockers

- [[Analysis: Context Injection Pipeline Blockers]] — 4 findings identified in analysis stage
- [[Investigation: Context Injection Pipeline Blocker Solutions]] — solution options per blocker
- [[Plan: Context Injection Pipeline Blocker Fixes]] — operations plan applying the fixes

## Analysis / Investigation / Plan Chain — Output Quality (TK-01)

- [[Analysis: Why TK-01 Produces 88 Lines of Low-Value Output]] — 10 systemic issues
- [[Investigation: Solutions for Context Output Quality]] — option tradeoffs
- [[Plan: TK-01 Golden Path — 200+ Lines of High-Value Output]] — design plan

## Validation & Findings

- [[Critical Review Findings — Context Injection Scenarios]] — ~25 issues from line-by-line review
- [[Validation Issues Catalog — Every Problem Found]] — cumulative catalog
- [[15 Anti-Patterns from TierRenderer Session]] — operational anti-patterns
- [[OpenFleet doctor.py Rules Mapped to Agent Failure Taxonomy]] — coverage map of our 10 doctor rules vs brain's 8 taxonomy classes; 5 novel rules flagged as candidate contributions

## Orchestrator & E003 Design

- [[Brain (Orchestrator) Audit — E003 Phase 0]] — current 13-step cycle audit
- [[Context Strategy Design — E003]] — what to inject, at what depth, for whom
- [[Deterministic Bypass Design — E003]] — $0 Python decisions, reserve Claude for reasoning
- [[Effort Escalation Design — E003]] — model × effort selection ladder

## Chain/Bus (E002) & Gateway

- [[Chain/Bus Architecture Audit — E002 Phase 0]] — 16 chain builders + bus inventory
- [[Gateway File Injection Audit]] — how gateway reads agent files and injects context

## Navigator / Intent Map

- [[Navigator Intent-Map Gap Analysis]] — coverage gap (41% of theoretical matrix)
- [[Navigator Intent-Map Expansion — 19 Missing Intents + Pack Skills]] — scope + pack wiring

## TOOLS.md Redesign Track

- [[generate-tools-md.py Redesign — Algorithm Specification]] — algorithm spec
- [[TOOLS.md Redesign — Focused Desk, Detail On-Demand]] — structural redesign
