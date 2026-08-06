---
doc: board2video
role: workflow
authority: canon
owner: vince
updated: 2026-08-05
status: trial
answers:
  - how a shot goes from storyboard straight to clip, with no per-shot still
  - what the asset sheets must carry for this to work
not_here:
  the alternative route: workflows/shot2video.md
  prompt craft: skills/hearthlight-video-prompts/references/prompt-architecture.md
  performance writing: skills/hearthlight-acting/
---

# board2video — Storyboard → Video Direct

**Status: ACTIVE — parallel trial**, run against [shot2video](shot2video.md) on the same
shots.

No conditioning still. The board goes to video directly, and identity is held by **key asset
images** — character sheets, location sheets, a style reference — instead of by an approved frame.

**What this buys:** one step from board to motion. No Gate 3, no still to drift.
**What it costs:** the model decides framing, and a weak asset sheet has nowhere to hide. **The
assets carry the entire load.**

---

## The load-bearing rule

> **Assets first. Nothing generates until every character, location and prop is locked and
> stress-tested.**

In shot2video a bad sheet can be papered over by an approved still. Here it cannot. This one rule saves
more re-rolls than everything else in this document combined.

An asset is a pair: **a descriptor (text) + a reference (image)**. The descriptor goes into every
prompt word for word — the model has no memory. The image anchors identity.

The rules that make an asset hold are **law, not workflow** — they live with the skills that own
them, so there is exactly one statement of each:

| What | Owner |
|---|---|
| The asset stress test · state splitting · the tag dictionary | `hearthlight-conventions` |
| Location sheets — 3/4, the anchor, one light logic, reverse angles | `hearthlight-mise-en-scene` |
| Character sheet composition · believable-over-beautiful · catch-light | `hearthlight-character` |
| The no-double-pass law — amend by mask, never regenerate | `hearthlight-image-prompts` |

**Read them before starting this route.** shot2video can paper over a weak sheet with an approved still;
this route cannot.

> ⚠️ One open conflict: `hearthlight-character` § Contents specifies three full-body views, which
> competes with the headless-front finding. **P-011 open** — until Vince rules, that skill governs.

---

## What it is

**One sheet, one sentence.** Hearthlight composes an image of a storyboard spreadsheet covering a
10–15 second sequence — a panel sketch, description, action and audio per shot — and the prompt is:

```
Create a video according to the storyboard.
```

Building that sheet is `hearthlight-board-sheet`. **All the craft lives in the sheet**, which is why
the prompt can be one line. If the sheet is right it needs no help; if it is wrong, more words will
not save it.

This also settles the prompt-length question. The 3,000–4,000-word prompts from the source practice
were for **multiple shots chained in one generation** — that is this route's territory, not
shot2video's. And even here, the length is carried by the sheet rather than by prose.

### The sequence, not the shot

A sheet covers 3–6 shots cut at a natural seam — a location change, a time jump, a beat change.
Clips come back per sequence, not per shot, which is the real trade: **continuity within a sequence
is free, and control within it is gone.**

## The route

1. **Lock the assets.** Character sheets, location sheets, style reference. Blocking — this route has
   no conditioning still, so a weak sheet fails in every shot of the sequence at once.
2. **Cluster into sequences** — 10–15s, cut at a natural seam. `hearthlight-board-sheet`.
3. **Compose the board sheet** for the sequence, and read it back at 100%. If a cell is not legible
   to you, it is not legible to the model.
4. **Write the scene's `GEO SPATIAL LAYOUT`** if the sequence has internal cuts — a floor plan in a
   few lines: landmarks, frame-left and frame-right, where the camera stands, which line it never
   crosses. No characters, no action. This is the cure for characters teleporting between shots.
5. **Generate** — sheet + asset references + the one-line prompt. **Name the role of every
   reference** or the model guesses and guesses wrong.
6. **Gate 5 — Vince approves the clip.** There is no Gate 3 here; the clip review is the only quality
   gate on this route. Weight it accordingly.

> **Surface: `MiniMaxH3ReferenceToVideo`** — the same local ComfyUI graph that runs shot2video also
> carries a reference node taking an expandable `ref_images` list plus `ref_videos` and `ref_audios`.
> That is a board sheet **plus** character and location sheets as separate references, with a
> one-line prompt. Untested for this purpose; worth one deliberate trial before planning the
> comparison. Wiring: `skills/hearthlight-comfyui-graph`.

## Cost

**One approval loop per shot.** Cheaper per attempt than shot2video, but attempts can run higher because
framing is not pre-settled — the trial exists to find out whether the saved loop outweighs the extra
re-rolls.

## Known failure modes

- **The model copies the composition of a location reference** instead of reading it as space.
  Location references carry an explicit ban: *do not use as a starting frame, do not inherit the
  composition, the angle or the colour — take only the space and the texture.*
- **Extra people and cloned furniture.** The model adds characters and duplicates props. Every prompt
  opens with an exact character count and closes with positive constraints naming every count.
- **Characters teleport between shots.** The model does not remember the previous shot. Cured by the
  GEO block plus re-naming who stands where after every cut.
- **Identity drifts on wides.** The face is taken from whichever reference is easiest to read. Keep
  a large 3/4 portrait on the sheet as the single clean face source.
- **Complex action in the middle of a beat stalls.** The model shuffles and freezes. Open the prompt
  with the action already underway — *"he is ALREADY mid-swing, the door ALREADY cracking"* — and
  make the approach its own shot.
- **A weak asset sheet fails silently**, then fails in every shot at once. This is the failure mode
  shot2video does not have.

## Where it should win

Coverage and connective tissue. Establishing wides. Shots whose meaning is motion rather than
composition — a fall, a collapse, a fast reveal — where a still of the midpoint teaches the model a
pose instead of a movement. Sequences where speed of iteration matters more than per-frame control.

**Stated before the trial, so the trial can falsify it.**
