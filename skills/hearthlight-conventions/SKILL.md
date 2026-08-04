---
name: hearthlight-conventions
description: Hearthlight project conventions — directory structure, file naming (generated assets AND reference images), the reference manifest, versioning, where media enters the system, and the gate protocol. Load at the start of any Hearthlight project work or when unsure where a file belongs.
version: 0.2.0
metadata:
  hermes:
    tags: [hearthlight, conventions, folders]
    category: hearthlight
---

# Hearthlight — Project Conventions

## When to Use
At the start of every project, before writing any file, or whenever unsure where something belongs. Other hearthlight-* skills assume these conventions.

## Directory structure
Every project lives at `projects/{slug}/` inside the Story Studio workspace. Slug: lowercase, hyphenated, short (`mcconaughey-call`).

```
projects/{slug}/
  00-source/      INPUTS ONLY. Interview video/audio/transcript, Vince's rant
                  recordings. Never modified, never generated into.
    audio/        audio-only master(s) extracted from source video (m4a + wav)
  01-intake/      rant-transcript.md, interview-transcript.md (timestamped),
                  segment-timestamps.md, consolidation-doc.md, vision-brief.md,
                  boneyard.md
    clips/        per-moment audio (.wav) + video (.mp4) clips cut for storyboarding,
                  + clips-manifest.md  (see hearthlight-clip-extractor)
  02-outline/     story-arc.md, beat-sheet.md, av-script.md
  03-bible/       mise-en-scene.md (the aesthetic canon), characters/{name}/,
                  research-deck.md, family-questions.md, assets.json
    refs/         REFERENCE-MANIFEST.md  ← required index; see the Reference Naming Law
      wardrobe/ vehicles/ props/ environments/ light/ period/ likeness/
      storyboard-panels/   hand-drawn boards
      _rejected/           culled refs — kept, never deleted, never shown as chosen
  04-images/      beat-{nn}-v{n}.png or shot-{nn}-v{nn}.png, prompts.md, status.md, generations.jsonl
  05-storyboard/  storyboard.md
  06-video/       clip-{nn}-v{n}.mp4, prompts.md
  07-final/       approved assets only, copied (not moved) from earlier stages
```

## How media enters the system
- **Large files (video, long audio):** Vince drops them into `00-source/` directly (Windows Explorer or WSL). Telegram bots cannot download files over ~20 MB — never ask him to send source video through chat.
- **Small files (voice rants, reference images):** may arrive via Telegram; save them to the correct folder immediately. Nothing exists only in chat history.
- On receiving any new source file, confirm in chat: filename, where you saved it, and what you'll do with it (playback check).

## Transcribing source media (00-source → 01-intake)
Source audio/video must be transcribed faithfully (fragments and asides included) into a timestamped doc in `01-intake/`. Tested workflow in this environment:

1. **Extract audio with ffmpeg** (installed): `ffmpeg -y -i in.mp4 -ar 16000 -ac 1 -c:a pcm_s16le out.wav`
2. **Transcribe with faster-whisper.** PITFALL: `python3 -m venv` FAILS here (`ensurepip`/`python3-venv` not installed, no sudo). Do NOT try to build a fresh venv. Instead reuse the existing venv at `/home/vxi/projects/research-agent-mvp/.venv` — it can `pip install faster-whisper`. Run:
   ```python
   from faster_whisper import WhisperModel
   m = WhisperModel("small.en", device="cpu", compute_type="int8")
   segs, _ = m.transcribe("out.wav", beam_size=5, vad_filter=True,
                          vad_parameters=dict(min_silence_duration_ms=400))
   ```
   - `small.en` is fast + accurate for clean English; bump to `medium.en`/`large-v3` only if fidelity demands it (slower download; no HF_TOKEN set, so unauthenticated/rate-limited).
   - Long interviews may already have a transcript dropped in `00-source/` — check first before re-transcribing.
3. Write the result to `01-intake/{interview|rant}-transcript.md` with `[mm:ss]` timestamps preserved per segment. This timestamping is what lets ideation/consolidation cite provenance like `[vince 02:14]`.

## Naming
- Source files: descriptive-lowercase (`interview-full.mp4`, `rant-2026-06-12.ogg`).
- Generated assets: `beat-{nn}-v{n}` for beat-based projects; `shot-{nn}-v{nn}` for storyboard-shot projects; `clip-{nn}-v{n}` for video. Use zero-padded identifiers and immutable version suffixes.
- Documents: exact names listed above; downstream skills look for them.
- **Reference images: the Reference Naming Law below. Applies to every project, every time.**

## THE REFERENCE NAMING LAW (global — never project-specific)

**The failure this exists to prevent:** `gr-31285929.png`. The McConaughey project carries twenty-three
files named like that. Nobody thinks in those terms. Vince thinks *"what's my dad reference,"*
*"what's my uniform reference."* A reference nobody can find is a reference nobody uses, and the
research that produced it was wasted.

**Every reference image, in every project, is named:**

```
{category}-{subject}-{detail}-{nn}.{ext}
```

- **lowercase, hyphen-separated, zero-padded two-digit index.** No spaces, no capitals, no underscores.
- **Category leads**, so a plain file browser sorts into meaningful groups without opening anything.
- **`{detail}` is what the image SHOWS**, never where it came from: `front`, `side`, `rear`, `detail`,
  `worn`, `pattern`, `interior`, `context`.
