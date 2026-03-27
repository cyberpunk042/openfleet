#!/usr/bin/env bash
set -euo pipefail

# Configure an OpenClaw channel for fleet observation.
#
# Usage:
#   bash scripts/configure-channel.sh discord --token <bot-token> --guild <guild-id> --channel <channel-id>
#   bash scripts/configure-channel.sh irc --server <host> --port <port> --nick <nick> --channels "#fleet"
#
# After configuration, restart the gateway: make gateway-restart

FLEET_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

CHANNEL_TYPE="${1:?Usage: configure-channel.sh <discord|irc> [options]}"
shift

case "$CHANNEL_TYPE" in
    discord)
        BOT_TOKEN=""
        GUILD_ID=""
        CHANNEL_ID=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --token) BOT_TOKEN="$2"; shift 2 ;;
                --guild) GUILD_ID="$2"; shift 2 ;;
                --channel) CHANNEL_ID="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        if [[ -z "$BOT_TOKEN" ]]; then
            echo "ERROR: --token required for Discord"
            echo ""
            echo "Setup:"
            echo "  1. Go to https://discord.com/developers/applications"
            echo "  2. Create a new application"
            echo "  3. Go to Bot → Create Bot → Copy Token"
            echo "  4. Enable MESSAGE CONTENT INTENT"
            echo "  5. Invite bot to your server with Send Messages + Read Messages permissions"
            echo "  6. Run: bash scripts/configure-channel.sh discord --token <token> --guild <guild-id> --channel <channel-id>"
            exit 1
        fi

        echo "=== Configuring Discord Channel ==="
        python3 -c "
import json
with open('$OPENCLAW_CONFIG') as f:
    cfg = json.load(f)
cfg.setdefault('channels', {})['discord'] = {
    'accounts': [{
        'id': 'fleet',
        'token': '$BOT_TOKEN',
        'guildId': '$GUILD_ID',
        'channelId': '$CHANNEL_ID',
    }]
}
with open('$OPENCLAW_CONFIG', 'w') as f:
    json.dump(cfg, f, indent=2)
print('Discord channel configured')
print('Restart gateway: make gateway-restart')
"
        ;;

    irc)
        SERVER=""
        PORT="6667"
        NICK="fleet-bot"
        CHANNELS="#fleet"
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --server) SERVER="$2"; shift 2 ;;
                --port) PORT="$2"; shift 2 ;;
                --nick) NICK="$2"; shift 2 ;;
                --channels) CHANNELS="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        if [[ -z "$SERVER" ]]; then
            echo "ERROR: --server required for IRC"
            echo ""
            echo "For local IRC:"
            echo "  1. Install miniircd: pip install miniircd"
            echo "  2. Start: miniircd --ports 6667 &"
            echo "  3. Run: bash scripts/configure-channel.sh irc --server localhost --nick fleet-bot --channels '#fleet'"
            echo ""
            echo "For external IRC:"
            echo "  Run: bash scripts/configure-channel.sh irc --server irc.libera.chat --port 6697 --nick fleet-bot --channels '#your-channel'"
            exit 1
        fi

        echo "=== Configuring IRC Channel ==="
        python3 -c "
import json
with open('$OPENCLAW_CONFIG') as f:
    cfg = json.load(f)
channels_list = '$CHANNELS'.split(',')
cfg.setdefault('channels', {})['irc'] = {
    'accounts': [{
        'id': 'fleet',
        'host': '$SERVER',
        'port': int('$PORT'),
        'nick': '$NICK',
        'channels': channels_list,
        'dmPolicy': 'open',
    }]
}
with open('$OPENCLAW_CONFIG', 'w') as f:
    json.dump(cfg, f, indent=2)
print('IRC channel configured')
print('Restart gateway: make gateway-restart')
"
        ;;

    *)
        echo "Unknown channel: $CHANNEL_TYPE"
        echo "Supported: discord, irc"
        exit 1
        ;;
esac

echo ""
echo "After restart, bind agents to the channel:"
echo "  openclaw agents bind <agent-name> --channel $CHANNEL_TYPE --target <target>"
echo ""
echo "Or bind all fleet agents:"
echo "  for agent in architect software-engineer qa-engineer devops technical-writer ux-designer; do"
echo "    openclaw agents bind \$agent --channel $CHANNEL_TYPE --target <target>"
echo "  done"