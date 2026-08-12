---
name: hearthlight-comfyui-graph
description: Hearthlight Stage 6 plumbing — queue the local ComfyUI MiniMax H3 i2v graph that turns an approved still (plus an optional end frame) into a video clip. Owns the wiring; gets its prompt text from hearthlight-video-prompts. The RunningHub Seedance graph is parked.
metadata:
  hermes:
    tags: [hearthlight, comfyui, minimax, video]
    category: hearthlight
---

# Hearthlight — ComfyUI Graph (Stage 6 plumbing)

## When to Use
After the relevant storyboard shots are locked, to actually generate clips. This skill owns the **wire**. It does
NOT write the prompt — that comes from `hearthlight-video-prompts`.

---

# ACTIVE GENERATOR — local ComfyUI, MiniMax H3 i2v

```
C:\Users\vxi\Documents\ComfyUI\user\default\workflows\minimax_h3_i2v_int8.json
```

**Local, not RunningHub.** Confirmed working by Vince on `yugioh` Shot 1, 2026-08-05. This is what
runs today; everything below the RunningHub heading is parked.

## What it takes

| Input | Meaning |
|---|---|
| **Start frame** | The approved conditioning still — `04-images/shot-{nn}-v{nn}.png`, exact filename from the storyboard. Required. |
| **End frame** *(optional)* | Where the shot finishes. **New capability the Seedance graph did not have.** |
| **Text prompt** | From `hearthlight-video-prompts`, shot2video register: motion only, short. |

**One shot per generation.** This is the [shot2video](../../workflows/shot2video.md) route by
construction — it conditions on a frame, so there is no board2video path through this graph.

## The end frame changes how a shot is designed

With a start *and* an end frame, motion is **bracketed** rather than described. This is a
meaningfully better instrument than a prompt alone, and it changes the craft:

- **Use it when the destination matters** — a head that must finish turned, a hand that must arrive
  on the receiver, a figure that must end small in frame. Specify the arrival instead of hoping.
- **Use it to kill drift on long holds.** If start and end are near-identical, the model has nowhere
  to wander. This is the cheapest fix for a shot that keeps inventing movement.
- **Leave it empty when the motion is the point** and you want the model to find it — steam rising,
  a curtain moving, anything ambient.
- **Both frames must come from the same approved lineage.** An end frame generated from a different
  style pass reintroduces the drift the conditioning frame exists to prevent.
- **The pair must be physically reachable in the duration.** Two frames that imply more movement than
  the clip length allows produce a speed-ramp or a snap.

## Per-shot procedure

1. **Start frame** = the approved still for this shot. Never an unapproved candidate.
2. **End frame** = the approved destination still, or empty. Record which, per shot.
3. **Prompt** = `hearthlight-video-prompts`, carrying the medium preservation clause verbatim.
4. **Duration** = the board's timed duration (`hearthlight-timing-intake`), snapped up to an allowed
   value and trimmed in the edit. The board is the timing authority.
5. Queue locally. Save as `06-video/clip-{nn}-v{n}.mp4`.
6. Log prompt, both frame filenames, duration and seed in `06-video/prompts.md`. **A clip whose
   inputs were not logged cannot be reproduced** — and with a local graph there is no platform
   history to fall back on.

## Node map

Working copy: `references/minimax-h3-i2v-template.json` (versioned here — the project copy at
`projects/yugioh/workflow-development/comfy_graphs/` is gitignored and would never travel).
Verified no credentials. MiniMax H3 is omni-modal: text, image, video and audio in, video **with
native stereo audio** out. Up to 2K, 24fps, ~15s max.

| Node | Role |
|---|---|
| `LoadImage` "Starting Frame" | the conditioning still → `first_frame` |
| `LoadImage` "Ending Frame" | the destination still → `last_frame`. Optional |
| `ResolutionSelector` | aspect + megapixels → width/height, rounded to a multiple of 32 |
| `ImageScaleToTotalPixels` | conforms the input frames to that canvas |
| **`MiniMaxH3ImageToVideo`** | **the shot2video node.** `first_frame` / `last_frame` / `prompt` / `width` / `height` / `length` |
| **`MiniMaxH3ReferenceToVideo`** | **see below — this is the board2video surface** |
| subgraph `#105` | where the live config actually sits: prompt, 1344×768, duration, seed, model files |
| `SaveVideo` | output, `filename_prefix: video/MiniMax_H3` |