- **Rename on arrival.** Renaming happens as part of the download, not as a later tidy-up. A
  source-site filename must never land on disk, not even temporarily — that's how they survive.

| Category | Use for | Folder under `03-bible/refs/` |
|---|---|---|
| `wardrobe` | uniforms, clothing, boots, insignia | `wardrobe/` |
| `vehicle` | cars, trucks, anything driven | `vehicles/` |
| `prop` | hero objects, hand props | `props/` |
| `env` | locations, interiors, exteriors | `environments/` |
| `light` | lighting behaviour, shadow colour, time of day | `light/` |
| `period` | general era texture, packaging, signage | `period/` |
| `likeness` | real-person reference (rights note required) | `likeness/` |
| `style` | aesthetic exemplars feeding the moodboard | `refs/` root |

Examples: `wardrobe-dcu-blouse-front-01.jpg` · `vehicle-pickup-crewcab-side-02.jpg` ·
`light-backlit-blue-shadow-01.jpg` · `env-driveway-suburban-summer-01.jpg`

Hand-drawn boards keep their own slot: `storyboard-panels/board-panel-{nn}.{ext}`.

**Culled images move to `refs/_rejected/` — never deleted, never shown as if chosen**
(`hearthlight-reference-report`). A rejection is data; it stops the same wrong image being re-fetched.

### Grandfathering
Existing badly-named files are renamed **only as a coordinated change** across every doc that
references them by path (`assets.json`, `shot-specs.md`, `mise-en-scene.md`). Never rename a file
that a generation pipeline is pointing at without updating the pointers in the same pass.

## THE REFERENCE MANIFEST (required in every project)

Every project keeps `03-bible/refs/REFERENCE-MANIFEST.md`. A folder of images is not reviewable; the
manifest is what makes the collection usable by a human *and* by a prompt-writing agent.

Every row answers, on sight: **what is this, and what is it a reference FOR?**

| Field | Meaning |
|---|---|
| File | The compliant filename |
| Shows | What is visible in it — the reason it was kept |
| Status | `HAVE` on disk · `FETCH` sourced, not downloaded · `GAP` no source yet |
| Source | URL or named provenance |
| Licence | Recorded per file on download. **Never assumed.** |
| Confidence | `[verified]` multi-source · `[likely]` single source · `[stylized]` Vince's call |

Two rules that make the manifest earn its keep:

1. **Organize by role, not by filename.** Group by what the references are FOR. Collapse pools — a
   twenty-image resemblance sweep is one gallery with one caption, not twenty rows.
2. **Write the findings even when the images are missing.** A prompt can state a fact in words. Record
   what the drawing has to get right — pattern, cut, colour, and especially *what the subject is NOT*
   — next to the `GAP`. A sourced written finding beats a missing image, and it feeds prompts today.

### The fetch pipeline (the mechanical half)
1. Research surfaces a candidate URL (`hearthlight-research`).
2. Fetch → save into the category folder → **rename on arrival** per the law above.
3. Append the manifest row, licence included.
4. Register generation-relevant refs in `03-bible/assets.json` so the image pipeline can reach them.
5. De-duplicate by content hash — the same photo arrives from four different sites.
6. Cull pass → rejects to `_rejected/`, manifest row updated, never deleted.

_Ratified by Vince 2026-07-31, promoted from the yugioh project where it was first written._

## Versioning (immutability rule)
- Approved files are immutable. A revision is a new version (`-v2`), never an overwrite.
- For versioned image passes, `04-images/generations.jsonl` is append-only truth for generation, review, and final-selection events. `prompts.md` and `status.md` are derived human views. Older projects without JSONL keep `status.md` as their per-beat source of truth.

## Gate protocol
- Gates 0–5 map to stages 1.5–6 (see PRD §5). A gate passes only on Vince's explicit ✅ in Telegram.
- Record each gate pass at the top of the stage's main doc: `GATE n PASSED {date}`.
- Never start work belonging to a later stage while a gate is open.

## PROPOSED AMENDMENT — cockpit intake (Vince to ratify, 2026-07-30)
The Hearthlight cockpit (`hearthlight-dashboard`, localhost:8787) is now a valid
entry point for media and text. It files everything by these conventions:
- `03-bible/refs/environments/` — location reference images.
- `03-bible/refs/props/` — prop reference images.
- `03-bible/refs/storyboard-panels/` — hand-drawn boards (matches USER-GUIDE).
- `03-bible/characters/{name}/` — character sheets (existing rule; cockpit enforces it).
- `01-intake/rant-typed-{YYYYMMDD-HHMM}.md` — typed rants; treat exactly like a
  voice-note transcript (feed to the ideation loop).
- `01-intake/ideas-inbox.md` — appended loose ideas; sweep into ideation (take/park/no).
- Cockpit uploads never overwrite: collisions get `-v2`, `-v3` (immutability rule).
- **Check the intake on session start:** new rant-typed files or inbox entries you
  haven't processed are unread input from Vince. The cockpit and the agent meet in
  the folders, never in each other.

## Pitfalls
- Writing generated files into `00-source/` (inputs only, forever).
- Overwriting an approved asset (versions, always).
- Holding content in chat without writing it to the project folder.
- Inventing new folder names — if something has no home, ask Vince and propose updating this skill.
