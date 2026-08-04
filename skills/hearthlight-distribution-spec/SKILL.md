---
name: hearthlight-distribution-spec
description: Hearthlight project-level brief — the project's IDENTITY (format, client, charged register) plus its technical target (platform, aspect ratio, length, captions, hook timing, safe areas). Decided ONCE per project at the front, then OBEYED by every downstream stage (outline, mise-en-scène framing, storyboard durations, ComfyUI aspect, terse register). This file is where a project declares what kind of film it is; the engine assumes nothing about format or client without it.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, distribution, platform, aspect-ratio, brief]
    category: hearthlight
---

# Hearthlight — Distribution Spec (project brief)

## When to Use
At the **start** of a project, before the shot list is framed — and re-read at every stage. Two jobs:
declare **what kind of film this is** (identity) and **what shape it is** (technical target).

## Project identity — declare this FIRST, the engine assumes nothing

Hearthlight is a genre-agnostic, client-agnostic engine. It does not know whether it is making a
short film, a social clip, or a commissioned remembrance piece — and it must not guess. Three keys:

```
format:           short-film | social-content | remembrance | commercial | <other>
client:           none | talefeather | <name>
charged_register: <one line: what is emotionally load-bearing in THIS film>
```

- **`format:`** — what kind of thing this is. Always set. Its only wired effect is **suggesting the
  distribution defaults below**; everything else it does is inform judgment. Don't build behavior on
  it speculatively.
- **`client:`** — which profile under `profile/clients/` to load, if any. **`none` is the normal
  value** and most projects use it; the engine works fine without a client profile. `talefeather`
  loads `profile/clients/talefeather/AUDIENCE-CONTEXT.md` (grief / living-legacy cohorts, the
  competitive wedge). **Never load a client profile a project didn't declare** — a project with no
  grieving family should not inherit a grieving audience.
- **`charged_register:`** — the content this film protects. `hearthlight-terse` reads it to know what
  it must never compress into fragments. Talefeather: *"tenderness under a running clock — the
  storyteller, the family, the loss."* A comedy short: *"the timing and the punchline's setup."* A
  brand piece: *"the founder's own words about why she started."* Every film has one. Naming it is
  what keeps the machine's brevity from flattening the thing that matters.

Current projects: `yugioh` → `short-film` / `none` (4:3 Academy master).
`mcconaughey-call` → `social-content` / `talefeather` (9:16, 2s hook).

### Format → distribution defaults (starting points, not laws)
Propose these when a project declares its format; Vince overrides any of them freely.

| | **short-film** | **social-content** |
|---|---|---|
| Aspect | 16:9 | 9:16 |
| Hook window | patient — earn the open | ~2s or they scroll |
| Captions | off / optional subtitle track | burned-in, safe-zone aware |
| Sound | assume sound-on | assume sound-off; captions carry the VO |
| Length | as the story needs | short, with re-hooks |
| Safe areas | full frame | platform UI eats ~15% |

`remembrance` and `commercial` inherit whichever of the two matches their delivery target — ask.

The rest of this file is the **technical target**: where the film goes and what shape it is.

## Why it must come early
Aspect ratio and length are **creative constraints, not export settings.** A 9:16 vertical piece composes differently than 16:9 (stacked/center-weighted vs. lateral space); a 60s cut tells the story differently than 110s. Deciding these after the shot list means reworking the shot list. Decide first; obey downstream.

## What the spec captures (`03-bible/distribution-spec.md` or project root)
- **Identity:** `format`, `client`, `charged_register` (see above — declare before anything else).
- **Platform(s):** TikTok / Reels / Shorts / YouTube / Vimeo / website / feed. Primary + any secondary.
- **Aspect ratio:** 9:16 vertical · 16:9 horizontal · 1:1 square · 4:5 portrait-feed. The compositional frame everything is drawn into.
- **Length target:** the finished runtime, with tolerance (e.g. ~110s ± 10).
- **Resolution / export:** 1080×1920 for 9:16, etc. (matches the ComfyUI `ratio`/`resolution` in `hearthlight-comfyui-graph`).
- **Captions / subtitles:** on-screen burned-in? (Essential on sound-off social feeds.) Style, position, safe of UI.
- **Hook window:** how fast the opening must grab (vertical social: ~2s; website: more patience).
- **Safe areas:** platform UI overlays (TikTok right-rail + bottom caption zone eat ~15% of a vertical frame) — keep faces/key action out of those zones.
- **Sound-on assumption:** does the audience hear it by default? (Feed = often sound-off → captions carry the VO; website = sound-on.)

## How it constrains each downstream stage
- **Outline / Beat Sheet:** length target sets beat count and pacing. A short vertical can't hold long pauses unless it re-hooks.
- **Mise-en-scène framing:** the aspect ratio IS a compositional rule. 9:16 → vertical isolation (small below ceiling / above floor), center-weighted, foreground/background depth instead of left/right space. Horizontal wides do not translate — they must be re-conceived, not cropped.
- **Storyboard:** every panel drawn in the target aspect from the start. Durations sum to the length target.
- **ComfyUI graph:** set `ratio` (e.g. 16:9 → 9:16) and `resolution` to match — don't generate 16:9 then crop.
- **Captions:** if burned-in, the VO becomes on-screen text; storyboard must leave room in the safe zone.

## Multi-format note
If the spec is "master + cutdowns," draw the **master** with the vertical crop in mind (keep key action center-safe) so a 9:16 derivative doesn't decapitate anyone. One framing discipline serves both.

## Pitfalls
- Treating aspect ratio as an export setting instead of a composition law.
- Building the shot list, THEN choosing vertical — horizontal wides die in 9:16; you'll redraw.
- Long runtime on a feed platform with no re-hooks — retention collapses.
- Forgetting captions on a sound-off feed (if the VO carries the piece, it goes unheard).
- Faces/text in the platform UI safe-zone (covered by the right-rail / caption bar).
- **Assuming a client.** Treating every project as Talefeather/remembrance work — inheriting a
  grieving audience, a no-generated-audio law, and a tenderness register the project never declared.
  If `client:` is unset, ask; do not default to grief.
- Confusing identity with technical target — keep client-emotion and frame-shape separate.

## Verification
- `distribution-spec.md` exists with `format`, `client`, `charged_register`, platform, aspect,
  length, captions, hook, safe areas.
- Any client profile loaded this session matches the declared `client:` value.
- The shot list / storyboard is drawn in the spec's aspect ratio (not cropped from another).
- ComfyUI `ratio`/`resolution` match the spec.
- Durations sum to the length target.
