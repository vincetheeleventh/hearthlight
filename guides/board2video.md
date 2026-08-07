---
doc: GUIDE-BOARD2VIDEO
role: guide
authority: canon
owner: vince
updated: 2026-08-07
answers:
  - how a storyboard sheet becomes a clip with no still in between
  - what has to be true before this route can work at all
not_here:
  the route's failure modes and evidence: workflows/board2video.md
  making the sheets: guides/assets.md
---

# Guide — board2video (board straight to video)

**The parallel trial.** No still, no Gate 3. You compose an image of your storyboard covering a
short sequence, hand it over with your character and location sheets, and the prompt is one line.

You approve **once** per sequence, at the clip.

---

## The one rule

> **Assets first. Nothing generates until every character, location and prop is locked.**

On [shot2video](shot2video.md) a weak sheet gets papered over at the still stage — you fix it in
the picture and move on. Here there is no still. A weak sheet fails **in every shot of the
sequence at once**, and it fails quietly.

If you read nothing else on this page, read [the assets guide](assets.md) and come back.

---

## How it works

You build **one image** of a storyboard laid out like a spreadsheet: panel sketch, description,
action and audio, one row per shot, covering 10–15 seconds. Then:

```
Create a video according to the storyboard.
```

That's the whole prompt. **All the craft lives in the sheet.** If the sheet is right it needs no
help; if it's wrong, more words will not rescue it.

This also answers the prompt-length question you may have seen elsewhere. Those 3,000–4,000-word
prompts were for chaining several shots into one generation — that's this route's territory. And
even here, the length is carried by the sheet, not by prose.

### Sequences, not shots

A sheet covers **3–6 shots** cut at a natural seam: a location change, a time jump, a beat
change. Clips come back per sequence.

That's the real trade. **Continuity inside the sequence is free** — the model sees all the shots
together, so nobody's shirt changes mid-scene. **Control inside the sequence is gone** — you
can't re-roll shot 3 without re-rolling shots 1 through 6.

---

## The steps

### 1. Lock the assets

Blocking. Character sheets, location sheets, style reference, props registry. Bound by
`shot_id`. See [the assets guide](assets.md).

### 2. Run the continuity pass

```bash
python skills/hearthlight-image-prompts/scripts/continuity_pass.py run --project {slug}
```

This matters *more* here than on the other route, because there's no still where you'd otherwise
catch a drifting prop by eye. One agent reads every shot at once and reports where two disagree.

### 3. Cluster into sequences

10–15 seconds, cut at a natural seam. Don't cut mid-beat — a sequence that ends halfway through
an action gives the model nowhere to land.

### 4. Compose the sheet

`hearthlight-board-sheet` builds it. Then **look at it at 100%.** If a cell isn't legible to you,
it isn't legible to the model, and that shot is going to come back as an invention.

### 5. Write the floor plan

If the sequence has cuts inside it, write a `GEO SPATIAL LAYOUT`: landmarks, what's frame-left,
what's frame-right, where the camera stands, which line it never crosses. A few lines. No
characters, no action — just the space.

**This is the cure for characters teleporting between shots.** The model does not remember the
previous shot; the floor plan is the only thing that makes the space persist.

### 6. Generate

Sheet + asset references + the one-line prompt, through `MiniMaxH3ReferenceToVideo` on the local
graph — it takes a list of reference images alongside the sheet.

**Name the role of every reference.** *"This is the boy's face. This is the room's space — take
the space and the texture, not the framing or the colour."* Left unlabelled, the model guesses,
and its favourite wrong guess is to copy the location reference's composition.

### 7. Gate 5 — you approve the clip

This is the **only** quality gate on this route. Weight it accordingly. Nothing upstream caught
anything for you.

---

## What goes wrong here

Worth knowing in advance, because each has a specific cure rather than a re-roll:

- **Extra people, cloned furniture.** Open the prompt with an exact character count, close it by
  naming every count again.
- **Characters teleport between cuts.** The floor plan, plus re-naming who stands where after
  every cut.
- **The face drifts on wide shots** — the model grabs whichever reference is easiest to read.
  Keep one large 3/4 portrait on the sheet as the single clean face source.
- **Complex action mid-beat stalls** — the model shuffles and freezes. Start the prompt with the
  action *already underway*: "he is ALREADY mid-swing, the door ALREADY cracking." Make the
  approach its own shot.
- **The model copies a location reference's composition** instead of reading it as space. Ban it
  explicitly, every time.

---

## When to use this route

Coverage. Connective tissue. Establishing wides. Anything where the specificity premium isn't
worth two review loops.

And especially: **shots whose meaning is motion** — a fall, a collapse, a fast reveal. A still of
the midpoint teaches the model a pose. This route skips that problem entirely.

Use [shot2video](shot2video.md) when composition *is* the argument, or when a close-up is
carrying a likeness.

---

## Log what happens

This route is on trial against shot2video, and the trial only produces an answer if you fill in
the ledger in `workflows/README.md`. One row per shot tried: attempts, cost, verdict, and **what
decided it**.

*"board2video lost — hands drifted on the close-up"* is a finding. *"shot2video was better"* is
not. And log the failures especially — a route that failed on a shot type is the most useful row
in the table.
