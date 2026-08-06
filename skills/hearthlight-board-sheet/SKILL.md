---
name: hearthlight-board-sheet
description: >
  Compose the board sheet that board2video feeds to a video model — a single image of a storyboard
  spreadsheet covering one 10-15 second sequence, with a panel sketch, description, action and audio
  per shot. Clusters the shot list into sequences, crops each panel, and renders the sheet. The whole
  point is that the prompt afterwards can be one sentence. Use when running board2video, or when a
  sequence needs to be handed to a video model as a picture rather than as prose.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, board, storyboard, sequence, board2video, gate-5]
    category: hearthlight
---

# Hearthlight — Board Sheet (board2video input)

## When to Use
Running [board2video](../../workflows/board2video.md). This skill builds the **one image** that route
depends on. It does not generate video — it prepares the thing the video model reads.

## The idea

A storyboard already carries framing, order, and intent in a form a model can read directly. Rather
than translating that into three thousand words, **hand over the board itself** and say:

```
Create a video according to the storyboard.
```

That is the whole prompt. If the sheet is right, it does not need help; if the sheet is wrong, more
words will not save it. **All the craft moves into the sheet.**

---

## Clustering — 10 to 15 seconds per sheet

One sheet covers one **sequence**, not the whole film.

- **Target 10–15 seconds** of screen time per sheet. Use the board's real durations from
  `hearthlight-timing-intake`, never estimates.
- **Typically 3–6 shots.** More than that and the panels get too small to read; fewer and you lose
  the continuity that makes this route worth using.
- **Cut sequences at natural seams** — a location change, a time jump, a beat change from the Beat
  Sheet. Never split mid-beat to hit a duration target. **The seam matters more than the number.**
- **Never cross a location boundary in one sheet** unless the transition itself is the sequence, in
  which case the threshold shot leads and both locations appear.
- A shot longer than ~15s alone gets its own sheet, or belongs in shot2video instead.

Record the clustering in `05-storyboard/sequences.md`: sequence ID, shot IDs, total duration, and the
seam reason. Sequence IDs are stable like shot IDs — `seq-01` — and clips are named from them.

## Sheet layout

One row per shot, in order, read left to right and top to bottom.

| Column | Holds | Notes |
|---|---|---|
| **Shot** | Shot ID + duration | The permanent ID (D-009), not the row number |
| **Panel** | The storyboard sketch, cropped | The load-bearing column |
| **Description** | What is in frame — the still | One or two lines |
| **Action** | What moves, and when | The only column carrying time |
| **Audio** | VO line, or the SFX that matters | Quoted speech verbatim |

**Panels are truncated on purpose.** Crop to the essential frame content and drop the marginalia,
board numbering, and any director's scrawl — a model reads every mark on the image, and a stray
annotation becomes an object in the shot. Uniform panel size across the sheet: unequal panels read as
importance and skew what the model emphasises.

**Text is short and physical.** These cells are prompt text in disguise. The medium's rules still
apply — see `hearthlight-video-prompts`. No photographic vocabulary on an illustrated film, no
emotion words where a body movement will do (`hearthlight-acting`), and no age, ever.

**Legibility is the whole product.** If a cell is unreadable at the sheet's output resolution, the
model cannot read it either. Render generously: a 3-shot sheet should be wide enough that the
description text is comfortably readable at 100%.

## The header strip

One band across the top of every sheet, carrying what the panels cannot:

- **Sequence ID and total duration** — `seq-03 · 12.5s`
- **The locked style block**, verbatim from `03-bible/mise-en-scene.md`
- **Aspect ratio** — a composition law (D-008), not an export setting
- **Character tags present in this sequence**, matching the reference manifest exactly

Everything in the header is copied, never paraphrased. This is the same verbatim discipline as any
prompt; the sheet is just a different carrier.

## Procedure

1. **Read the board's durations** from `hearthlight-timing-intake`. Do not estimate.
2. **Cluster into sequences** and write `05-storyboard/sequences.md` with the seam reasons.
3. **Crop the panels** from `03-bible/refs/storyboard-panels/` — uniform size, marginalia removed.
   Crops are derived files; never modify the originals.
4. **Compose the sheet** — header strip, then one row per shot.
5. **Render** to `05-storyboard/sheets/seq-{nn}-v{n}.png`. Versioned and immutable like any generated
   asset (`hearthlight-conventions`).
6. **Read it back at 100%.** If any cell is not comfortably legible, re-render larger before spending
   a single generation.
7. **Hand to the video model** with the one-line prompt, plus the asset sheets as references.

## Pitfalls

- **A sheet nobody can read.** The most common failure and the most preventable — check before generating.
- **Cropping to a duration target instead of a seam.** A sequence split mid-beat produces two clips
  that will not cut together.
- **Marginalia left in the panel.** Board numbers and arrows become objects in the generated frame.
- **Paraphrasing the style block** into the header. Verbatim or the look drifts.
- **Unequal panel sizes.** Reads as emphasis and skews the result.
- **Letting the prompt grow.** If you find yourself writing paragraphs alongside the sheet, the sheet
  is underspecified — fix the sheet. The one-sentence prompt is the contract; a long prompt means
  this route has quietly become board2video/B2.

## Verification

- [ ] Every shot in the sequence appears, in order, with its permanent Shot ID
- [ ] Total duration is 10–15s and matches the board
- [ ] Seam reason recorded in `sequences.md`
- [ ] Header carries the style block verbatim, the aspect ratio, and the character tags
- [ ] Panels uniform, cropped, free of annotation
- [ ] Every cell legible at 100%
- [ ] No photographic vocabulary on an illustrated film; no ages anywhere
- [ ] Sheet saved versioned under `05-storyboard/sheets/`
