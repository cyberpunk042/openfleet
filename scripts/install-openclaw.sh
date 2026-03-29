#!/usr/bin/env bash
set -euo pipefail

# Install OpenClaw if not already installed.
# Uses npm global install.

echo "=== Installing OpenClaw ==="

if command -v openclaw >/dev/null 2>&1; then
    VERSION=$(openclaw --version 2>/dev/null | head -1 || echo "unknown")
    echo "  OpenClaw already installed: $VERSION"
else
    echo "  Installing openclaw via npm..."
    npm install -g openclaw 2>/dev/null || {
        echo "  Trying with sudo..."
        sudo npm install -g openclaw 2>/dev/null || {
            echo "  ERROR: Could not install openclaw. Install manually: npm install -g openclaw"
            exit 1
        }
    }
    echo "  OpenClaw installed: $(openclaw --version 2>/dev/null | head -1)"
fi