---
name: hearthlight-shot-runner
description: Batch execution engine for the render stages. After a gate passes, turns the approved shot list into a written batch plan (exact paths, exact prompt sources, verification steps, no placeholders), then executes it shot by shot — fresh subagent per shot, two-stage review (Stage A spec compliance judged by the machine; Stage B quality judged ONLY by Vince in Telegram), a durable progress ledger so a crashed session never re-renders paid generations, and a two-strike parking rule so one stubborn shot never stalls the batch. Use at Stage 4 (conditioning images, after Gate 2/3) and Stage 6 (Seedance clips, after Gate 4/5). Adapted for Hearthlight from obra/superpowers (MIT): subagent-driven-development + writing-plans + verification-before-completion.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, batch, execution, subagents, review, ledger, stage-4, stage-6]
    category: hearthlight
---

# Hearthlight — Shot Runner (batch execution between gates)

## The idea
Adapted from **superpowers**' subagent-driven development. Its insight: a controller that
dispatches a *fresh* worker per task, reviews each result against spec, and tracks progress in a
durable ledger will run for hours without drifting. Hearthlight's translation: **shots are
tasks, the Aesthetic Bible is the spec, and quality is the one review the machine may never
perform.** The runner buys autonomy *between* gates while keeping the gates sacred.

**Core principle:** fresh subagent per shot + spec review per shot + ledger = a 28-shot batch
that survives crashes, never silently drifts, and lands on Vince's phone in reviewable batches.

**Continuous execution:** once a batch starts, do not stop to ask "should I continue?" between
shots. Stop only for: BLOCKED you cannot resolve, genuine ambiguity, or batch complete. (Vince
approved the batch at the gate — that ✅ is the instruction to run.)

## When to use
- **Stage 4:** conditioning images for the approved shot list (requires: style block LOCKED,
  Gate 2 passed; run `hearthlight-selfcheck` first — it blocks generation if the bible is DRAFT)
- **Stage 6:** Seedance clips for approved storyboard shots (requires: Gate 4 passed, prompts
  compiled by `hearthlight-video-prompts`, graph per `hearthlight-comfyui-graph`)
- Re-runs: any subset of shots Vince marked 🔁 at review

Not for: anything before a gate ✅. This skill executes approved work; it never originates
creative choices. A shot with an unresolved creative question goes to `hearthlight-shot-crew`,
not the runner.

## Two-stage image-pass prerequisite

Stage 4 is two batches, not one. For Krea style/composition, `krea_style_comp.py --project {slug} --all` is the sole compiler and `krea_style_comp_run.py` is the sole paid runner. The runner consumes immutable packets only; it never writes or expands a prompt. Run two calibration shots first, inspect Stage-A compliance, show the remaining cost/time preflight, then record explicit approval before `--all`. Krea receives the moodboard and neutral/raw K2 parameters but no character-sheet images. Each completed image is downloaded and written to `generations.jsonl` before the next submission. Matching request fingerprints skip; unfinished submitted jobs resume by job ID. After Vince confirms composition review and selects bases, run likeness preflight; GPT Image 2 receives the selected base plus every relevant approved local character sheet. Never dispatch likeness before base selection. Never dispatch a shared owner twice. Source-photo shots never dispatch. A recorded provider job is paid-and-done.
## Step 1 — Write the batch plan (no placeholders)
Before generating anything, write `projects/{slug}/0X-*/batch-plan.md`. One row per shot:

```markdown
### Shot 12 — Dad stands at the lawnmower
- conditioning image: 04-images/shot-12_v2.png          (Stage 6; Stage 4: "none — generating")
- character sheet:    03-bible/characters/dad-sheet.png
- prompt source:      05-storyboard/shotlist.md row 12 + crew entries (compiled verbatim)
- style conditioning: Krea Stage A moodboard ID + strength; textual stages use locked block verbatim
- output:             06-video/shot-12_v1.mp4
- duration target:    4.0s board → generate 5s (COMBO), trim in edit
- verify:             file exists · target AR · provider-correct style conditioning · required refs attached ·
                      duration ≥ target · audio setting as confirmed for this project
```

**Plan failures (from superpowers, kept):** "TBD", "similar to shot N", "adjust as needed",
a verify line with no checkable condition. Every row must be executable by a subagent with
zero session context. Self-review the plan against the shot list before starting: every
approved shot has a row; every row's paths exist (except outputs); no row contradicts the
distribution spec.

## Step 2 — Execute: fresh subagents, dispatched in PARALLEL
Dispatch worker subagents. Hand each artifacts as **files/paths, not pasted text** — the row from
batch-plan.md, the style block location, the graph template. A worker never inherits session history.

**Independent shot units run in parallel, not one at a time.** *(Vince's explicit correction:
"they could've been done in parallel via subagents… remember this for future runs." This supersedes
the earlier one-at-a-time caution.)*

- Dispatch via `delegate_task` batch, capped by `delegation.max_concurrent_children` (default 3),
  or the durable `hermes kanban` board.
- **Keep each worker's set small and contiguous — 3–5 shots.** An iterative subagent hits its
  tool-iteration cap (~50 calls) mid-batch and simply stops.
- Each worker reads its prompt **verbatim from a packet file** and returns artifacts as paths —
  never pasted text, never session history.
- Subagents must load deferred Krea MCP tools (`tool_describe(mcp__krea_ai__generate_image)`,
  `…get_job`) before calling them; they are not in the top-level tool list.

### Ledger integrity — non-negotiable under parallelism
**Parallel workers must NOT append to `generations.jsonl`** — or any append-only ledger —
concurrently. Interleaved writes corrupt it and lose events.

