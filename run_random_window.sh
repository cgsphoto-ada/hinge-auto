#!/usr/bin/env bash
# Run hinge-auto at a random offset within the current hour.
# Intended for an external cron that fires every hour at :00.
#
# Usage: add to system crontab:
#   0 * * * * /home/ada/.openclaw/workspace/hinge-auto/run_random_window.sh
#
# Each hour picks a random delay 0-30min, sleeps, then runs the bot.
# Combined with the 0-2 random like cap, every run looks different.
# Sends notifications to #hinge-bot via webhook.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load webhook URL from .env
source /dev/stdin <<< "$(grep '^DISCORD_WEBHOOK_URL=' .env 2>/dev/null || echo 'DISCORD_WEBHOOK_URL=')"
WEBHOOK="${DISCORD_WEBHOOK_URL:-}"

# Figure out the next :00 hour
NEXT_HOUR=$(date -d 'next hour' '+%I:%M %p')

# Random delay 0-30 minutes (in seconds)
delay=$((RANDOM % 1800))
start_time=$(date -d "+${delay} seconds" '+%H:%M')

# Notify: run starting soon
echo "[$(date)] Will run at ~${start_time} (${delay}s delay)"
if [ -n "$WEBHOOK" ]; then
    curl -s -o /dev/null -X POST "$WEBHOOK" \
        -H "Content-Type: application/json" \
        -H "User-Agent: HingeAuto" \
        -d "{\"content\":\"⏰ **Next run:** ~${start_time} (next hour: ${NEXT_HOUR})\"}"
fi

sleep "$delay"

# Notify: starting now
echo "[$(date)] Starting run..."
if [ -n "$WEBHOOK" ]; then
    curl -s -o /dev/null -X POST "$WEBHOOK" \
        -H "Content-Type: application/json" \
        -H "User-Agent: HingeAuto" \
        -d '{"content":"🚀 **HingeAuto run starting...**"}'
fi

source .venv/bin/activate
python -u main.py --mode carlos 2>&1
EXIT_CODE=$?

# Notify: done
echo "[$(date)] Done (exit $EXIT_CODE)"
if [ -n "$WEBHOOK" ]; then
    if [ "$EXIT_CODE" -eq 0 ]; then
        curl -s -o /dev/null -X POST "$WEBHOOK" \
            -H "Content-Type: application/json" \
            -H "User-Agent: HingeAuto" \
            -d '{"content":"✅ **HingeAuto run complete**"}'
    else
        curl -s -o /dev/null -X POST "$WEBHOOK" \
            -H "Content-Type: application/json" \
            -H "User-Agent: HingeAuto" \
            -d "{\"content\":\"❌ **HingeAuto run failed** (exit $EXIT_CODE)\"}"
    fi
fi

exit $EXIT_CODE