**Models:** `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (diffusion) ·
`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (text encoder) · `minimax_h3_video_vae_fp16` +
`minimax_h3_audio_vae_fp32` (VAEs).

**Canvas.** Native short edge is 768, capped at 768×1344, multiple of 32. The graph is set to
**16:9 @ 0.4 MP → 864×480**, which matches yugioh's declared 16:9 master. That is a **draft-grade
canvas** — fine and fast for iteration, but the final pass wants more: 0.98 MP gives 1344×768.
Decide deliberately rather than discovering it at the edit.

**Duration.** Seconds are converted to frames on the model's **17k+5 grid** — 5, 22, 39, 56, 73, 90,
107, 124 — snapping **up**. Generate generously and trim to the board's exact duration in the edit.

**One shot per generation** on the i2v node.

## `MiniMaxH3ReferenceToVideo` — the board2video surface

This node takes **`ref_images.ref_image_0`** (an expandable list), plus `ref_videos`, `ref_audios`
and a prompt. That is exactly what [board2video](../../workflows/board2video.md) needs and could not
find: a board sheet **plus** character and location sheets as separate tagged references, with a
one-line prompt.

**The generator gap flagged in that workflow is closed — it is a different node in the same graph,
not a different platform.** Untested for this purpose. Worth one deliberate trial before planning
the comparison.

## Audio — a real conflict to settle

H3 generates **voice, SFX and music jointly in a single forward pass**, and the model's own guidance
is to describe audio in the prompt alongside motion.

The imported prompt practice says the opposite: *"SFX only. No music."* — because on that platform a
generated soundtrack obstructed the edit. Both positions are reasonable and they cannot both be
followed.

**Unresolved.** Whether a project uses real recorded VO or generated audio is a per-project
production decision — ask, note it in the project, never silently flip it. What is new here is that
*declining* generated audio now needs saying out loud, because this model produces it by default.

## Open items

- **Both `LoadImage` nodes point at the same test file** (`pasted/image (23).png`). Expected for a
  first test; per-shot wiring must set them separately, and an end frame identical to the start frame
  is a deliberate "hold" instruction, not a default.
- **`width`/`height`/`length` on the top-level nodes are unlinked widgets** while the live config sits
  in subgraph `#105`. Know which one you are editing before a batch.
- **Local generation has no spend meter.** The shot-runner ledger still earns its keep — with local
  compute the cost is time and GPU, and a crashed session should not re-render an approved clip.
- **`workflow-development/` is a new folder** inside the project, not yet in
  `hearthlight-conventions`. Harmless, but it should be named there or it will be reinvented.

---

# PARKED — RunningHub Seedance 2.0

**Not in use.** Kept because it works and may return for shots needing multi-reference conditioning
or generated audio. Do not queue against it without saying so.

## The proven graph (from Vince's `wfu_whyacarrot.json`)
A working RunningHub workflow Vince has already run. Template lives at `references/seedance-i2v-template.json` (sanitized — API key replaced with a placeholder).

**Node map:**
- `RHSettingsNode` — `base_url: https://www.runninghub.cn/openapi/v2`, `apiKey: <from profile .env, never hard-coded>`. Output `api_config` → the video node.
- `RH_RhartVideoSparkvideo20FastMultimodalVideo` — the Seedance 2.0 **Fast** multimodal node. Endpoint `/rhart-video/sparkvideo-2.0-fast/multimodal-video`. Accepts up to 9 images, 3 videos, 3 audios.
  - `image1` ← **Load Image (Storyboard)** — the approved still, the i2v conditioning frame.
  - `image2` ← **Load Image (Character Sheet)** — identity reference from the Mise-en-scène (Aesthetic Bible) character sheets.
  - `prompt` ← the text from `hearthlight-video-prompts`.
  - `seed` ← `PrimitiveInt` (randomize to explore, fix to iterate — this node DOES expose seed, unlike gpt-image-2).
