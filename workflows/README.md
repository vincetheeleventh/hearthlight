---
doc: WORKFLOWS
role: catalog
authority: canon
owner: vince
updated: 2026-08-05
answers:
  - which routes from storyboard to finished clip exist
  - which one to use for a given shot
  - which one actually won, and on what evidence
not_here:
  the argument for cataloguing workflows: archive/decisions/D-022.md
  how to write the prompts themselves: skills/hearthlight-video-prompts/
---

# WORKFLOWS — the routes from storyboard to finished clip

A **workflow** is a complete route from an approved storyboard to a delivered clip. More than one
route exists. They are not stages of each other — they are **alternatives**, run in parallel and
compared on real shots.

This catalog exists because *"workflows live in one person's head"* is a named core problem
(`GOALS.md`). A route that worked gets written down and becomes repeatable. A route that failed
leaves a lesson. Neither should depend on Vince remembering.

---

## The routes

| ID | Name | Status | Route |
|---|---|---|---|
| **board-intake** | [Board Intake](board-intake.md) | **ACTIVE — run first** | photographed boards → panels as files → canonical shot record. Not a route to a clip; the *state* both routes below assume |
| **shot2video** | [Shot-Image → Video](shot2video.md) | **ACTIVE — v1 path** | storyboard → one conditioning still per shot → i2v from that still |
| **board2video** | [Storyboard → Video Direct](board2video.md) | **ACTIVE — parallel trial** | storyboard → video, conditioned on asset sheets + style reference. No per-shot still. |

**board-intake runs before either.** It is idempotent — re-run it whenever boards are redrawn or the
workbook is re-pasted. `hearthlight-selfcheck` WARNs per project when it has not been run.

> **Plain-language versions of both routes live in [`guides/`](../guides/README.md)** — written for
> Vince at the bench rather than for an agent settling an argument. Start with
> [`guides/assets.md`](../guides/assets.md); both routes stand on the sheets.

Both clip routes are live. shot2video is carrying the Yu-Gi-Oh! film; board2video is being trialled alongside it on the same
shots to find where each one wins.

### The difference that matters

**shot2video buys control and pays in passes.** Every shot gets a still that Vince approves before any
video spend. Framing, likeness, and composition are settled in a cheap medium. The cost is two
review loops per shot and a still that can itself drift.

**board2video buys speed and pays in specificity.** No still to approve, so a shot goes from board to
motion in one step. Identity is held by the character and location sheets instead of by a frame.
The cost is that the model decides framing, and a weak asset sheet has nowhere to hide.

They fail differently, which is the whole reason to run both.

---

## Choosing a route

Neither is the default yet — that is what the trial is for. Until there is evidence, use this:

| The shot is… | Try |
|---|---|
| A detonation beat, or any shot where composition *is* the meaning | **shot2video** — approve the frame before it moves |
| A close-up carrying likeness | **shot2video** — likeness is cheaper to fix in a still |
| Coverage, connective tissue, an establishing wide | **board2video** — the specificity premium is not worth two loops |
| A shot already reshot twice through one route | **The other route.** Two strikes means the route is wrong, not the wording |
| Motion the still cannot imply (a fall, a collapse, a fast reveal) | **board2video** — a still of the midpoint teaches the model the wrong thing |

## Comparison ledger

One row per shot tried through a route. **This is the point of the exercise** — without it, the
trial produces opinions instead of an answer.

Fill it in as shots come back. Attempts = iterations to an approved clip.

| Shot | Route | Attempts | Cost | Verdict | What decided it |
|---|---|---|---|---|---|
| *(no trials logged yet)* | | | | | |

**Verdicts:** `WON` · `LOST` · `TIE` · `PARKED` (two strikes, moved on)

**Rules for the ledger**

- Log the failures. A route that failed on a shot type is the most useful row here.
- One variable at a time. Comparing shot2video with an approved still against board2video with a half-finished
  character sheet measures the sheet, not the route.
- Name what decided it, not just which won. *"board2video lost — hands drifted on the close-up"* is a
  finding. *"shot2video was better"* is not.
- **Ten-to-fifteen rule.** If a shot has not come together in that many iterations, the problem is
  not the wording. Simplify the shot: split it in two, remove an action, change the angle.

## When a route proves itself

The trial ends when the ledger says something. Then:

1. The winning route's document is promoted — status **ACTIVE — v1 path**.
2. The losing route stays in the catalog with status **PARKED** and its evidence intact. Parked is
   not deleted; a route that lost on dialogue may still win on action.
3. The lesson goes into `DECISIONS.md`, one line, with the argument archived.
4. `PRODUCT_SPEC.md` § pipeline is updated to describe what is actually run.

## Adding a route

New routes are welcome — that is the point of a catalog. A new workflow document needs:

- **What it is** in two sentences, and what it is an alternative *to*
- **When to use it** — the shot types it should win on, stated before the trial so the trial can
  falsify it
- **Inputs** — exactly what must exist first, with paths
- **The route** — numbered steps, each naming the skill that owns it
- **Cost** — generations per approved shot, and where the review loops are
- **Known failure modes** — how it breaks, so a bad result is diagnosed rather than re-rolled
- **Status and evidence** — trial / active / parked, and what the ledger says

A workflow with no named failure modes has not been run enough to catalog.
