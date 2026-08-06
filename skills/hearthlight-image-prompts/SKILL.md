---
name: hearthlight-image-prompts
description: "Hearthlight Gate 3 still workflow: compile shot prompts from the approved board and bible, run a Krea 2 style-and-composition pass, preserve version history, review composition with Vince, then use GPT Image 2 to replace provisional people with approved character-sheet identities without changing the shot. Use for first-pass boards, likeness replacement, revisions, contact sheets, and final still selection."
metadata:
  hermes:
    tags: [hearthlight, image-prompts, krea, gpt-image-2, version-history, gate-3]
    category: hearthlight
---

# Hearthlight — Images (Gate 3)

## THE FRAME-ONE LAW (read before writing any still prompt)

**A still is ONE INSTANT — frame one of the shot, and nothing else.**

An image generator has no concept of "after." Given a sequence it renders every clause
*simultaneously*. The yugioh shot-2 failure is the canonical case: the still spec read
*"After the knot is pulled tight, her hand lowers dog tags into the close-up and he takes them,"*
and the model produced a wife handing over dog tags while the father was still tying his boot.
Nonsense, and it cost a paid generation.

**Banned from any Still spec:** *after, then, once, next, meanwhile, begins to, starts to, about to,
as he/she/the, enters frame, comes down, lowers X into, reaches for, turns and, straightens, rises,
stands up, sits down.* If a spec needs one of these, the shot holds **two states** and you owe a
decision before generating.

**Two columns, two audiences — never mix them:**

| Column | Consumer | Holds |
|---|---|---|
| `Still (frame one)` | image generator | one frozen instant; static tableau; present tense |
| `Action (motion — video only)` | video generator (i2v from the approved still) | what changes, with timings |

### Resolving a two-state shot
1. **Split into two stills** — preferred when **new information enters frame** (a prop appears, a
   person arrives). The model has never seen the new element and will invent it. Splitting costs no
   runtime: divide the duration. A camera move survives as a match between the two clips.
2. **Frame-one only** — fine when the change is *movement of something already visible* (a hand
   tightening, a head turning). The Action prompt carries it.
3. **Condition on the later state** — cheapest, but forfeits the reveal.

**Check the graph for an end-frame input before assuming first+last conditioning exists.** As of
2026-08-01 the Hearthlight Seedance graph exposes only `image1` (still) and `image2` (character
sheet) — no last-frame slot — so option 1 is the only reliable route for a reveal.

### Describe what is VISIBLE; record what it IS in Notes
A prompt is not a continuity record. If an object must be **unreadable** in a shot, the still spec must
not name it — a generator told "dog tags" renders legible dog tags and destroys the question the shot
exists to ask. Write appearance (*"something small and indistinct held in both hands"*); put the
identity in **Notes** for the reviewer, with an explicit reject line. yugioh shots 2→3 are the model:
the wide asks, the insert answers.

### Never put a signature string in the possessive
Signature strings end in nouns — *"tired eyes"*, *"tan boots"*, *"a band-aid on one knee"* — so `X's`
is always ungrammatical and produces garbage like *"a band-aid on one knee's hand"*. This happens
silently whenever strings are bulk-substituted into sentences.
**Write `the hand of {X}`, never `{X}'s hand`.** The validator checks for this.

### Enforce it mechanically
```bash
python3 skills/hearthlight-image-prompts/scripts/check_frame_one.py <shotlist.xlsx>   # exit 1 on violation
```
Run before any batch. A word-scan is cheaper than a re-render.

## Core workflow

Gate 3 has two separately approved image stages.

### Stage A — STYLE AND COMPOSITION CHECK

Model: live-discovered `krea/krea-2/medium`. Master: the Film Brief's declared aspect ratio; Yu-Gi-Oh is 16:9 widescreen.

Goal: approve style and the visible arrangement of one frozen instant. Facial likeness remains
provisional; Stage B owns identity replacement.

**Creative authority:** the latest submitted Shot Vision in `04-images/shot-vision.jsonl`, joined by
permanent Shot ID to the current `05-storyboard/shots.json` technical baseline. Imported hand-drawn
board workbooks are historical reference evidence only: archive them immutably, never let them regain
authority, and never block compilation because an old workbook is stale. A spreadsheet is generated
only as a human-readable handoff/export of current Studio state. Beat and narrative material may explain
meaning, but never enter a prompt as abstract prose. Generated prompts never rewrite Shot Vision.