- `SaveVideo` — output, `filename_prefix` set per project.

**Parameters Vince has used (confirm per shot):** `resolution: 1080p` · `duration: 14` (COMBO — valid values are platform-specific; Seedance docs cite 5–15s, verify in the node's dropdown) · `ratio: 16:9` · `generateAudio: true` · `real_person_mode` (see rights note) · `skip_error`.

## Mapping a storyboard entry onto the graph
For each storyboard shot:
1. **image1** = the approved still file (`04-images/beat-{nn}-v{n}.png`, exact filename from the storyboard). Upload to RunningHub / point LoadImage at it.
2. **image2** = the relevant character sheet from `03-bible/characters/{name}/`.
3. **prompt** = generated by `hearthlight-video-prompts` (carries the watercolour preservation clause).
4. **duration** = the panel's timed duration from `hearthlight-timing-intake` (Vince's Storyboard Pro
   timing against the VO) — snapped UP to the node's nearest allowed COMBO value (generate generously),
   then trimmed to the exact board duration in the edit. The board is the timing authority, not a guess.
5. **seed** = randomize for first pass; fix when iterating a near-miss.
6. **ratio/resolution** = project defaults unless the storyboard says otherwise.
7. Queue. Save output as `06-video/clip-{nn}-v{n}.mp4`; log node params + prompt in `06-video/prompts.md`.

## Vince's real prompt convention (align `hearthlight-video-prompts` to this)
His working prompts are richer than a bare motion line. Observed shape:
- A directive: *"Create a video from the storyboard [Image 1]... Match the storyboard images exactly, composition and framing. No subtitles. Reference character sheet [Image 2]."*
- **Panel timing block:** `[0-3s] Panel 1` / `[3-10s] Panel 2 ...` with continuity notes ("no cut between panel 2 and 3").
- A `[Cinematography]` block and an `[Audio]` block.
This is compatible with our executor — `hearthlight-video-prompts` should emit this structure, with the preservation clause folded into `[Cinematography]`.

## ⚠ Two decisions this graph surfaces (flag to Vince, don't assume)
1. **Audio fork.** This workflow has `generateAudio: true` and detailed voice direction — **Seedance is generating the soundtrack**, including character voices. That is one product; a real recorded VO over near-silent clips is another. Which one a project wants is Vince's call per project — ask, don't assume, and never silently flip it mid-project.
2. **`real_person_mode` + rights.** This flag exists on the node. For the public-figure pilot, combined with the stylized-resemblance rule (PRD §3), Vince must set it deliberately. Surface it; don't default it.

## Security
- The uploaded JSON contained a live API key. The sanitized template uses a placeholder. The real key belongs ONLY in `~/.hermes/profiles/hearthlight/.env` (e.g. `RUNNINGHUB_API_KEY=...`), injected into the Settings node at runtime — never written into any skill, template, or project file. **Vince should rotate the exposed key** (RunningHub dashboard) since it was shared in plaintext.

## Pitfalls
- Hard-coding the API key anywhere but `.env`.
- Using a non-approved still as image1, or skipping the character sheet on image2 (identity drift).
- Setting a `duration` the node's COMBO doesn't offer (it will reject or clamp).
- Flipping `generateAudio` or `real_person_mode` without Vince's say-so.
- Queuing the whole sequence before one clip proves the watercolour look survives (RunningHub credits are real money).

## Verification
- Settings node reads its key from env, not literal text.
- image1 = approved still (filename matches storyboard), image2 = character sheet.
- Prompt came from `hearthlight-video-prompts` and contains the preservation clause.
- Output saved to `06-video/clip-{nn}-v{n}.mp4`; params logged in `prompts.md`.
- Audio + real_person_mode settings were explicitly confirmed for this project.
