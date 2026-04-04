# OpenArms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork OpenClaw into a local `../openarms` repo with all identifying fingerprints stripped — device identity, User-Agent, client handshake, node registration, OAuth headers, and all "openclaw" branding replaced with "openarms".

**Architecture:** Clone the vendored OpenClaw source, apply 6 targeted changes to TypeScript source files, then do a global rename of "openclaw" → "openarms" across the codebase. Build and verify.

**Tech Stack:** TypeScript, Node.js, pnpm, tsdown (bundler)

**Spec:** `docs/superpowers/specs/2026-04-03-openarms-design.md`

---

## File Structure

All work happens in `../openarms/` (a new local git repo cloned from `vendor/openclaw/`).

**Files to modify (targeted changes):**
- `src/infra/device-identity.ts` — gut device identity generation and signing
- `src/infra/provider-usage.fetch.claude.ts` — strip User-Agent and identifying headers
- `src/gateway/client.ts` — strip client handshake metadata and device auth
- `src/node-host/runner.ts` — strip node registration metadata
- `src/version.ts` — update version resolution to use OPENARMS_* env vars

**Files to rename (global):**
- `package.json` — name, bin, homepage, repository
- `openclaw.mjs` → `openarms.mjs`
- `src/config/paths.ts` — `~/.openclaw` → `~/.openarms`
- `src/infra/openclaw-root.ts` → `src/infra/openarms-root.ts`
- `src/infra/openclaw-exec-env.ts` → `src/infra/openarms-exec-env.ts`
- `src/infra/tmp-openclaw-dir.ts` → `src/infra/tmp-openarms-dir.ts`
- `src/config/types.openclaw.ts` → `src/config/types.openarms.ts`
- All `OPENCLAW_*` env var references → `OPENARMS_*`
- All string literals, comments, error messages containing "openclaw"

---

### Task 1: Initialize OpenArms Repo

**Files:**
- Create: `../openarms/` (git repo)

- [ ] **Step 1: Copy vendor source to new repo**

```bash
cp -r /home/jfortin/openclaw-fleet/vendor/openclaw /home/jfortin/openarms
cd /home/jfortin/openarms
rm -rf .git
git init
```

- [ ] **Step 2: Verify the copy is intact**

```bash
cd /home/jfortin/openarms
ls package.json src/infra/device-identity.ts src/gateway/client.ts src/node-host/runner.ts
```

Expected: all files exist.

- [ ] **Step 3: Install dependencies**

```bash
cd /home/jfortin/openarms
pnpm install
```

Expected: dependencies installed successfully.

- [ ] **Step 4: Verify it builds in its current state**

```bash
cd /home/jfortin/openarms
pnpm build
```

Expected: build succeeds — this is our baseline.

- [ ] **Step 5: Initial commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "chore: initial fork from openclaw 2026.3.26"
```

---

### Task 2: Remove Device Identity Generation

**Files:**
- Modify: `src/infra/device-identity.ts`
- Modify: `src/gateway/client.ts` (lines ~440-451, device auth payload)

- [ ] **Step 1: Gut device-identity.ts**

Replace the entire file content. Keep the type exports so downstream code compiles, but make all functions no-ops that return null/undefined.

```typescript
// src/infra/device-identity.ts
// Device identity stripped — OpenArms does not generate or transmit device fingerprints.

import { createHash } from "node:crypto";

export interface DeviceIdentity {
  deviceId: string;
  publicKeyPem: string;
  privateKeyPem: string;
}

/** Returns null — no device identity is generated or stored. */
export function loadOrCreateDeviceIdentity(): DeviceIdentity | null {
  return null;
}

/** No-op — returns empty string. */
export function signDevicePayload(
  _privateKeyPem: string,
  _payload: string,
): string {
  return "";
}

/** No-op — always returns false. */
export function verifyDeviceSignature(
  _publicKey: string,
  _payload: string,
  _signature: string,
): boolean {
  return false;
}

/** No-op — returns empty string. */
export function normalizeDevicePublicKeyBase64Url(
  _publicKeyPemOrRaw: string,
): string {
  return "";
}

/** No-op — returns empty string. */
export function deriveDeviceIdFromPublicKey(
  _publicKeyPemOrRaw: string,
): string {
  return "";
}

