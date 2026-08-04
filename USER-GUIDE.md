# Hearthlight — User Guide

How to run a story through the pipeline, from your seat. (One-time install lives in `profile/SETUP.md`; this guide assumes the Hearthlight bot is alive in your Telegram.)

## The shape of the work

You do two things: **direct** and **approve**. Hermes does everything between — and increasingly it also **argues with you** (the critique gate, the shot crew). It's a collaborator, not an intern: it researches, pushes back honestly, remembers your taste, and leaves every charged decision to you. Your time should run ~80% direction/approval, ~20% fiddling. If that inverts, the instructions are wrong, not you — say so and have Hermes propose a skill fix.

The pipeline is a sequence of gates — nothing moves until you say ✅:

```
Distribution Spec (decide format FIRST)
  └─ Rant → GATE 0 Vision Brief → GATE 1 Outline → (Critique pass) → GATE 2 Mise-en-scène
        → Shot crew designs shots → GATE 3 Images → GATE 4 Storyboard → GATE 5 Clips → your edit
```

## Before a new story: the Distribution Spec

Decide **format first** — platform, aspect ratio, length, captions. Say e.g. *"this is a 9:16 vertical short, ~110s, burned-in captions."* This isn't paperwork: aspect ratio is a **composition law**, not an export setting — a wide shot drawn for 16:9 doesn't survive a vertical crop, it has to be re-conceived. Deciding late means redrawing. (Skill: `hearthlight-distribution-spec`.)

## Starting a new story

