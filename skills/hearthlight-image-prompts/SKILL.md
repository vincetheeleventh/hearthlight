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

Model: live-discovered `krea/krea-2/medium`.

Goal: approved style, composition, camera, crop, body silhouette, relative height, pose, action, environment, light, palette.

Inputs:
- `Still (frame one)` from the newest approved shot-list workbook — the sole prompt-body source;
- master aspect ratio from `03-bible/assets.json` as an API parameter;
- selected Krea moodboard ID and strength from `03-bible/assets.json` as API parameters.

Never read `Action (motion — video only)` while compiling a Krea still prompt. Never append timecodes,
camera motion, Notes, continuity bookkeeping, review rules, stage explanations, global negative lists, or
character `must_hold` arrays. Character and style language must already be visible-image language inside
`Still (frame one)`. If it is missing there, block and amend the sheet; do not silently assemble a second prompt.
Do not attach character-sheet images during Stage A. Facial likeness is provisional. Prompt the people as accurately as possible, but prioritize frame geometry and body construction. For adult/child scenes, state the relative scale explicitly.

Compile and verify the complete current board:

```bash
python skills/hearthlight-image-prompts/scripts/krea_style_comp.py --project {slug} --all
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --shots {shot-a} {shot-b} --dry-run
```

The compiler blocks stale registry/workbook hashes, unstable Shot IDs, shared-setup duplicates, source-photo jobs, forbidden motion text, and any packet that differs from its exact `Still (frame one)` cell. It writes `prompt-packets/frame-one-{revision}/batch-plan.json` plus one immutable packet per unique setup. The legacy `two_pass.py compile-prompts --stage style-composition` path is disabled because it mixed video/action material into image prompts.

Krea request parameters are separate from prompt text: `creativity=raw`, `intensity=0`, `complexity=0`, and `movement=0`. Raw mode prevents Krea prompt expansion from inventing subjects outside the authored still. Moodboard ID/strength, aspect ratio, resolution, prompt, model, and these K2 parameters form one request fingerprint; changing any field creates a new version instead of being mistaken for completed work.

Generate two calibration shots first. Machine-check file readability, aspect ratio, exact prompt history, required/forbidden depicted elements, and crash resume. Vince alone judges aesthetic quality. Then show the full remaining-batch cost/time estimate, wait for explicit approval, and record `cost_approvals.style_composition_v4` in `03-bible/assets.json` before `--all` may submit.

```bash
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --shots {shot-a} {shot-b}
python skills/hearthlight-image-prompts/scripts/krea_style_comp_run.py --project {slug} --all
```

Generate one owner per unique setup. Shared shots never dispatch twice. Source-photo shots never dispatch. Download and ledger every completed output before the next paid job. Never overwrite. A matching completed request fingerprint skips without spend; a submitted unfinished job resumes by Krea job ID.

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

## Prompt construction

For Stage A, submit the normalized `Still (frame one)` cell as the complete Krea prompt body. Do not wrap it in workflow instructions. Do not inject other spreadsheet columns or bible arrays. Rephrasing happens upstream when the Still cell is authored or amended; compilation is faithful extraction.

No incidental text. Preserve only text explicitly required by the board or character bible, such as SONICS or the canonical Warrior Returning Alive title.

## Durable contract

- `03-bible/assets.json`: moodboard, critical assets, approval states, stage settings, cost approvals.
- `04-images/shot-specs.json`: compiled live-board direction plus image-pass amendments.
- `04-images/image-workflow.json`: model routing and per-shot stage requirements.
- `04-images/prompt-packets/`: exact submitted prompts and reference arrays.
- `04-images/generations.jsonl`: append-only generation, review, and selection truth.
- `04-images/status.md`: derived view only.

Read `references/versioned-review.md` for event and recovery rules. Never hand-edit derived workflow/status views.

## Verification

- Every live board row maps to generated, shared, or source-photo mode.
- Every Stage A prompt equals its current workbook Still (frame one) cell after whitespace normalization.
- No Stage A prompt contains action timecodes, Frozen action, Camera law, Continuity, or character must_hold material.
- Stage A packets contain moodboard references and no character-sheet image references.
- Stage B packets contain the selected base plus all relevant approved character sheets.
- Every likeness generation names its composition parent version.
- Files are immutable `shot-{nn}-v{nn}.png`, open locally, and match 4:3.
- Shared and source-photo shots never spend generation credits.
- Quality remains Vince’s call.