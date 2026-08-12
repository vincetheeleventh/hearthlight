---
name: hearthlight-video-prompts
description: Hearthlight Stage 6 — write one image-to-video prompt per locked storyboard shot and queue it through the current ComfyUI workflow. Adapt motion from the board and condition from the selected still without inventing new action.
metadata:
  hermes:
    tags: [hearthlight, video, seedance, comfyui]
    category: hearthlight
---

# Hearthlight — Video Prompts & Generation (Stage 6)

## When to Use
After the relevant storyboard shots are locked. One prompt per storyboard entry, derived mechanically — nothing improvised at this stage.

## Which workflow are you on?
Two routes reach a clip, and they need different prompts. Read `workflows/README.md` first.

- **shot2video — Shot-Image → Video.** An approved still conditions the clip. **The image carries the look;
  the prompt carries only the motion.** This is what the rest of this SKILL.md describes.
- **board2video — Board Sheet → Video.** No still. A rendered storyboard sheet carries framing, order
  and intent for a 10–15s sequence (`hearthlight-board-sheet`), and **the prompt is one sentence**:
  *"Create a video according to the storyboard."* Long structured prompts belong here only when
  chaining several shots in one generation — never on a single shot.

Getting this backwards is the common error. **A long prompt on a single shot2video clip re-describes
what the still already settled and invites the model to repaint the frame.** The source practice's
3,000–4,000-word prompts were written for multiple chained shots; they do not belong on one i2v job.

**Performance in either route comes from `hearthlight-acting`.** Motion is not performance.

## The i2v difference (critical adaptation of the seedance practice)
Vince's seedance format was built for text-to-video shot lists. Here every generation is **image-to-video, conditioned on the approved still**. That changes what the prompt is for:
- **The image carries the look.** Composition, character, palette, style live in the conditioning frame. Do NOT re-describe what the still already establishes — re-description invites the model to repaint it.
- **The prompt carries the motion.** Describe only what changes: the named motion intent, its quality and pace, what stays still.
- **Defend the medium.** Seedance will drift toward photoreal physics when animating. Every prompt includes the preservation clause, verbatim:
  `Preserve the hand-painted ink and watercolour look of the source image throughout; paper texture constant; no transition toward photorealism.`

## Format — aligned to Vince's working RunningHub prompts
His real prompts (see `hearthlight-comfyui-graph`) are structured, not a single line. Emit this shape:
```
Create a video from the storyboard [Image 1], following the action. Match the storyboard
image exactly — composition and framing. No subtitles. Reference character sheet [Image 2].

[panel/timing block]
[0-3s] Panel 1 — {what moves}
[3-Xs] Panel 2 — {what moves; continuity notes e.g. "no cut to panel 3"}

[Cinematography]: {camera behavior from the conservative register} + {motion intent, pace,
what stays still} + Preserve the hand-painted ink and watercolour look of the source image
throughout; paper texture constant; no transition toward photorealism.

[Audio]: {per project — see audio fork below}
```
The `[Image 1]`/`[Image 2]` tags refer to the graph's wired inputs (storyboard still, character sheet). The preservation clause lives inside `[Cinematography]`.

**Audio fork:** Vince's multimodal node can *generate* audio (`generateAudio`). Where a project uses a real recorded VO instead, the `[Audio]` block should say `No generated audio — recorded VO added in post` and `generateAudio` is set false in the graph. Other projects may want generated or scored audio, in which case write the `[Audio]` block as real direction. Confirm per project, never assume. (Details in `hearthlight-comfyui-graph`.)

### Legacy single-block format (still valid for non-RunningHub targets)
```
[Xs] Title From the Storyboard
Single paragraph: camera behavior, then motion intent, then the preservation clause.
```
- `[Xs]` = the storyboard duration, single value, never a range.
- Title = the storyboard title verbatim.
- No shot numbers, no meta-commentary inside the block, no storyboard/sketch references in the prompt body — the conditioning image is an API parameter, not prompt text.

## Example
Storyboard entry: *Shot 04 — The Receiver, Lifted. Image: beat-04-v2.png. Duration 4s. Motion: slow push-in; steam from the coffee cup on the booth shelf. Transition: cut.*
```
[4s] The Receiver, Lifted
Slow push-in toward the figure at the payphone, barely perceptible, steady. Steam rises gently from the coffee cup on the booth shelf and drifts; the figure holds still, receiver at his ear, fingers tight on the cord. Everything else in the frame remains motionless. Preserve the hand-painted ink and watercolour look of the source image throughout; paper texture constant; no transition toward photorealism.
```