1. **Drop source material** into the project folder from Windows Explorer:
   `C:\Users\vxi\AppData\Local\hermes\Story Studio\projects\{project}\00-source\`. Interview video/audio/transcript here. Big files always by folder — bots can't receive files over ~20 MB. (For a giant file, send it to your Telegram **Saved Messages** first, then download on PC and drop in the folder.)
2. **Rant.** Voice-note the bot, off the cuff. Tell it the story you're pointing at and what you see.
3. The bot transcribes and the **ideation loop** begins.

## Stage 1.5 — Ideation (multi-turn, take your time)

Lasts as long as you want — multiple voice notes, across days. Hermes does three things, each rationed:
- **Dig** — a question or two deepening what you mean.
- **Offer** — era knowledge as storytelling opportunities ("1989 dorm halls had shared wall phones — a private call in a public place. Opportunity?"). Say *take it*, *park it*, or *no*. Declined offers never return.
- **Reflect** — play back what's accumulating.

Useful phrases: "**Research [direction]**", "**Park that**", "**Just listen**" (capture only), "**Consolidate**" / "**lock it**" (ends ideation, compiles the doc).

Then the **selects pass**: keep / kill / merge per item, name the primary arc in one sentence. Killed ideas go to the boneyard (never deleted). You get a one-page **Vision Brief** — read it asking: *is this still my story?* ✅ = Gate 0.

## Stage 2 — Outline, then the Critique pass

- **Outline (Gate 1):** three docs one at a time — Story Arc, Beat Sheet, A/V Script. Watch for `[OPEN SLOT]` markers — creative decisions reserved for you (the detonation image, the withheld turn). Approve each separately; voice-note revisions work.
- **Critique:** before you commit to drawing, ask *"critique this"* — Hermes pressure-tests the *telling* (not the story): buried detonation beats, echo shots, close-up inflation, sentimentality, contrast spine not on the page. It argues once, you keep or reject each note. This is the collaborator earning its seat. (Skill: `hearthlight-critique`.)

## Stage 3 — Mise-en-scène (the Aesthetic Bible) — Gate 2, the sacred one

The ONE aesthetic source of truth every prompt draws from. Two tiers:
- **Tier 1 — LOCKED:** the **style block** (exact ink-and-watercolour wording — a draft awaits your blessing), palette, and character **signature details** + turnarounds. Set in stone; drift from it is the failure.
- **Tier 2 — COMPOSED:** the **world by location** — props, layout, wardrobe, light, vibe per set, grounded in research, finalized by your creative calls.

Plus an **Overview** (the visual thesis): the contrast spine, colour-as-emotion, framing language, motifs. This is where your storyteller's eye lives. Research feeds it (`hearthlight-research`), and reference images become a glanceable Notion report (`hearthlight-reference-report`). **No image generates until this is blessed.** Don't rush it — every minute here saves ten at Stage 4.

## Shot design — the crew

When designing the shot list, Hermes runs a **crew** (in illustration terms): Layout, Value-Light, Background, Continuity/Model, Posing, Motion, Sound, Editor — each tells the story in its dimension. Routine shots it handles in one pass; **contested shots** it delegates the conflicting roles to subagents, then reconciles and shows you the tradeoff (*"Layout wanted a wide for isolation; Continuity flagged it'd lose the eyeline — kept the wide, added the gaze cue"*). Each crew member writes a per-dimension entry into the shot row; the video-prompt writer later compiles those entries into one prompt. **Best watched in the TUI** (`hearthlight` in a terminal, then `/agents`) so you see the crew deliberate. (Skill: `hearthlight-shot-crew`.)

## Stage 4 — Image review (Gate 3)

Images arrive in Telegram batches of 3–5, by beat. Reply per image: ✅ approve (immutable; changes = new versions) · 🔁 *with a note* (regenerate) · ✏️ edit the prompt. If a correction is *general* ("more paper texture at night"), say so — Hermes offers to write it into the rules. Before Gate 3, **spot-check full-res files** — Telegram thumbnails hide drift.
### Adding or removing shots at any stage

Hearthlight Studio can add a shot at the end, insert one between existing shots, or retire a shot during
storyboard, image, video, or edit work. The visible shot number may change; the permanent Shot ID does not.
?Delete shot? retires it: media, prompts, comments, approvals, and versions remain attached and the shot can
be restored. A new spreadsheet must carry the `Shot ID` column. If a regenerated workbook cannot prove a
match, Hearthlight stops for reconciliation instead of moving assets by row number. Full protocol:
`skills/hearthlight-dashboard/references/SHOT-IDENTITY-PROTOCOL.md`.



## Stages 5–6 — Storyboard, timing, and video

- **Storyboard (Gate 4):** per shot — image, VO timestamps, duration, *motion intent* (one move: a push-in, steam, light fading). Figures don't mouth the VO unless you say so.
- **Timing from your hand:** if you've timed panels in **Storyboard Pro**, export a **Final Cut XML with one clip per panel** and drop it in. Hermes reads your exact per-panel durations (the pace you set by ear) and uses them for the shot list, the audio cuts, AND the Seedance clip lengths — one timing source, no re-guessing. (Skill: `hearthlight-timing-intake`.)
- **Watch it back:** Hermes can write a **Final Cut XML you import into DaVinci Resolve** — your panels (hand-drawn now, generated later) held at your timing with the VO synced. Press play, watch the whole story at real pace before any video renders. Same export later carries the animated Seedance clips.
- **Video (Gate 5):** clips render through ComfyUI/RunningHub. Review with ✅/🔁. Watch one thing above all: does it still look *painted*? Photoreal creep is the enemy. Approved clips + VO land in `07-final/` for your edit.

## Notion — your point of contact

Hermes surfaces work to Notion: **working notes** (transcripts, briefs), a **daily journal** (what got done), and a **Threads database** (one row per project/feature). Threads are really Hermes *sessions* — on Telegram, use a **forum topic per thread** and `/title` it, so you can return to "the pilot" or "the build" with full context. (Skill: `hearthlight-notion-log`; details in `profile/SESSIONS-AND-THREADS.md`. Notion needs its MCP wired — `profile/NOTION-SETUP.md`.)

## Version control

- Everything lives natively on Windows (`C:\Users\vxi\AppData\Local\hermes\Story Studio\`) — Cowork and the gateway work on the same files; no syncing.
- **Git** (the instruction layer's history): `_git/GITHUB-SETUP.md`. Versions the reusable system; project media + secrets stay out.
- **After adding/editing skills:** `hearthlight gateway restart`, then `/new` in Telegram so the chat session sees them. (`hearthlight skills list` in WSL is ground truth for what loaded.)

## Where everything lives

`projects/{slug}/` — numbered folders `00-source` → `07-final`. `00-source` is inputs-only, forever. Hand-drawn reference panels → `03-bible/refs/storyboard-panels/`. Nothing exists only in chat. Full conventions: `hearthlight-conventions`.

## When something goes wrong

- **Bot not responding:** WSL → `hearthlight gateway restart`.
- **New skill not showing in Telegram:** `hearthlight gateway restart`, then `/new`. Confirm with `hearthlight skills list`.
- **Drifting images (3+ same cause):** stop — say "drift check". The fix belongs in the Mise-en-scène, not per-image notes.
- **Hermes overstepping** (filling open slots, pushy offers, re-pitching a rejected note): name it; have it written back into the skill. The constitution is yours to amend.
- **Re-explained something twice:** a memory failure. "remember this" / "add this to the rules". Aesthetic verdicts go to `profile/TASTE.md`.

## The covenant, short version

Your improvisation is sacred; the machine catches everything, argues honestly, and asks before adding. Gates fail cheap; skipping them fails expensive. The instruction layer gets smarter every project — correct the system, not just the output.