- **Orchestrator-serializes (preferred).** Workers write only their output file and RETURN
  `(asset path, job id, url)`. The orchestrator runs the `record` step afterward, one at a time,
  then reconciles the ledger against disk.
- If a worker must record itself, file-lock the append.

### Recovery — a cut-off worker with an in-flight job
A worker that hits its iteration cap can leave a job submitted but not recorded. **Never re-spend a
completed job.**

1. Read the worker's live transcript for the in-flight `job id`.
2. Poll it (`get_job`) — it has usually completed since the worker died.
3. Download the result and record it yourself.
4. Resume the remaining shots with a fresh worker.

Full reproduction recipe: `references/parallel-and-moderation.md`.

**Voice contract — paste verbatim into every worker prompt.** A fresh subagent does not inherit
`hearthlight-terse` and will return prose that lands straight in Vince's context. Both directions
must be governed:

```
VOICE: terse. Drop articles, filler, pleasantries, hedging. Fragments fine. No preamble,
no tool-call narration, no closing recap, no self-summary. State each fact once.
Never compress: Tier 1 style block, character signature block, prompt bodies, file paths,
commands — reproduce verbatim.
Report in the RETURN schema only. No prose outside it.

RETURN:
STATUS: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
OUTPUT: <path>
NOTE:   <one line — concern or blocker; omit if DONE clean>
```

The orchestrator never quotes worker returns back to Vince — it aggregates into counts, parked
reasons, and one seam offer.

Worker reports one of four statuses (superpowers vocabulary, kept exactly):
- **DONE** — output written, self-checked against the row's verify line
- **DONE_WITH_CONCERNS** — output written, but flagged (e.g. "wash looks glossier than refs").
  Read concerns; real doubt about the look → route to Stage B with the concern attached so
  Vince sees it beside the image.
- **NEEDS_CONTEXT** — missing input (path wrong, ref absent). Fix context, re-dispatch.
- **BLOCKED** — cannot complete (API down, key invalid, node rejects graph). Never force the
  same retry unchanged: fix the cause, or park (below). Mechanical blockers → selfcheck.

## Step 3 — Two-stage review (the heart of the adaptation)
**Stage A — SPEC compliance. Machine judges.** Mechanical, checkable, per shot:
- output file exists, non-trivial size, correct aspect ratio (distribution spec is law)
- style conditioning matches the stage: Krea Stage A uses approved moodboard ID/strength and contains no style/aspect scaffold in prompt prose; textual stages carry the Tier 1 block verbatim
- character conditioning matches the stage: Krea Stage A omits character sheets; likeness/textual stages use approved identity references and required signature rules
- duration ≥ board target (Stage 6); `generateAudio` matches what Vince confirmed for this project
- nothing extra: no shots generated that aren't in the plan (over-building is a spec fail)

FAIL → dispatch fix with the specific finding → re-check. Two failed fixes → **park the shot**
(mark PARKED in ledger with reason), continue the batch, report parked shots at the end.
One stubborn shot never stalls twenty-seven good ones.

**Stage B — QUALITY. Vince judges. Always.** Ship Stage-A-clean shots to Telegram in batches
of 3–5 by beat (existing convention): ✅ approve · 🔁 regenerate with note · ✏️ edit prompt.
The machine may *attach* observations (a worker's concern, a suspected drift) but **never
approves, rejects, or ranks quality itself.** Photoreal creep, a dead pose, a wash gone muddy
— Vince's eye only. Gates stay sacred; this skill widens the road between them, not through them.

## The ledger (durable progress — re-rendering costs real money)
Append-only `projects/{slug}/0X-*/batch-ledger.md`, one line per event:

```
shot-12: DONE      06-video/shot-12_v1.mp4  specA=pass  → review batch 3
shot-13: PARKED    seedance node rejects 14s combo — needs graph fix
shot-14: REDO(🔁)  "hands too detailed, let the wash blur them" → v2 queued
```

- **At runner start, read the ledger first.** DONE/approved shots are done — never re-dispatch
  (paid API calls; superpowers calls re-execution "the single most expensive failure," and here
  it's literal dollars). Resume at the first shot without a clean line.
- After any crash/restart, trust ledger + files on disk over conversation memory.
- Vince's 🔁 notes get logged verbatim (terse rules never compress his words) — they are
  taste data; general ones go to `profile/TASTE.md` via the offer protocol.

## Evidence over claims (verification-before-completion)
A shot is DONE when: file exists on disk + Stage A passed + ledger line written. A batch is
DONE when: every shot is approved-✅ or PARKED-with-reason, the ledger reconciles against the
plan (no orphans either direction), and the summary is logged to Notion (`hearthlight-notion-log`).
"Generation ran fine" is a claim; a path that opens is evidence. Report in terse register
(`hearthlight-terse`): counts, parked reasons, next seam offer.

## Red flags (never)
- Run before the gate ✅ or the selfcheck gate-block clears
- Let a worker inherit session history instead of its plan row
- Skip Stage A because "it's probably fine" — drift is silent by nature
- Judge quality, or auto-advance 🔁 fixes to approved
- Re-dispatch a shot the ledger marks DONE/approved
- Retry a BLOCKED shot unchanged a third time — park it
- Paste the whole bible into a dispatch — hand paths; the style block travels verbatim into
  the *prompt*, not the chatter

## Integration
`hearthlight-selfcheck` (pre-flight) → this skill ← `hearthlight-image-prompts` /
`hearthlight-video-prompts` (what to render) ← `hearthlight-shot-crew` (contested shots first)
→ `hearthlight-timing-intake` (approved outputs into the Resolve timeline) →
`hearthlight-notion-log` (batch summary). Offer at the seam after Gate 2/4 passes:
*"Batch is approved — want me to run it? I'll come back with the first 3–5 for review."*
