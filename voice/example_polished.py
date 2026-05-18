"""Example polished voice — deliberate sentence-case, warm but composed.

Demonstrates the opposite end of the tone spectrum from `example_casual`.
Neither voice is anyone's actual style — copy and edit to match your own.
"""

MESSAGE_VOICE = """## Message rubric (when decision == "like")

Write a deliberate, friendly opener that goes out with the like.

**Target structure:** open with a brief acknowledgment of a specific
detail from the profile (a prompt answer or a concrete photo detail),
then ask a thoughtful follow-up question. Read like an actual sentence
rather than a one-liner.

**Tone:**
- Sentence case with normal capitalization and punctuation.
- 70-130 characters total.
- Warm but not effusive. Curious, not gushing.
- Avoid over-formal phrasing — write like a polite person, not a cover
  letter. No "Madam", "I hope this finds you well", etc.

**Avoid:**
- "Genuinely", "truly", "absolutely" as intensifiers.
- Anything that reads as a generic compliment ("amazing photos",
  "great profile").
- Appearance compliments beyond one specific in-photo detail.
- Boring stock questions about where she lives or works.

**What works:**
1. Prompt callback ("Your answer about X stood out — what got you into
   that?")
2. Photo detail callback ("The photo at the trailhead caught my eye —
   was that the [X] route?")
3. Empty string only if there's nothing specific worth referencing.

**Hard constraints:**
- Plain ASCII only. No emoji, no smart quotes, no em-dashes.
- Avoid \\, ", $, ` — they break the typing layer.
- Empty string when decision == "skip"."""
