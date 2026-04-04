# OpenArms — Privacy-First OpenClaw Fork

## Summary

OpenArms is a fork of [OpenClaw](https://github.com/openclaw/openclaw) (MIT licensed) with all identifying fingerprints stripped. It exists as a local repo at `../openarms`, eventually pushed to a private remote.

The openclaw-fleet IaC installs OpenArms as its vendor instead of OpenClaw. Mission Control and all fleet logic remain in openclaw-fleet — OpenArms is only the engine replacement.

## Problem

Starting April 4 2026, Anthropic enforces separate billing for third-party harnesses. Claude Code will attempt to detect OpenClaw usage through telemetry signals. The fleet's operations should be private — each agent session should be indistinguishable from the PO using Claude Code directly.

## Threat Model

OpenClaw leaves fingerprints across 6 categories that Anthropic can detect:

| Category | Detection Signal | Source File(s) |
|----------|-----------------|----------------|
| Device identity | Ed25519 keypair + device ID sent in gateway handshake | `src/infra/device-identity.ts` |
| User-Agent | `"openclaw"` in HTTP headers | `src/infra/provider-usage.fetch.claude.ts`, `src/plugins/provider-usage.fetch.codex.ts` |
| Client handshake | clientName, displayName, version, instanceId, deviceFamily, platform | `src/gateway/client.ts` (lines 461-484) |
| Node registration | clientName, displayName, version, platform, instanceId | `src/node-host/runner.ts` (lines 181-200) |
| OAuth headers | `anthropic-version`, `User-Agent: "openclaw"` on usage endpoint | `src/infra/provider-usage.fetch.claude.ts` (lines 115-177) |
| Branding | "openclaw" strings in package name, config paths, references | Throughout codebase |

## Scope

OpenArms modifies **only** the OpenClaw source to remove fingerprints. Six changes:

### 1. Device Identity Removal
- **File:** `src/infra/device-identity.ts`
- **Action:** Remove Ed25519 keypair generation, device ID computation, `device.json` storage
- **Effect:** No cryptographic device fingerprint, no signing in gateway handshake
- **Also:** `buildDeviceAuthPayloadV3()` in `src/gateway/client.ts` (lines 440-451) — skip device signing in `sendConnect()`

### 2. User-Agent Stripped
- **File:** `src/infra/provider-usage.fetch.claude.ts` (line 125)
- **File:** `src/plugins/provider-usage.fetch.codex.ts` (line 55)
- **Action:** Remove `"User-Agent": "openclaw"` header, or replace with generic browser-like string
- **Effect:** HTTP requests don't self-identify as OpenClaw

### 3. Client Handshake Metadata Stripped
- **File:** `src/gateway/client.ts` (lines 461-484)
- **Action:** Remove or anonymize: `clientName`, `displayName`, `version`, `instanceId`, `deviceFamily`, `platform`, `mode`
- **Effect:** Gateway connections carry no identifying client metadata

### 4. Node Registration Stripped
- **File:** `src/node-host/runner.ts` (lines 181-200)
- **Action:** Remove identifying metadata from node pairing (clientName, displayName, version, platform, instanceId)
- **Effect:** Node host registration carries no identifying information

### 5. OAuth Headers Cleaned
- **File:** `src/infra/provider-usage.fetch.claude.ts` (lines 115-177)
- **Action:** Remove `"User-Agent": "openclaw"` and `"anthropic-version"` headers from OAuth usage API calls
- **Effect:** Usage quota checks don't identify the caller as OpenClaw

### 6. "openclaw" Strings Replaced Throughout
- **Action:** Global find-replace of "openclaw" branding — package name, config directory paths (`~/.openclaw/`), import references, comments, error messages
- **Replacement:** "openarms" where a name is needed, removed where it's just branding
- **Config path:** `~/.openclaw/` → `~/.openarms/`
- **Package name:** `openclaw` → `openarms`

## What OpenArms Does NOT Change

- No changes to Mission Control (stays in openclaw-fleet vendor)
- No changes to fleet orchestrator, MCP tools, or agent logic
- No changes to how Claude Code is invoked (that's fleet IaC responsibility)
- No new architecture, no new components, no spawner abstraction
- No changes to functionality — OpenArms does everything OpenClaw does, minus the fingerprints

## Out of Scope (Fleet IaC — Separate Work)

The following are real concerns but belong to openclaw-fleet, not OpenArms:

- Gateway rewrite (how fleet invokes Claude Code)
- Workspace directory naming (`workspace-mc-{uuid}` patterns)
- Fleet env var sanitization (`FLEET_AGENT`, `FLEET_TASK_ID` in MCP config)
- `--append-system-prompt`, `--output-format json` CLI flag cleanup
- HTTP header cleanup in fleet Python code (`X-Title`, `HTTP-Referer`)

These will be addressed in a separate fleet IaC spec after OpenArms is ready.

## Implementation Approach

1. Fork OpenClaw source into `../openarms`
2. Apply the 6 changes listed above
3. Build and verify it runs
4. Update openclaw-fleet IaC to install from `../openarms` instead of npm
5. Push to private remote when ready

## Verification

After changes, verify zero fingerprints by:
- Grep for "openclaw" in the entire openarms repo — should return zero results
- Confirm `~/.openclaw/` directory is not created
- Confirm `~/.openarms/identity/device.json` is NOT created
- Inspect outbound HTTP headers during a session — no "openclaw" User-Agent
- Inspect gateway handshake — no identifying client metadata