## Input: compile the crew's per-dimension entries (the keystone handoff)
When a shot was designed by `hearthlight-shot-crew`, its row carries a **crew-entry block** — one
line per dimension (Layout / Value / Background / Continuity / Posing / Motion / Sound), each stating
that dimension's intent for the shot AND how it connects to the arc. **Your job is to COMPILE those
entries into one Seedance prompt — not to invent the shot.** The crew thought per-dimension; you
assemble their intents into a single coherent i2v prompt, resolving phrasing (not creative) conflicts.
- Read every crew entry for the shot. Fold Layout→framing language, Value→light/value description,
  Posing→what the figure does, Motion→the motion intent, Continuity→what must stay consistent,
  Background→the painted world, into the prompt's natural prose.
- Preserve the Tier-1 style block verbatim and the watercolour preservation clause (below).
- If a shot has no crew entries (routine, Mode A), compile from the shot row directly as before.
- The crew entries are the score; you are the player. Don't override their dimension calls — translate them.

## The prompt-director references
Three companion files under `references/`. Adapted from an outside production practice, proprietary
and platform-specific naming removed. **For board2video sequences and for diagnosing a stuck shot**; on a routine shot2video clip, reach for them when it
keeps missing.

| File | Holds |
|---|---|
| `prompt-architecture.md` | The skeleton and its ordering · the character-count header · reference role-naming · the **`GEO SPATIAL LAYOUT`** block that stops characters teleporting between shots · the one-second opening wide · physics · scale anchors · positive-form constraints · iteration discipline |
| `optics-language-bank.md` | Six ready-to-paste FOV blocks (8° → 107°) · the lens decision tree · telephoto and wide **visual outcome stacks** · anti-drift locks · multi-shot lens consistency · optics anti-patterns |
| `failure-locks.md` | The four-D pass (deconstruct / diagnose / develop / deliver) · the diagnosis checklist · context isolation · when negatives are worth writing · safe verb and measurement vocabulary · the ban dictionary · the silent self-QA before sending |

**Why references and not a separate skill:** this skill already owns *the prompt words*. A second
skill claiming the same territory would create two places to state the same law — the drift D-002
exists to prevent. The craft is deep enough to warrant three files; it is not a separate stage.

**The three rules worth memorising:** positive control beats negative control · the model has no
memory, so every prompt is a sealed current-shot document · describe observable optical *outcomes*,
never lens metadata.

## Companion reference (vocabulary only)
For Seedance-specific phrasing, camera/lighting vocabulary, and i2v technique, you may consult `references/seedance-os-bridge.md` (a curated bridge to the Seedance 2.0 Skill OS repo). Borrow wording, never process — this skill's conservative motion register, lip-sync policy, file conventions, and preservation clause always win. For the pilot, read that repo's `seedance-copyright` notes: McConaughey is a public figure, stylized resemblance only (PRD §3).

## Carryover rules from the seedance practice
- Read the WHOLE storyboard before writing — rhythm is global.
- Present-tense, frame-bound description; convert any director's-note voice.
- Camera language from the conservative register only (locked-off, breath, slow push-in/pull-out — per the storyboard's motion vocabulary).
- Director-reference shorthand becomes visual qualities, never names.
- Lip sync: per storyboard policy, figures don't mouth the VO. If an entry says `mouth moves, inaudible within scene`, render it explicitly ("his lips move as he speaks into the receiver, words inaudible") — otherwise add "mouths do not move" when a figure could be misread as speaking.
- Flags and notes go AFTER the full block set, separated by `---`, never interleaved.

## Generation (ComfyUI → RunningHub → Seedance 2.0)
- Queue via the Hermes ComfyUI skill: conditioning image = the approved still (exact filename from the storyboard), prompt = the block's paragraph, duration = the block's `[Xs]`.
- Save outputs as `06-video/clip-{nn}-v{n}.mp4`; log every prompt + parameters in `06-video/prompts.md`.
- Vince reviews in ComfyUI and/or clips posted to Telegram. Same protocol as images: ✅ / 🔁 with note / ✏️; versions never overwrite; status tracked in `06-video/prompts.md`.
- Watercolour-fidelity check per clip: paper texture held? linework stable? any photoreal creep mid-clip? Two clips failing the same way → stop and re-examine the prompt pattern or workflow settings before burning more RunningHub credits.

When Vince approves a clip, copy it to `07-final/` (copy, never move) alongside the VO segment and storyboard. Assemble the edit from approved clips; other shots may continue iterating.

## Pitfalls
- Re-describing the still (repaint invitation).
- Omitting the preservation clause.
- Motion not present in the storyboard ("it felt static" requires a storyboard revision, not prompt liberty).
- Duration ranges, shot numbers, interleaved commentary, non-English text.
- Queuing big batches before the first clip proves the style holds.

## Verification
- One block per storyboard entry; durations and titles match the storyboard exactly.
- Preservation clause present in every prompt.
- `06-video/prompts.md` logs every generation; approved clips exist at the logged filenames.
- Each approved clip has a durable review event; `07-final/` is populated by copy.
