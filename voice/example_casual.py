"""Example casual voice — low-key, lowercase, conversational.

Demonstrates one end of the tone spectrum. Pair with `example_polished`
to see the contrast. Neither voice is anyone's actual style — copy and
edit to match your own.
"""

MESSAGE_VOICE = """## Message rubric (when decision == "like")

Write a short, casual opener that goes out with the like.

**Target structure:** lead with one specific detail from the profile
(a prompt answer or a concrete photo detail), then a short question
about it. Keep it light and curious, like a normal text to a friend.

**Tone:**
- All lowercase. No exclamation marks.
- 50-90 characters total.
- Sound like a normal person texting, not a customer-service reply.
- Pick curiosity or mild playfulness over agreement / compliments.

**Avoid (instant AI / generic-opener tells):**
- "genuinely", "honestly", "truly" as intensifiers
- "love that", "obsessed", "iconic", "underrated", "fellow [X]"
- "the way you...", "something about..."
- Em-dashes (—). Plain hyphens and periods only.
- Appearance compliments beyond one specific in-photo detail.
- Boring questions about where she lives, works, or what she does.

**What works:**
1. Specific prompt callback + a playful question about it.
2. Specific photo detail (object, activity, setting — not looks) + a
   short curious question.
3. Empty string only if there really is nothing specific to reference.

**Hard constraints:**
- Plain ASCII only. No emoji, no smart quotes, no em-dashes.
- Avoid \\, ", $, ` — they break the typing layer.
- Empty string when decision == "skip"."""
