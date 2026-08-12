---
doc: shot2video
role: workflow
authority: canon
owner: vince
updated: 2026-08-05
status: active
answers:
  - how a shot goes from storyboard to clip via an approved still
  - when to spend two review loops on a shot
not_here:
  the alternative route: workflows/board2video.md
  prompt craft: skills/hearthlight-video-prompts/
---

# shot2video — Shot-Image → Video

**Status: ACTIVE — the v1 path.** Currently carrying the Yu-Gi-Oh! film.

Every shot gets its own conditioning still. Vince approves the still, then the still conditions the
video. The alternative is [board2video](board2video.md), which skips the still entirely.

**What this buys:** framing, likeness and composition are settled in a cheap medium, before any
video spend. You see the shot before it moves.
**What it costs:** two review loops per shot, and a still that can itself drift from the bible.

---

## Inputs

Nothing starts until all of these exist:

| Input | Where | Owner |
|---|---|---|
| Approved storyboard | `projects/{slug}/05-storyboard/storyboard.md` | `hearthlight-storyboard` |
| Locked style block | `projects/{slug}/03-bible/mise-en-scene.md` | `hearthlight-mise-en-scene` |
| Character sheets + signature strings | `projects/{slug}/03-bible/characters/` | `hearthlight-character` |
| Shot registry with stable IDs | `projects/{slug}/05-storyboard/shots.json` | `hearthlight-dashboard` |
| Project identity (aspect is a composition law) | `projects/{slug}/project.json` | `hearthlight-distribution-spec` |

## The route

1. **Compile the still prompt** — `hearthlight-image-prompts`. Assembled from the mise-en-scène and
   the shot's vision. The style block is copied **verbatim**, never paraphrased.
2. **Generate the still** — three sub-stages, currently being built as they run: **style composition
   → likeness → final input image.**
3. **Vince approves the still.** Stage A (spec compliance: verbatim style block, aspect
   ratio, references) is machine-judged. Stage B (quality) is **Vince only**.
4. **Write the video prompt** — `hearthlight-video-prompts`, using the approved still as the
   conditioning frame. Performance comes from `hearthlight-acting`.
5. **Generate the clip** — `hearthlight-comfyui-graph` (Seedance i2v via RunningHub). The still goes
   to `image1`; the character turnaround sheet goes to `image2`.
6. **Vince approves the clip.** Watch one thing above all: does it still look *painted*?
   Photoreal creep is the enemy.

Batch execution at steps 2 and 5 is `hearthlight-shot-runner` — fresh subagent per shot, durable
ledger so a crashed session never re-renders a paid generation, two-strike parking.

## Cost

**Two approval loops per shot** — the still and the clip — and at least two paid generations. A shot that
needs three still attempts and two clip attempts costs five generations and five reviews.

This is the expensive route. It is worth it where the frame carries meaning and cheap where it does
not — which is the question the trial against board2video is meant to settle.

## Known failure modes

- **The still teaches the wrong thing on a motion shot.** A still of the midpoint of a fall implies
  a pose, not a movement. The model holds the pose. Shots whose meaning *is* motion are the clearest
  board2video candidates.
- **Still drift compounds.** An approved still that has quietly drifted from the style block passes
  its drift into every clip conditioned on it. This is why Stage A checks the style block verbatim.
- **Likeness looks right in a still and wrong in motion.** A face that is beautiful-but-slightly-fake
  survives a still review and collapses once it has to act. Pick the *believable* face, not the most
  beautiful one, and check for a catch-light in the eye — a dead eye cannot act.
- **Two review loops invite fatigue.** Still approvals get looser as a batch runs long. The
  spot-check discipline (full-res, not Telegram thumbnails) exists for this.

## Where it is strongest

Detonation beats. Shots where composition *is* the argument — small-in-frame for trapped, the same
frame inverted for private joy. Close-ups carrying likeness. Anything Vince would want to see before
it moves.
