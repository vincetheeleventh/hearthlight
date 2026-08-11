# Hearthlight — Sessions & Threads

How "go back to a separate thread" actually works, since Hermes and Notion are two systems.

## The model
- **The real thread is a Hermes session.** Hermes auto-saves every conversation as a session with full history, a title, and full-text search across all of them. That's the resumable thing.
- **The Notion Threads row is its readable mirror** — a row in the "Hearthlight Threads" database (under the pilot page), holding the thread's session title, status, summary, working notes, and daily journal.
- You browse on Notion; you resume in Hermes.

## Getting real threads on Telegram (the important bit)
By default, a Telegram DM is **one rolling session** — everything blurs together. To get separate threads:

**Use a Telegram forum + topics.** Each forum **topic** becomes its own Hermes session (`group:<chat_id>:<thread_id>`). So:
1. Make the Hearthlight chat a forum (group with Topics enabled), or use Bot API topic mode.
2. One topic per thread — one per project and one per build workstream: "Film — Yu-Gi-Oh!",
   "Build — Hearthlight", "Feature — Notion logging".
3. In each topic, run `/title <name>` once so the session has a stable, resumable name.

Now each topic is a real thread: its own context, its own history, resumable by name. Switching topics switches threads cleanly.

**CLI alternative:** `hermes -p hearthlight -r "yugioh"` resumes that session from the terminal. `/new` starts a fresh thread; `/title` names it.

## Finding and resuming
- List: `hermes -p hearthlight sessions list`
- Resume by name: `hermes -p hearthlight -r "hearthlight-build"`
- The agent also has `session_search` — ask it "what did we decide about the audio fork?" and it searches all past threads (FTS5) before asking you to repeat yourself.

## Threads seeded as Notion rows
| Thread | Type | Hermes session title |
|---|---|---|
| Film: Yu-Gi-Oh! — The Warrior Returning Alive | Project | `yugioh` |
| Pilot: McConaughey — Don't Half Ass It | Project | `mcconaughey-pilot` |
| Build: Hearthlight system | Feature | `hearthlight-build` |

`yugioh` is the v1 film (`GOALS.md`). Create a session by opening a topic and running `/title <name>`.

## Discipline that keeps it clean
- One topic = one thread = one session. Don't discuss the pilot in the build topic.
- Name every thread (`/title`) — unnamed sessions are hard to find later.
- New project/feature → make a topic, `/title` it, and tell Hearthlight to add a Threads row (it uses `hearthlight-notion-log`).
- `session_reset` policy: keep it `none` for this profile (config), so threads don't auto-expire mid-project. (Active sessions are never auto-pruned regardless.)

## Why not just "Notion pages are the threads"?
Considered and rejected (June 2026): Notion would hold *notes about* a thread but couldn't *replay* the conversation with full context. Sessions give true resume + cross-thread search; Notion gives the browsable map. Both, not either.
