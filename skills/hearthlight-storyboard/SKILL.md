---
name: hearthlight-storyboard
description: Hearthlight Stage 5 (Gate 4) — assemble the storyboard doc from approved images + A/V script: motion intent, durations, transitions. The single source of truth for video generation; Seedance prompts derive from it, never improvised.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, storyboard, motion, gate-4]
    category: hearthlight
---

# Hearthlight — Storyboard (Stage 5, Gate 4)

## When to Use
After Gate 3 (all beat images approved and sequence locked).

## What this document is
`05-storyboard/storyboard.md` — one entry per shot, assembled from the approved images and the A/V script. It is the **single source of truth for video generation**: Stage 6 prompts are derived from it mechanically. If something about a shot isn't in the storyboard, it doesn't exist.

## Entry format (one per shot, in sequence)
```markdown
## Shot {nn} — {title}
Image: 04-images/beat-{nn}-v{n}.png   (the approved version, by exact filename)
VO: [{mm:ss}–{mm:ss}] "{verbatim segment text}"
Duration: {n}s
Motion intent: {what moves, and only what moves}
Transition out: {cut / dissolve / hold-to-black / match note}
```
Titles follow the seedance practice: the dramatic point, not a label — `The Receiver, Lifted`, not `Shot 3 CU`.

**Narrative sidecar.** Alongside the registry lives `05-storyboard/shot-narrative.json` (contract:
dashboard skill's `SHOT-IDENTITY-PROTOCOL.md`) — per `shot_id`: the `one_liner` the shot answers to,
`expanded` narrative, `open_loops`, `why_this_shot`, and `staging` split into `surfaced` (what the
viewer registers: shot type, camera move, actions, setting) and `ambient` (what they feel but never
notice: props, lighting, sound). One-liners are born at outline/crew time and carried in here —
assembling the storyboard, fill or update each shot's entry; a shot that resists a one-liner is a
story problem to flag, not a field to skip. Hearthlight Studio renders this layer on the shot page.

## Motion vocabulary — what suits ink-and-watercolour stills
The conditioning frame is a hand-painted still. Motion must feel like the painting breathing, never like footage. Approved register, in increasing order of boldness:
- **Atmosphere:** dust motes in light, steam rising, rain on the booth glass, watercolour bloom subtly spreading
- **Light:** a pool of light warming or fading, headlights sweeping past, shadow lengthening
- **Camera:** barely-perceptible breath; slow push-in; slow pull-out (the workhorses — most shots want one of these and nothing else)
- **Figure:** small singular gestures — fingers tightening on the cord, a head bowing, chest rising with a breath
- **Forbidden:** walk cycles, full-body action, head turns to camera, fast pans/whips, anything that demands the model redraw the figure substantially — that is where the painted look dies

One motion idea per shot as the default. Two maximum (e.g. push-in + steam). If a beat seems to need more, that's an A/V-script problem, not a motion problem — flag it.

## Duration heuristics (from the seedance practice)
2s quick inserts · 3s gestures/punctuation · 4s standard beats · 5s held shots and the detonation beat · 6–8s exceptional stillness only. Sum the durations against the VO segment length — total clip time should cover the VO with a small tail, and the cut rhythm should breathe with the speech (cuts land in the pauses, not mid-phrase).

## Lip sync policy
The VO is interview audio — the older voice remembering. The illustrated figures are the memory. **Default: figures do NOT mouth the VO words.** A figure may speak silently within the scene (we see the call happen; we hear the man remember it) — if so, write `mouth moves, inaudible within scene` explicitly. Any true lip-sync exception is Vince's call, flagged at the gate.

## Procedure
1. Read the A/V script and `04-images/status.md`; confirm every beat has an approved image (if not, stop — Gate 3 isn't actually closed).
2. Draft entries in sequence. Read the whole sequence before finalizing durations — rhythm is global, not per-shot.
3. Post to Telegram as one document with a per-shot summary table. **GATE 4:** explicit ✅.

## Pitfalls
- Motion intent that re-describes the image instead of naming the change.
- Action-movie verbs in a watercolour world.
- Durations chosen shot-by-shot without hearing the VO rhythm.
- Deriving anything in Stage 6 that isn't written here.

## Verification
- Every shot: approved image filename, VO timestamps, duration, exactly one (max two) motion ideas, transition.
- Durations sum to VO length + tail.
- `GATE 4 PASSED {date}` at the top after approval.