**Focused author contract:** `references/PROMPT-AUTHOR.md` has one job: translate one validated shot
bundle into one high-quality Krea prompt. `prompt_authoring.py` injects the full contract into every
author and reviewer call; the broad Gate 3 workflow in this file is not the worker's context.

**Compilation order:**
1. Python loads and hashes film laws, full visual-system context, declared master aspect, current Shot
   Vision, current shot-registry fields, narrative record, adjacent-shot continuity, region-tagged character
   facts, mapped assets, special lighting laws, and the Krea provider profile.
2. A tool-restricted Hermes Shot Prompt Author uses the focused guide to make the visual judgments:
   crop-first visibility, observable emotion, atomic ownership, medium translation, semantic-density
   reduction, and concise `prompt_body`. It returns strict structured JSON only.
3. Python validates facts and invariants: source identity, one instant, canonical visible traits,
   subject/prop ownership, counts, model-control separation, provider vocabulary, and prompt length.
   A failed object gets one source-preserving author repair attempt.
4. Python passes through the author's coherent visible-frame prose without appending aspect ratio,
   locked style, or repeated acceptance sections. Those remain request parameters and structured
   validation data. An independent, tool-restricted Hermes Shot Prompt Reviewer then checks source grounding, visual coherence,
   continuity, attribute binding, illustration language, and likely Krea readability. It may block
   but never invent direction. One repair attempt is allowed; a second failure stays blocked.
5. Show the Prompt Board. Vince may correct Vision and recompile. Only approval of the exact batch
   hash, job count, model, estimate, moodboard strength, and aspect ratio unlocks generation.

Studio endpoints preserve append-only Vision revisions, prompt specs, prompt batches, approval
events, and generation lineage. Revert appends a restoration revision; it never deletes history.
Shared shots compile through their owner. Source-photo shots save Vision but never compile or spend.

Krea request controls remain parameters, never prose: `creativity=raw`, `intensity=0`,
`complexity=0`, `movement=0`, model, resolution, aspect ratio, moodboard ID, and moodboard strength.
The full request fingerprint controls retry/resume and immutable versioning.

Compile from Studio by editing Shot Vision and pressing **Submit changes**. For command-line batch
execution after Prompt Board approval:

```bash
python skills/hearthlight-image-prompts/scripts/krea_style_comp.py --project {slug} --all
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --shots {shot-a} {shot-b} --dry-run
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --shots {shot-a} {shot-b}
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --all
```

Once `shot-vision.jsonl` exists, `krea_style_comp.py` accepts only the newest approved prompt packet
for each current Vision revision. It blocks missing approval, stale Vision, changed batch hashes,
unstable identity, shared duplicates, source photos, motion text, schema drift, and packets that disagree with the declared master aspect.
Before migration only, it can read the legacy exact frame-one packets so existing history remains
recoverable. `two_pass.py` Stage A remains disabled.

Generate one owner per unique setup. Download and ledger every result before the next paid job.
Never overwrite. A matching completed request fingerprint skips without spend; a submitted unfinished
job resumes by Krea job ID.

### Gate 3A — composition review

Send a labeled contact sheet plus full-resolution images in batches of 3–5. Vince reviews style and composition. A voice rant changes no state by itself.

Parse only explicitly named shots. Echo:
- flagged shots with feedback verbatim;
- unflagged shots proposed as composition-approved;
- ambiguous references.

Apply only after Vince confirms the summary. For each approved shot, record `composition-approved` and select exactly one immutable `composition-base`. Framing/composition revisions remain in Krea and create a new version.

### Stage B — LIKENESS REPLACEMENT

Model: `openai/gpt-image-2`, through Codex OAuth first.

Goal: replace provisional depicted people with the exact approved characters. This is an edit of the approved Krea base—not a new composition.

Inputs, ordered:
1. selected composition base;
2. every approved character sheet for people in frame;
3. exact signature/must-hold text;
4. canonical prop reference when exact identity matters.

Preserve exactly: canvas, camera, crop, perspective, figure placement, relative scale, body pose, hand position, action, environment geometry, prop placement, lighting direction, value pattern, palette, ink line, colour wash, white-space boundaries, and overall Krea-derived style.

Change only: identity, required wardrobe details, and explicitly referenced canonical prop identity.

