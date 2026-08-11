---
doc: README
role: index
authority: canon
owner: agents
updated: 2026-08-04
answers:
  - what this folder is
  - where each part of the system lives
not_here:
  what to read as an agent: AGENTS.md
  how to run a story through it: USER-GUIDE.md
archive: archive/readme.md
---

# Hearthlight Story Studio — Hermes workspace

This folder is the working home of **Hearthlight**, a single-operator AI filmmaking tool: it turns a
director's input — storyboards, spoken vision, narrative beats — into what image and video generation
need, and pairs with the Film Study Tool UI as a visual shot tracker and production dashboard.

`PRODUCT_SPEC.md` is the definition of record. (An older PRD lives in Notion: "PRD — Hearthlight".)

## Layout

```
Story Studio/
  USER-GUIDE.md                    ← how Vince runs a story through the pipeline
  guides/                          ← plain-language guides: assets, shot2video, board2video
  profile/                         ← SETUP, SOUL, NOTION-SETUP, SESSIONS-AND-THREADS for the hearthlight profile
    clients/talefeather/           ← CLIENT layer. Grief/living-legacy cohorts, voice-as-treasure,
                                     the competitive wedge. Loaded ONLY when a project's spec says
                                     `client: talefeather` — never assumed. Most projects: `client: none`.
  GOALS.md                         ← WHY the product exists (North Star — Vince owns it)
  PRODUCT_SPEC.md                  ← WHAT currently exists (descriptive)
  ROADMAP.md                       ← WHAT we're trying to change
  DECISIONS.md                     ← WHY important choices were made (append-only)
  SKILL-INVENTORY.md               ← every component, classified, with what justifies it
  PROPOSALS.md                     ← the improvement backlog: what is awaiting Vince's decision
  checkpoints/                     ← dated daily alignment reports + the weekly workshop (the evolution record)
  governance/                      ← checkpoint.py + canon.py, the runbooks, audits, Syncthing rules, miro.json
  archive/                         ← superseded history: decisions, retired skills, prior versions of canon docs
  workflows/                       ← the routes as SPECIFICATIONS, for agents — shot2video, board2video,
                                     board-intake + the comparison ledger
  guides/                          ← the same routes in PLAIN LANGUAGE, for Vince at the bench.
                                     Start at guides/assets.md; both routes stand on the sheets
  staging/overview-ui/             ← Hearthlight Studio, the production cockpit. Final home undecided
  skills/                          ← Hermes skills = the instruction layer (PRD §6). 23 skills:
    hearthlight-distribution-spec/ Platform/aspect/length/captions + format/client/charged_register — decided first
    hearthlight-conventions/       Folders, naming, versioning, conventions
    hearthlight-consolidate/       Stage 1.5 — bounded ideation → Vision Brief
    hearthlight-outline/           Stage 2 — Story Arc → Beat Sheet → A/V Script
    hearthlight-critique/          Stage 2.5 — story pressure-test before drawing
    hearthlight-research/          Period research → sourced Research Deck
    hearthlight-mise-en-scene/     Stage 3 — Aesthetic Bible: LOCKED style + COMPOSED world
    hearthlight-character/         Stage 3.5 — CHARACTER.md dossier + lighting-neutral turnaround sheet
    hearthlight-timing-intake/     Storyboard Pro XML in, Resolve FCP XML out — one timing source
    hearthlight-clip-extractor/    transcript→clips: audio master + per-moment audio/video cuts
    hearthlight-reference-report/  loose ref images + writeup → glanceable Notion report
    hearthlight-image-prompts/     Stage 4 — conditioning stills
    hearthlight-shot-crew/         Stage 4.5 — 8 illustration roles negotiate contested shots
    hearthlight-storyboard/        Stage 5 — motion intent, durations, transitions
    hearthlight-video-prompts/     Stage 6 — the prompt WORDS
      references/seedance-os-bridge.md  ← companion notes on the Seedance 2.0 Skill OS repo (vocab only)
    hearthlight-comfyui-graph/     Stage 6 plumbing (the WIRE — local ComfyUI MiniMax H3; RunningHub Seedance parked)
      references/seedance-i2v-template.json  ← sanitized from Vince's working workflow
    hearthlight-shot-runner/       Stages 4+6 batch execution — subagent per shot, two-stage review, ledger
    hearthlight-dashboard/         Read-only pipeline view + Shot ID protocol
    hearthlight-selfcheck/         Plumbing health — mechanical failure vs. quality judgment
    hearthlight-notion-log/        Notion surfacing — working notes, journal, Threads DB
    hearthlight-board-sheet/       Board sheet for board2video — cluster 10-15s, panels + text, one image
    hearthlight-acting/            Performance writing — behaviour not emotion, master profile, eye life
    hearthlight-terse/             Voice register — mechanics terse, art full
  projects/                        ← NOT in git (media + rights-constrained work)
    mcconaughey-call/              ← pilot (private use only — rights note in PRD §3)
      00-source/  01-intake/  02-outline/  03-bible/
      04-images/  05-storyboard/  06-video/  07-final/
    yugioh/
```

The pointer stubs in Claude's skill store are **not** copies — each one names the `SKILL.md` above as
canonical and holds no instructions. See `DECISIONS.md` D-002.

## One-time setup

Hearthlight runs as its **own Hermes profile** with its own Telegram bot.
Follow `profile/SETUP.md` — exact commands for: `hermes update` (your install
is missing the ComfyUI skill), `hermes profile create hearthlight --clone`,
Claude via OpenRouter, `terminal.cwd` + `external_dirs`, SOUL.md, BotFather.

Once running, every skill here is a slash command in the Hearthlight bot:
`/hearthlight-consolidate <paste or voice-note your rant>`

## Working agreement
- Skills are the constitution. When a chat correction is *general*, the fix gets written back into
  the relevant SKILL.md — **edited in place under `Story Studio/skills/`**, which `external_dirs`
  already points at. Vince approves.
  > ⚠️ **Do not use `skill_manage` / `hermes skills install` for hearthlight skills.** They write a
  > *copy* into `profiles/hearthlight/skills/hearthlight/`, giving the skill two homes. The name then
  > resolves ambiguously and the agent can silently load the older copy. Three shadows accumulated
  > this way and were removed 2026-08-06; `hearthlight-selfcheck` now fails RED if any come back.
- The machine never approves its own work. Agents draft, run and report; only Vince marks a design
  Locked or a shot Approved. Approval is per shot — there are no gates (D-026).
- Nothing exists only in chat history — every artifact lands in `projects/{slug}/`.
