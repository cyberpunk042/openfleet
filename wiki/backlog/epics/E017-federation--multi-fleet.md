---
title: "Federation & Multi-Fleet"
type: epic
domain: backlog
status: draft
priority: P2
created: 2026-04-08
updated: 2026-04-09
tags: [federation, multi-fleet, plane, identity, fleet-number, cross-fleet]
confidence: high
sources: []
---

# Federation & Multi-Fleet

## Summary

Multiple fleets connected to the same Plane. Each fleet has its own number, its own agent names, its own identity. A different fleet would have different names and usernames. Two fleets can coordinate through shared Plane projects. Federation protocol for cross-fleet communication.

> "having their own Identity name and username and whatnot (another fleet would have another name and username, you need to think about this, like we do a diff fleet number if that is still in place, since it will be possible to have two fleet connected to the same Plane)"

## Goals

- Fleet identity: fleet number, fleet name, agent prefix (alpha-architect vs beta-architect)
- Agent namespacing: each agent has fleet-prefixed username for cross-fleet disambiguation
- Shared Plane: two fleets can work on the same Plane project without conflict
- Cross-fleet communication: federation protocol for fleet-to-fleet coordination
- Machine identity: fleet knows what machine it runs on (for multi-machine deployment)

## Done When

Derived from the Goals section above; each goal is a verifiable end-state. Epic is done when all of these hold AND the common verification gates at the bottom pass.

- [ ] Fleet identity: fleet number, fleet name, agent prefix (alpha-architect vs beta-architect)
- [ ] Agent namespacing: each agent has fleet-prefixed username for cross-fleet disambiguation
- [ ] Shared Plane: two fleets can work on the same Plane project without conflict
- [ ] Cross-fleet communication: federation protocol for fleet-to-fleet coordination
- [ ] Machine identity: fleet knows what machine it runs on (for multi-machine deployment)

**Common verification gates:**

- [ ] `pytest fleet/tests/ -v` — 0 failures
- [ ] `python3 tools/lint.py --summary` — no new issues introduced
- [ ] All artifacts committed + linked from the epic's Phases section (if present)
- [ ] PO review + approval before marking `status: done`


## Existing Foundation

- config/fleet-identity.yaml — fleet.id ("alpha"), fleet.name ("Fleet Alpha"), fleet.number (1)
- config/agent-identities.yaml — agent display names, usernames
- fleet/core/federation.py — load_fleet_identity(), FleetIdentity dataclass
- fleet/mcp/context.py — FleetMCPContext.namespaced_agent (fleet prefix + agent name)
- fleet/core/cluster_peering.py — FUTURE schema for multi-machine
- setup.sh Step 0c — generates fleet_id, machine_id, agent_prefix

## Phases

### Phase 0: Research

- [ ] Audit current federation code — what's schema only vs functional
- [ ] Research how Plane handles multi-source issue creation (conflict resolution?)
- [ ] Document what a second fleet deployment looks like (different machine? same machine?)
- [ ] Research cross-fleet communication patterns (Plane comments? board memory? IRC?)

### Phase 1: Design

- [ ] Design fleet identity propagation (fleet number → agent names → commits → PRs → IRC)
- [ ] Design Plane namespacing (fleet prefix in issue labels, comments, assignments)
- [ ] Design cross-fleet coordination protocol (shared board memory? separate boards?)
- [ ] Design machine identity for multi-machine deployment

### Phase 2: Implement

- [ ] Wire fleet identity into all agent files (IDENTITY.md template variables)
- [ ] Wire fleet prefix into Plane operations (plane_sync.py)
- [ ] Wire fleet prefix into IRC messages (irc_client.py)
- [ ] Build cross-fleet discovery (fleet A sees fleet B's agents in Plane)

### Phase 3: Test & Validate

- [ ] Test second fleet deployment (different config, same Plane)
- [ ] Test cross-fleet Plane interaction (no conflicts)
- [ ] Test agent identity uniqueness across fleets

## Relationships

- DEPENDS_ON: E001 (Directive Chain — identity files carry fleet prefix)
- RELATES_TO: E013 (IaC — federation config must persist)
- RELATES_TO: E009 (Signatures — signatures carry fleet identity)
