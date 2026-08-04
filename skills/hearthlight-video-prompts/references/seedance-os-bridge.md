# Seedance 2.0 Skill OS — companion reference (bridge note)

Source: `github.com/Emily2040/seedance-2.0` (MIT, anonymous author "iamemily2050"), reviewed 2026-06. A prompt-craft **knowledge library** for Seedance 2.0 — 23 sub-skills + 40 reference docs on how to phrase prompts. It contains **no API client, no ComfyUI node, no RunningHub integration** and generates nothing on its own.

## How it relates to Hearthlight
- It does **not** replace `hearthlight-video-prompts`. Ours is the *executor*: storyboard-derived i2v prompt + watercolour preservation clause + ComfyUI/RunningHub queuing + Gate 5. That logic stays authoritative.
- This repo is a *vocabulary and technique* source the executor may consult. When the two disagree, **Hearthlight rules win** — our conservative motion register, our preservation clause, our lip-sync policy, our file conventions are non-negotiable. Borrow phrasing, never borrow process.

## Pieces worth consulting (read on demand)
- `references/i2v-guide.md` — image-to-video best practices; sanity-check our i2v approach against it.
- `references/first-last-frame-guide.md` — only if we ever do FLF2V transitions between stills.
- `references/anti-slop-lexicon.md` — weak-phrase replacements; useful, but our register is watercolour-restraint, not action-cinema, so filter accordingly.
- `skills/seedance-copyright/` — **directly relevant to the pilot.** McConaughey is a public figure; this skill's rewrite patterns (stylized resemblance, not likeness) reinforce the PRD §3 rights constraint. Worth reading before any pilot clip.
- `references/api-status.md` / `model-name-map.md` — dated model-ID notes (e.g. `doubao-seedance-2-0-260128`); cross-check against what RunningHub actually exposes during setup. Treat as leads, verify on our surface.

## What we deliberately do NOT take
- Its install scripts (`scripts/install_*.py`, validation scripts) — never run repo code on Vince's machine. If installed at all, use Hermes's own skill installer (which security-scans) and take markdown only.
- Its "professional delivery" scope (ACES, subtitles, campaign cutdowns) — out of scope for the pilot; ignore.
- Its multilingual vocab — not needed.

## If installing the whole repo as a Hermes skill
Optional. `hermes skills install https://github.com/Emily2040/seedance-2.0` runs a security scan first. Keep it as a *separate companion skill* (e.g. `seedance-20`), never merged into the hearthlight-* set — so its general advice can't quietly override our gated process.
