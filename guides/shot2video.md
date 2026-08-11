---
doc: GUIDE-SHOT2VIDEO
role: guide
authority: canon
owner: vince
updated: 2026-08-07
answers:
  - what has to exist before a shot image can be generated
  - how a still becomes a clip, step by step
not_here:
  the route's failure modes and evidence: workflows/shot2video.md
  making the sheets: guides/assets.md
---

# Guide — shot2video (still first, then video)

**The route the Yu-Gi-Oh! film is running on.** Each shot gets one still image. You approve it.
Then that still becomes the first frame of the clip.

You approve twice per shot: once for the picture, once for the movement.

---

## Part 1 — getting to a shot image

### What must exist first

Nothing runs until all five are true. If a render comes back wrong, check this list before
rewriting anything — most bad renders are a missing input, not a bad prompt.

| Needs to exist | Where | If it's missing |
|---|---|---|
| Aspect ratio decided | `distribution-spec.md` | Everything gets re-composed later. Aspect is a composition law, not an export setting |
| Locked style block | `03-bible/mise-en-scene.md` | Every shot looks like a different film |
| Character + location sheets | `03-bible/` | Faces and rooms drift shot to shot ([guide](assets.md)) |
| Props registry | `03-bible/props.json` | Objects go generic — this is how the cards became "trading cards" |
| Shot record with stable IDs | `05-storyboard/shots.json` | Nothing can be bound to anything |

Plus your **boards**, which have to be *files* the system can open — not images pasted in a
spreadsheet. That's a one-time import per project:

```bash
# the full seven-step procedure, with dry-runs
cat workflows/board-intake.md
```

### Step 1 — read the drawings

An LLM with vision opens each panel and reports what it sees.

```bash
# one packet per unread panel, plus the dispatch note
python skills/hearthlight-image-prompts/scripts/panel_reader.py plan --project {slug}
# an agent reads each drawing under references/PANEL-READING.md, then:
python skills/hearthlight-image-prompts/scripts/panel_reader.py record --project {slug} --shot 8 --reading reading.json
```

**This is not optional decoration.** Until a panel is read, the prompt author is told a
drawing exists and to ignore it — the boards are the most authored thing in the project and an
unread one contributes nothing. `Inputs` says *"the board panel has never been read"* on any shot
in that state.

The reader **names conflicts and never settles them.** If your sketch shows a two-shot and the
Vision says single, you get told both. A sketch is concrete and a Vision is abstract, and
concreteness is not authority — that call is yours.

### Step 2 — check the whole film for disagreements

Run this **before** generating anything. It is cheap, and it catches the class of error that
otherwise costs you a regeneration.

```bash
python skills/hearthlight-image-prompts/scripts/continuity_pass.py run --project {slug}
```

One agent reads every shot at once and reports where two shots state facts that disagree — a
prop named specifically in one and generically in another, a character described two ways, a
setup two shots share but describe differently.

Every other reviewer in the system sees one shot at a time. That is why this pass exists: shot 1
and shot 5 were never in the same room before it, so nothing could notice they disagreed.

It **reports and never resolves**. You decide.

### Step 3 — write the prompt

```bash
python skills/hearthlight-image-prompts/scripts/prompt_authoring.py --project {slug} …
```

An LLM writes it under a contract (`references/PROMPT-AUTHOR.md`), a second LLM reviews it and
may block but never rewrite, and Python validates the result. No script writes prompt text — that
part is judgment and it stays with a model under contract.

**Blockers are the product, not a failure.** If the author flags that your direction is
incoherent or a fact is missing, that's the system working. A flagged contradiction beats a
fluent prompt every time.

Order of authority when sources disagree — worth knowing, because it explains most outcomes:

1. Film laws, rights, aspect ratio
2. **Your latest Shot Vision** ← creative authority
3. Storyboard text and the panel drawing (once it has been read)
4. Adjacent-shot continuity
5. Character, location, prop records
6. What the provider can do

### Step 4 — generate the still

Style/composition first, then likeness, then the final input image.

The style block is **never in the prompt text.** It's a moodboard parameter. If you see the style
sentence inside prompt prose, that prompt is invalid and the compiler will reject it.

### Step 5 — you approve the picture

Two halves:

- **Machine-checked:** right aspect ratio, style block handled correctly, references present.
- **Yours alone:** is it good.

Look at it full-res. Not the Telegram thumbnail — a thumbnail hides exactly the problems that
survive into video.

---

## Part 2 — turning the still into a clip

### Step 6 — write the video prompt

Built from the approved storyboard entry, never improvised (`hearthlight-video-prompts`).

Performance comes from `hearthlight-acting`, and its one rule is worth carrying in your head:
**write behaviour, not feelings.** "Sad" makes the model improvise and it improvises shallow.
A goal, an obstacle, and a change in how the character fights gets you a performance. The
emotion arrives on its own.

Check the eyes. Gaze that moves, blinks that change rate, a catch-light in the pupil. Dead eyes
are the number-one tell of AI acting.

### Step 7 — generate

MiniMax H3 image-to-video, through the local ComfyUI graph.

- `image1` — your approved still
- `image2` — the character turnaround sheet

The sheet on `image2` is what stops the face drifting across the clip. Don't skip it.

H3 generates audio by default. Decide per project whether you want that or whether it just
obstructs your edit — and write the decision down.

### Step 8 — you approve the clip

Watch one thing above everything else: **does it still look painted?** Photoreal creep is the
enemy. The moment a clip starts looking like footage, the film has quietly changed genre.

Then check: did the face hold? Did the eyes stay alive? Does the emotion tail off at the end
rather than switching off — because that tail is what stitches your cut together.

---

## What this costs

Two approvals and at least two paid generations per shot. A shot needing three still attempts and
two clip attempts costs five generations and five reviews.

**The ten-to-fifteen rule.** If a shot hasn't come together in that many tries, the problem is
not the wording. Simplify it — split it in two, remove an action, change the angle. Two strikes
on one route means try [the other route](board2video.md), not another re-roll.

## When to use this route

When the frame carries the meaning. Detonation beats. Close-ups holding a likeness. Anything you
want to see before it moves.

When *motion* is the meaning — a fall, a collapse, a fast reveal — a still of the midpoint
teaches the model a pose instead of a movement. Use [board2video](board2video.md) instead.