/** No-op — returns empty string. */
export function publicKeyRawBase64UrlFromPem(_pem: string): string {
  return "";
}
```

- [ ] **Step 2: Strip device auth from gateway client sendConnect()**

In `src/gateway/client.ts`, find the `buildDeviceAuthPayloadV3()` call inside `sendConnect()` (around lines 440-460). The device payload is built and added to ConnectParams. Neutralize it:

Find this block (approximate — look for `buildDeviceAuthPayloadV3` or `device:` in the connect params):

```typescript
    // Build device auth payload
    const devicePayload = this.opts.deviceIdentity
      ? buildDeviceAuthPayloadV3({
```

Replace the entire device section so that `device` is always `undefined` in the connect params:

```typescript
    // Device identity stripped — no fingerprint transmitted
    const deviceField = undefined;
```

Then in the ConnectParams object below, ensure the `device` field uses `deviceField` (or simply remove the `device` property from the params object).

- [ ] **Step 3: Verify it compiles**

```bash
cd /home/jfortin/openarms
pnpm build
```

Expected: build succeeds. If there are type errors from callers expecting non-null DeviceIdentity, fix them by adding null checks.

- [ ] **Step 4: Commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "security: remove device identity generation and transmission"
```

---

### Task 3: Strip User-Agent and OAuth Headers

**Files:**
- Modify: `src/infra/provider-usage.fetch.claude.ts`

- [ ] **Step 1: Strip identifying headers from OAuth usage fetch**

In `src/infra/provider-usage.fetch.claude.ts`, find the `fetchClaudeUsage()` function. It calls `https://api.anthropic.com/api/oauth/usage` with headers including `"User-Agent": "openclaw"` and `"anthropic-version": "2023-06-01"`.

Find:
```typescript
      "User-Agent": "openclaw",
```

Replace with:
```typescript
      "User-Agent": "node",
```

Find:
```typescript
      "anthropic-version": "2023-06-01",
```

Remove this line entirely (or keep it if the API requires it — test after).

- [ ] **Step 2: Strip identifying headers from claude.ai web fallback**

In the same file, the `fetchClaudeWebUsage()` function calls `claude.ai/api/organizations` and `/usage`. Check for any "openclaw" User-Agent there too. If present, replace with `"node"`.

- [ ] **Step 3: Search for any other User-Agent headers in the codebase**

```bash
cd /home/jfortin/openarms
grep -rn '"User-Agent"' src/ --include='*.ts' | grep -i 'openclaw\|codex'
```

Fix any remaining hits.

- [ ] **Step 4: Verify it compiles**

```bash
cd /home/jfortin/openarms
pnpm build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "security: strip identifying User-Agent and OAuth headers"
```

---

### Task 4: Strip Client Handshake Metadata

**Files:**
- Modify: `src/gateway/client.ts` (lines ~461-490, ConnectParams builder)

- [ ] **Step 1: Anonymize the client block in sendConnect()**

In `src/gateway/client.ts`, inside `sendConnect()`, find the ConnectParams object. It contains a `client` block like:

```typescript
      client: {
        id: this.opts.clientName,
        displayName: this.opts.clientDisplayName,
        version: VERSION,
        platform: this.opts.platform,
        deviceFamily: this.opts.deviceFamily,
        mode: this.opts.mode,
        instanceId: this.opts.instanceId,
      },
```

Replace with minimal, non-identifying values:

```typescript
      client: {
        id: "node",
        displayName: undefined,
        version: undefined,
        platform: undefined,
        deviceFamily: undefined,
        mode: this.opts.mode,
        instanceId: undefined,
      },
```

Keep `mode` because the gateway needs it for routing. Everything else is stripped.

- [ ] **Step 2: Verify it compiles**

```bash
cd /home/jfortin/openarms
pnpm build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "security: strip client handshake metadata from gateway connect"
```

---

### Task 5: Strip Node Registration Metadata

**Files:**
- Modify: `src/node-host/runner.ts` (lines ~181-220)

- [ ] **Step 1: Anonymize node host registration**

In `src/node-host/runner.ts`, find the `GatewayClient` constructor call inside `runNodeHost()`. It passes identifying metadata:

```typescript
      clientName: GATEWAY_CLIENT_NAMES.NODE_HOST,
      clientDisplayName: displayName,
      clientVersion: VERSION,
      platform: process.platform,
```

Replace with anonymous values:

```typescript
      clientName: "node",
      clientDisplayName: undefined,
      clientVersion: undefined,
      platform: undefined,
```

- [ ] **Step 2: Remove device identity loading from node host**

In the same function, find:
```typescript
      deviceIdentity: loadOrCreateDeviceIdentity(),
```

Replace with:
```typescript
      deviceIdentity: null,
```

- [ ] **Step 3: Verify it compiles**

```bash
cd /home/jfortin/openarms
pnpm build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "security: strip node registration metadata"
```

---

### Task 6: Global Rename — "openclaw" to "openarms"

This is the largest task. It covers: package name, binary name, config paths, env vars, string literals, file names, and directory names.

**Files:**
- Modify: ~5,400 files across the repo
- Rename: ~160 files/directories

- [ ] **Step 1: Rename package.json essentials**

Edit `package.json`:
- `"name": "openclaw"` → `"name": "openarms"`
- `"homepage"` → remove or set to empty string
- `"bugs.url"` → remove or set to empty string
- `"repository.url"` → remove or set to empty string
- `"bin": { "openclaw": "openclaw.mjs" }` → `"bin": { "openarms": "openarms.mjs" }`
- In `"files"` array: `"openclaw.mjs"` → `"openarms.mjs"`
- In `"exports"`: `"./cli-entry": "./openclaw.mjs"` → `"./cli-entry": "./openarms.mjs"`
- In `"scripts"`: rename any `openclaw` references to `openarms`

- [ ] **Step 2: Rename the entry point file**

```bash
cd /home/jfortin/openarms
mv openclaw.mjs openarms.mjs
```

Update any imports/references to `openclaw.mjs` inside the file itself.

- [ ] **Step 3: Global string replacement — case-sensitive passes**

Run these replacements in order (most specific first to avoid double-replacing):

```bash
cd /home/jfortin/openarms

# Pass 1: Environment variables (SCREAMING_CASE)
find src/ scripts/ apps/ -type f \( -name '*.ts' -o -name '*.mjs' -o -name '*.sh' -o -name '*.json' -o -name '*.swift' -o -name '*.kt' \) \
  -exec sed -i 's/OPENCLAW_/OPENARMS_/g' {} +

# Pass 2: Config paths
find src/ scripts/ apps/ docs/ -type f \( -name '*.ts' -o -name '*.mjs' -o -name '*.sh' -o -name '*.json' -o -name '*.md' \) \
  -exec sed -i 's/\.openclaw/\.openarms/g' {} +

# Pass 3: PascalCase (Swift, Kotlin, class names)
find src/ apps/ -type f \( -name '*.ts' -o -name '*.swift' -o -name '*.kt' \) \
  -exec sed -i 's/OpenClaw/OpenArms/g' {} +

# Pass 4: lowercase in strings, imports, comments
find . -type f \( -name '*.ts' -o -name '*.mjs' -o -name '*.js' -o -name '*.sh' -o -name '*.json' -o -name '*.md' -o -name '*.yml' -o -name '*.yaml' \) \
  ! -path './.git/*' \
  -exec sed -i 's/openclaw/openarms/g' {} +
```

- [ ] **Step 4: Rename files and directories containing "openclaw"**

```bash
cd /home/jfortin/openarms

# Rename files (deepest first to avoid path conflicts)
find . -depth -name '*openclaw*' ! -path './.git/*' | while read f; do
  dir=$(dirname "$f")
  base=$(basename "$f")
  newbase=$(echo "$base" | sed 's/openclaw/openarms/g; s/OpenClaw/OpenArms/g')
  if [ "$base" != "$newbase" ]; then
    mv "$f" "$dir/$newbase"
  fi
done
```

- [ ] **Step 5: Verify no "openclaw" references remain**

```bash
cd /home/jfortin/openarms
grep -ri 'openclaw' --include='*.ts' --include='*.json' --include='*.mjs' --include='*.sh' -l | grep -v '.git/' | head -20
```

Expected: zero results (or only in CHANGELOG.md / historical docs which are acceptable).

- [ ] **Step 6: Verify it builds**

```bash
cd /home/jfortin/openarms
pnpm install  # lockfile may need refresh after package rename
pnpm build
```

Expected: build succeeds.

- [ ] **Step 7: Commit**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "chore: rename openclaw to openarms throughout codebase"
```

---

### Task 7: Final Verification

**Files:**
- None modified — verification only

- [ ] **Step 1: Full grep audit**

```bash
cd /home/jfortin/openarms

# Check for any remaining "openclaw" (case-insensitive) in source
echo "=== Source files ==="
grep -ri 'openclaw' src/ --include='*.ts' -c 2>/dev/null | tail -5
echo "=== Config files ==="
grep -ri 'openclaw' *.json *.mjs -c 2>/dev/null | tail -5
echo "=== Scripts ==="
grep -ri 'openclaw' scripts/ --include='*.sh' -c 2>/dev/null | tail -5
```

Expected: zero matches in source, config, and scripts. CHANGELOG.md and docs/ historical references are acceptable.

- [ ] **Step 2: Verify no device identity files are created**

```bash
# Clean any existing state
rm -rf ~/.openarms/identity/

# Run openarms briefly (if it supports a --version or --help flag)
cd /home/jfortin/openarms
node openarms.mjs --version

# Check no identity was created
ls ~/.openarms/identity/device.json 2>/dev/null && echo "FAIL: device identity created" || echo "PASS: no device identity"
```

Expected: "PASS: no device identity"

- [ ] **Step 3: Verify config path uses ~/.openarms**

```bash
grep -r 'resolveStateDir\|stateDir\|STATE_DIR' /home/jfortin/openarms/src/config/paths.ts | head -5
```

Expected: references to `.openarms`, not `.openclaw`.

- [ ] **Step 4: Build clean dist**

```bash
cd /home/jfortin/openarms
rm -rf dist/
pnpm build
```

Expected: clean build with no errors.

- [ ] **Step 5: Final commit and tag**

```bash
cd /home/jfortin/openarms
git add -A
git commit -m "chore: openarms v1.0.0 — verified clean of all openclaw fingerprints"
git tag v1.0.0
```

---

## Summary

| Task | Description | Estimated Steps |
|------|-------------|-----------------|
| 1 | Initialize repo from vendor source | 5 |
| 2 | Remove device identity | 4 |
| 3 | Strip User-Agent and OAuth headers | 5 |
| 4 | Strip client handshake metadata | 3 |
| 5 | Strip node registration metadata | 4 |
| 6 | Global rename openclaw → openarms | 7 |
| 7 | Final verification | 5 |
| **Total** | | **33 steps** |
