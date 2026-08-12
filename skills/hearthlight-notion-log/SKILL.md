---
name: hearthlight-notion-log
description: "Hearthlight's Notion surfacing — Vince's preferred point of contact. Maintain three surfaces on Notion: working notes (usable artifacts), a daily journal (what got done), and a Threads database (one row per project/feature, linked to its Hermes session). Append-only, rate-limit-safe."
metadata:
  hermes:
    tags: [hearthlight, notion, logging, threads, journal]
    category: hearthlight
---

# Hearthlight — Notion Surfaces

## When to Use
Notion is Vince's preferred point of contact. Surface work there so he can browse and return to it without living in Telegram. Three distinct surfaces — keep them distinct:

1. **Working notes** — artifacts he'll *use*: transcripts ready for storyboarding, the vision brief, research decks, key decisions. Reference material.
2. **Daily journal** — one entry per working day: what got accomplished. Reflective, human-readable.
3. **Threads** — the Threads database; one row per project or feature, each linked to its Hermes session so it's resumable.

These map to the IDs in `projects/{slug}/notion-log.md` (read it first). Requires the Notion MCP (`profile/NOTION-SETUP.md`). If MCP is down, write to local `activity-log.md` and tell Vince — never silently drop.

## Threads = Hermes sessions, mirrored to Notion
The *real* thread (the resumable conversation) lives in Hermes as a **session with a title**; the Notion Threads row is its readable mirror. See `profile/SESSIONS-AND-THREADS.md` for the discipline. In practice:
- Each thread has a Hermes session title (e.g. `mcconaughey-pilot`, `hearthlight-build`). On Telegram, a forum **topic** = its own session; title it with `/title`.
- The Threads database row stores that session title in the **Hermes Session** field, so Vince (or the agent) can resume via `hermes -p hearthlight -r "<title>"`.
- When work happens in a thread, update its row's **Last Active** and append to that thread page's journal/notes — not to a global feed.

## Where each surface writes
- **Working notes** → the relevant thread page's `## Working notes` section (or a linked sub-page for long artifacts like a full transcript). Big transcripts: store the file locally, put a short summary + the local path + key excerpts on Notion, not the whole 10k-word dump (context + rate-limit hygiene).
- **Daily journal** → the thread page's `## Daily journal`, under a `### YYYY-MM-DD` header. One bullet per accomplishment.
- **Threads DB** → create a row when a new project/feature starts; update Status + Last Active as it moves.
- **Milestones** (locked brief, approved shot, key decisions) → also mirror a one-liner to the project log so the production trail stays glanceable.
- The standalone **Activity Log page** (created earlier) remains the optional full chronological feed; the three surfaces above are the primary, curated views Vince asked for.

## Rate-limit & readability discipline
Notion throttles (~3 req/s); naive per-event writes shred the page and hit limits.
- **Batch per turn:** collect the turn's surface-updates, write them in as few calls as possible.
- **One call per logical action**, not per sub-step. A batch of 5 generated images = one journal line, not five.
- **Daily headers** group journal entries; never start a new page per session.
- On write failure: queue to local `activity-log.md`, retry next turn. Local is source of truth, Notion is mirror.

## What NOT to do
- Don't dump raw transcripts/large artifacts into Notion — summary + path + excerpts.
- Don't write secrets, tokens, or the storyteller's private content to Notion (record *that* a transcript exists, not its sensitive body).
- Don't append/delete across threads — each thread's notes stay in its own row.
- Don't collapse the three surfaces into one feed; Vince explicitly wants working-notes vs journal vs threads kept separate.
- Don't let a Notion outage block the pipeline.

## Verification
- New project/feature → a Threads row exists with its Hermes Session title filled.
- Daily work → a journal bullet under today's header in the right thread.
- Usable artifacts → in Working notes (summarized, with local path).
- Milestones mirrored to the dashboard; full feed (if used) on the Activity Log page.
- On MCP failure, entries landed locally and Vince was told.