Do not restage, relight, recrop, beautify, age-shift, add/remove people, or redesign the image. A shot without likeness-critical people may finish at Stage A. Exact hero-prop shots still use Stage B.

Run:

```bash
python skills/hearthlight-image-prompts/scripts/two_pass.py --project {slug} preflight --stage likeness
python skills/hearthlight-image-prompts/scripts/two_pass.py --project {slug} compile-prompts --stage likeness
```

Before paid Stage B work, record its estimate and explicit approval with the same `set-estimate` / `approve-cost` commands using `--stage likeness`. Stage B is blocked until every needed Krea base is composition-approved/selected and every needed local character sheet is approved. Krea upload URLs are not required for GPT Image 2 local references.

### Gate 3B — final image review

Review the likeness versions using the same confirmed-rant protocol. Likeness revisions create a child version of the selected composition base. A final selection must come from Stage B when that shot requires likeness; otherwise it may come from Stage A. Gate 3 closes only after every shot has a final selection and Vince gives explicit ✅.

Approved final still paths are the sole conditioning inputs for later video generation.

## THE NO-DOUBLE-PASS LAW (amend by mask, never by regeneration)
**An image never runs through a model twice in full.**

Every full pass destroys texture and drifts colour. After two passes a face turns symmetrical,
plastic and lifeless — and **dead texture ruins the acting downstream**, because a plastic face
cannot carry a performance however good the video prompt is.

To add a jacket, a scar, blood, or any point change to an approved image:

1. Generate the point change on a **copy**.
2. Composite **only the changed region** back onto the original, by hand, with a mask.
3. Everything outside the mask stays untouched original. The original skin texture survives.

This applies to conditioning stills and to character and location sheets alike. "Just running it
through once more to clean it up" is the fastest route to a plastic face. A change that alters
identity rather than surface is a **new state asset**, not a cleaned-up old one — see
`hearthlight-conventions` § EVERY STATE IS A SEPARATE ASSET.

## Prompt construction

Stage A prompt order:
1. framing, viewpoint, and crop;
2. one visible tableau with atomic subject-specific clauses;
3. spatial relationships and object ownership;
4. visible environment and light;
5. only non-redundant shot-specific constraints, folded into natural prose.

Aspect ratio, locked style, moodboard, model, resolution, and acceptance checklists stay outside the
prompt. `required_elements` and `forbidden_elements` remain structured compiler/reviewer data; Python
never renders a separate `Must show` section.

No workflow labels, motion, timecodes, camera movement, continuity bookkeeping, abstract emotion,
unowned props, invisible identity detail, full signature strings, photographic medium collisions, or
incidental text. Preserve only text visibly required by direction, such as SONICS or the canonical
Warrior Returning Alive title.

## Durable contract

- `03-bible/assets.json`: moodboard, critical assets, approval states, stage settings, cost approvals.
- `04-images/shot-vision.jsonl`: append-only Shot Vision revisions, reverts, compilation failures, and approvals.
- `04-images/prompt-specs/{batch}/`: immutable structured production objects and exact batch fingerprint.
- `04-images/image-workflow.json`: model routing and per-shot stage requirements.
- `04-images/prompt-packets/`: exact submitted prompts and reference arrays.
- `04-images/generations.jsonl`: append-only generation, review, and selection truth.
- `04-images/status.md`: derived view only.
- `05-storyboard/archive/hand-drawn-board-snapshots/`: immutable imported board workbooks and manifest.
- `05-storyboard/exports/`: disposable human-readable handoffs generated from current Studio state; never authority.

Read `references/versioned-review.md` for event and recovery rules. Never hand-edit derived workflow/status views.

## Verification

- Every live board row maps by permanent Shot ID to generated, shared, or source-photo mode.
- Every Stage A prompt is tied to an approved current Shot Vision revision and structured spec.
- Partial-body shots contain only useful traits from visible tagged regions; unknown/paraphrased traits block.
- No Stage A prompt contains motion, timecodes, multiple temporal states, workflow labels, full signatures,
  or character-sheet image conditioning.
- Film Brief, assets manifest, compiled packet, and live Krea schema agree on the declared master aspect ratio.
- Approval binds exact prompt-batch hash, job count, model, moodboard strength, estimate, and cost ceiling.
- Files are immutable, open locally, and retain prompt/reference/Vision provenance.
- Shared and source-photo shots never spend generation credits.
- Quality remains Vince's call.
