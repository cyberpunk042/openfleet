#!/usr/bin/env bash
set -euo pipefail

# Set up local IRC for fleet observation.
# Installs miniircd, configures OpenClaw IRC channel, binds agents.
# Called by setup.sh or run standalone.
#
# After setup:
#   - IRC server runs on localhost:6667
#   - All fleet agents post to #fleet channel
#   - Connect with any IRC client: irssi, weechat, or web client
#   - make irc-connect (opens weechat if installed, else prints instructions)

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
IRC_PORT="${FLEET_IRC_PORT:-6667}"
IRC_CHANNEL="${FLEET_IRC_CHANNEL:-#fleet}"
IRC_NICK="${FLEET_IRC_NICK:-fleet-bot}"
IRC_PID_FILE="$FLEET_DIR/.irc.pid"

echo "=== Setting Up Fleet IRC ==="

# 1. Install miniircd if not available
echo "1. Checking IRC daemon..."
if command -v miniircd >/dev/null 2>&1; then
    echo "   miniircd: OK"
elif python3 -c "import miniircd" 2>/dev/null; then
    echo "   miniircd: OK (Python module)"
else
    echo "   Installing miniircd..."
    pip install miniircd --quiet 2>/dev/null || pip install miniircd --quiet --break-system-packages 2>/dev/null || {
        echo "   FAIL: Could not install miniircd"
        echo "   Install manually: pip install miniircd"
        exit 1
    }
    echo "   miniircd: installed"
fi

# 2. Start IRC daemon if not running
echo "2. Starting IRC daemon on port $IRC_PORT..."
if ss -tlnp 2>/dev/null | grep -q ":${IRC_PORT}"; then
    echo "   Already running on port $IRC_PORT"
else
    # Find miniircd executable or use Python module
    MINIIRCD_CMD=""
    if command -v miniircd >/dev/null 2>&1; then
        MINIIRCD_CMD="miniircd"
    else
        # Try to find the installed script
        MINIIRCD_PATH=$(python3 -c "import miniircd, os; print(os.path.dirname(miniircd.__file__))" 2>/dev/null)
        if [[ -n "$MINIIRCD_PATH" && -f "$MINIIRCD_PATH/miniircd.py" ]]; then
            MINIIRCD_CMD="python3 $MINIIRCD_PATH/miniircd.py"
        else
            MINIIRCD_CMD="python3 -m miniircd"
        fi
    fi

    $MINIIRCD_CMD --ports "$IRC_PORT" --motd "OpenClaw Fleet IRC — connect to $IRC_CHANNEL" &
    IRC_PID=$!
    echo "$IRC_PID" > "$IRC_PID_FILE"
    sleep 2

    if kill -0 "$IRC_PID" 2>/dev/null; then
        echo "   IRC daemon started (PID $IRC_PID)"
    else
        echo "   FAIL: IRC daemon did not start"
        exit 1
    fi
fi

# 3. Configure OpenClaw IRC channel
echo "3. Configuring OpenClaw IRC channel..."
python3 -c "
import json

with open('$OPENCLAW_CONFIG') as f:
    cfg = json.load(f)

channels = cfg.setdefault('channels', {})
irc = channels.get('irc', {})
accounts = irc.get('accounts', [])

# Check if fleet account already exists
fleet_account = None
for acc in accounts:
    if acc.get('id') == 'fleet':
        fleet_account = acc
        break

# OpenClaw expects accounts as a record keyed by account ID, not an array
channels['irc'] = {
    'accounts': {
        'fleet': {
            'host': 'localhost',
            'port': $IRC_PORT,
            'tls': False,
            'nick': '$IRC_NICK',
            'channels': ['$IRC_CHANNEL'],
            'dmPolicy': 'open',
            'allowFrom': ['*'],
        }
    }
}
print('   IRC channel configured')

# Set channel defaults for fleet notifications
defaults = channels.setdefault('defaults', {})
defaults.setdefault('heartbeat', {}).update({
    'showOk': False,
    'showAlerts': True,
    'useIndicator': True,
})

with open('$OPENCLAW_CONFIG', 'w') as f:
    json.dump(cfg, f, indent=2)
"

# 4. Bind agents to IRC channel
echo "4. Binding agents to IRC..."
AGENTS=$(openclaw agents list 2>/dev/null | grep "^-" | sed 's/^- //' | awk '{print $1}')

for agent in $AGENTS; do
    # Skip main and gateway agents
    [[ "$agent" == "main" ]] && continue
    [[ "$agent" == mc-gateway-* ]] && continue

    # Check if already bound
    BINDINGS=$(openclaw agents bindings 2>/dev/null | grep "$agent.*irc" || true)
    if [[ -n "$BINDINGS" ]]; then
        continue
    fi

    openclaw agents bind --agent "$agent" --bind "irc:fleet" 2>/dev/null || true
done
echo "   Agents bound to IRC (irc:fleet)"

echo ""
echo "=== IRC Setup Complete ==="
echo ""
echo "IRC Server: localhost:$IRC_PORT"
echo "Channel:    $IRC_CHANNEL"
echo "Bot nick:   $IRC_NICK"
echo ""
echo "Connect with any IRC client:"
echo "  weechat:  /server add fleet localhost/$IRC_PORT && /connect fleet && /join $IRC_CHANNEL"
echo "  irssi:    /connect localhost $IRC_PORT && /join $IRC_CHANNEL"
echo "  Or:       make irc-connect"
echo ""
echo "After connecting, restart the gateway to activate the channel:"
echo "  make gateway-restart"