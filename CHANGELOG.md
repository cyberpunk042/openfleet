# Changelog

Generated: 2026-03-28T16:16:57Z

## Features

- **fleet**: trace CLI + auth tests — 13 commands, 58 tests (`702595e`)
- **fleet**: self-healing auth — auto-refresh token + restart gateway (`d750dd0`)
- **agents**: project-manager — SCRUM driver & DSPD product owner (`86186d2`)
- **fleet**: board management CLI — info, tasks, cleanup, tags, fields (`94a5ee4`)
- **fleet**: cache wired into MC client + cache management CLI (`31bb085`)
- **fleet**: SQLite cache — persistence, indexing, backup, export/import (`201f05b`)
- **governance**: fleet-ops heartbeat — autonomous board monitoring (`8004328`)
- **fleet**: daemon CLI — sync + monitor in Python, replaces bash daemons (`f18b83a`)
- **fleet**: create-task CLI — complete task lifecycle in Python (`2199516`)
- **fleet**: M139 — dispatch CLI replacing most complex bash script (`6f57679`)
- **fleet**: digest + quality CLI commands, Makefile migration (`e935e1a`)
- **approvals**: status shows approvals, sync handles gate, dispatch improved (`ef90e7f`)
- **approvals**: quality gate — agents create approvals on task completion (`fa8a191`)
- **dispatch**: explicit fleet_read_context call in dispatch message (`4f96b17`)
- **fleet**: M141 — unit tests + Makefile uses fleet CLI (`65c0f87`)
- **fleet**: M139-M140 — CLI layer with status, sync, notify commands (`f20bd32`)
- **fleet**: M137 — templates layer with PR, comment, memory, IRC formatters (`b622a90`)
- **workflow**: tool-only SOUL.md, curl fallback removed from agent view (`787045c`)
- **mcp**: confirmed Fleet MCP tools ARE available to gateway agents (`edaec83`)
- **mcp**: deploy Fleet MCP server to agent workspaces (`8d97d9a`)
- **fleet**: M138 — Fleet MCP Server with 7 native agent tools (`5e5263b`)
- **fleet**: M136 — IRC and GitHub infra clients (`b7a55ec`)
- **fleet**: M135-M136 — infra layer with MC client, config loader, cache interface (`714f20e`)
- **fleet**: M131-M134 — fleet/ Python package with core domain layer (`d97e12e`)
- **ops**: quality enforcement + operational playbook README (`e927763`)
- **governance**: Phase F4 — fleet-ops agent, board monitor, daily digest (`3a9e00d`)
- **lounge**: Phase F3 — The Lounge web IRC client + multi-channel support (`471653e`)
- **comms**: Phase F2 — communication protocol, decision matrix, and 4 intelligence skills (`a27bdca`)
- **skills**: Phase F1 foundation — URL resolver, markdown templates, and 5 formatting skills (`c9996d8`)
- **ops**: sync daemon, IRC notifications on create/merge, automated flow (`766d4f6`)
- **irc**: IRC notification pipeline for fleet events (`d0521e7`)
- **irc**: local IRC server setup for fleet observation (`c7d2107`)
- **ops**: board custom fields, tags, task-PR sync service (`eb9e3bc`)
- **delivery**: agent push + PR workflow, Phase A milestone plan (`4622057`)
- **channels**: add channel configuration script for Discord and IRC (`0329c8b`)
- **skills**: add fleet-specific skills for commit, report, and task workflow (`f7cc128`)
- **trace**: add task tracing for full context navigation (`cf93c8d`)
- **skills**: category/risk metadata, OCMC patches, gateway skill install (`edeef3d`)
- **skills**: skill pack registration, assignment config, and gateway install (`527c035`)
- **skills**: inventory OpenClaw skills and register OCMC marketplace packs (`9b62f0e`)
- **observe**: add real-time WS event monitor and session list (`f30df0e`)
- **standards**: enforce conventional commits and coding standards across fleet (`cb5d6a7`)

