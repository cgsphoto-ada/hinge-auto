"""Post run results to Discord via webhook.

Requires DISCORD_WEBHOOK_URL in the environment. No-op when unset.
The cron agent already handles photo uploads; this just sends a quick
stats embed so results show up in the channel immediately.
"""

import json
import os
import time
from urllib import request as urllib_request


def _send_embed(webhook_url: str, embed: dict) -> None:
    """Send a single embed payload to the Discord webhook."""
    body = json.dumps({"embeds": [embed]}).encode("utf-8")
    req = urllib_request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib_request.urlopen(req)
    except urllib_request.HTTPError as e:
        print(f"[report] webhook embed failed: {e.code} {e.read().decode()[:200]}")


def post_run(likes_sent: int, profiles_seen: int, skips: int,
             total_cost: float, total_duration_s: float,
             liked_profiles: list[dict] | None = None) -> None:
    """Post a quick stats embed to the configured Discord webhook.

    Reads DISCORD_WEBHOOK_URL from the environment. No-op when unset.
    """
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return  # silent no-op

    embed = {
        "title": "Hinge Auto — Run Complete",
        "color": 0x57F287,
        "fields": [
            {"name": "👀 Profiles Seen", "value": str(profiles_seen), "inline": True},
            {"name": "❤️ Likes Sent",    "value": str(likes_sent),    "inline": True},
            {"name": "⏭️ Skipped",       "value": str(skips),         "inline": True},
        ],
        "footer": {"text": f"${total_cost:.2f} · {total_duration_s:.0f}s"},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    }

    _send_embed(webhook_url, embed)