## Bug Fixes

- **config**: auto-resolve fleet_dir from package location (`5e49514`)
- **mcp**: tools accept task_id param, auto-discover worktree, robust errors (`e82487c`)
- **mcp**: register fleet MCP server in openclaw.json, not .mcp.json (`de7d6c2`)
- **lounge**: use --password flag for user creation, remove searchEnabled warning (`cab80c2`)
- **sync**: fix unbound variable in daemon startup (`21703ce`)
- **irc**: disable TLS for local miniircd connection (`5596a50`)
- **irc**: correct OpenClaw config format for IRC channel (`689d10a`)
- **workflow**: agents must set pr_url custom field on task completion (`db1eaff`)
- **skills**: symlink fleet skills into MC agent workspaces (`f15465c`)
- **infra**: use pkill -x to avoid self-SIGTERM in gateway-stop [task:f2188949] (`dc309ef`)

## Refactoring

- **makefile**: clean Makefile using fleet CLI as primary interface (`bb5ae1a`)
- **mcp**: tools.py delegates ALL formatting to templates layer (`e2e7017`)

## Documentation

- autonomous driver agents — self-organizing fleet with products (`49b6c44`)
- 5 more architecture designs — framework, events, surfaces, lifecycle, PM (`18a4df6`)
- 5 architecture design documents for fleet command center (`acd45c6`)
- agent command center architecture — smart system in/middleware/out (`9bbc9b1`)
- detailed milestone plans for Phases F1-F5 (`f2c5542`)
- **governance**: add verbatim user quotes as traceability anchors (`2cb550e`)
- fleet governance, quality, and communication architecture (M81-M105) (`94c7978`)
- fleet operations protocol — complete system design (`57d36b1`)
- identify 6 fundamental operational gaps in fleet (`a6607f9`)
- milestone plans for standards, skills, observability, and traceability (`e37c9f6`)

## Tests

- **fleet**: expand test suite — config loader + GH client parsing (`08db3e5`)

## Maintenance

- gitignore fleet-ops credentials and provisioned files (`1af7815`)
- **python**: uv-managed venv with Python 3.11+ and MCP SDK (`c1fbb88`)
- **vendor**: add patch management for OCMC modifications (`a9bb0e4`)
- gitignore skills/ directory (installed by OCMC marketplace) (`d06f410`)

## Other

- milestone: project-manager evaluated fleet backlog via opus (`0bd2a99`)
- milestone: fleet CLI E2E verified — PR #10 via Python-only pipeline (`c94fd89`)
- milestone: full MCP pipeline verified — PR #7 created via fleet tools (`20f55a0`)
- milestone: Fleet MCP tools used by agent in production (`5f3bfc1`)
- M38-M40: Fleet infrastructure — provisioning, dispatch, observation, and project integration (`149ee2d`)
- Fleet autonomy plan — making the fleet work on its own (`f8dec08`)
- M27: NNRT assessment + ocf-tag priorities (`edbf465`)
- M26: ocf-tag alignment with existing ecosystem (`eba059f`)
- + add license (`a00c5eb`)
- Phase 5 milestone plan: M26-M38 (`ea5d5a5`)
- Capture full Accountability Generator vision and development flow (`dfa8f58`)
- M25: Multi-project operations (`fb964f8`)
- M24: Continuous operations — task management through Mission Control (`5462ac2`)
- M23: ocf-tag Intake layer — built by the agent fleet (`3e690e8`)
- M21: Agent specialization — 4 agents produce meaningfully different output (`e42940f`)
- Move gateway to host — not Docker (`892e9ce`)
- M20: Operational loop — sessions + chat execution via Claude Code (`1fd50ac`)
- Add timezone detection to fleet setup (`e258320`)
- Gateway WebSocket protocol + fleet setup — all agents registered (`5092663`)
- Mission Control + Gateway running end-to-end (`b189d6c`)
- Initial scaffold for OpenClaw Fleet (`27570af`)

