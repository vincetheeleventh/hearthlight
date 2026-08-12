---
name: hearthlight-timing-intake
description: The timing round-trip between Hearthlight and an editor (Storyboard Pro / DaVinci Resolve). INTAKE — parse a Storyboard Pro Final Cut XML (per-panel clips) into per-shot durations that feed the shot list, the clip-extractor's audio cuts, and Seedance duration targets. ALSO — turn a hand-drawn board (panel images + CSV timing + VO audio + description) into a rough shot list, with VO transcribed (faster-whisper) and panels reconciled into shots (no-cuts). EXPORT — write an FCP XML so generated panels/clips + VO assemble into a watchable timeline in Resolve. One timing source; the board's pace becomes the system's pace.
metadata:
  hermes:
    tags: [hearthlight, timing, xml, davinci-resolve, storyboard-pro, round-trip]
    category: hearthlight
---

# Hearthlight — Timing Intake & Timeline Export (the round-trip)

## The idea
The editing timeline is the **shared document** between Vince and the system. Vince times panels
to the VO in Storyboard Pro; the system ingests that timing and inherits his pace instead of
re-guessing it. The system generates panels/clips; it writes them back into a timeline Vince
watches in DaVinci Resolve with the VO synced. The format both tools speak is **Final Cut XML
(xmeml v4)** — the lingua franca of editing handoff. Scripts: `scripts/timing.py` (intake),
`scripts/build_timeline.py` (export). Both run in WSL with `python3` (stdlib only, no installs).

## INTAKE — Storyboard Pro XML → the pipeline
**Required export:** in Storyboard Pro, export Final Cut XML with **one clip per panel** (NOT a
flattened movie). Verify the file has many `<clipitem>` on the video track (one per panel), each
with its own `<start>`/`<end>`/`<duration>` in frames. (The flattened export — a single video
clipitem — does NOT carry per-panel timing; re-export if you see only one.)

```bash
python3 scripts/timing.py parse    export.xml            # sanity table (panels, durations)
python3 scripts/timing.py shotlist export.xml            # markdown durations for the shot list
python3 scripts/timing.py moments  export.xml > 01-intake/clips/moments.tsv   # audio cut list
python3 scripts/timing.py seedance export.xml            # per-panel Seedance duration targets
```
- Frames → seconds = frames ÷ fps (the XML declares fps; this board is 24). Verified: 97f=4.04s.
- **Clips are named generically** (`name-2-1`, `-2-2`...) → join to panels/shots by **ORDER**
  (panel N = shot N). If a panel is inserted/deleted, numbering shifts — re-export and re-intake.
- Writes feed THREE consumers from ONE source: shot-list durations, the clip-extractor's
  `moments.tsv` (so audio cuts share the exact timecodes), and Seedance per-clip targets.

### Seedance duration + the COMBO constraint (generate-long-then-trim)
Seedance's `duration` is a fixed COMBO (verify the node's allowed values; default assumed
[5,10,14]). A panel timed to 3.2s can't be a 3.2s generation — `seedance` mode rounds UP to the
nearest allowed length (generate generously), and you **trim to the board's exact duration in the
edit**. The board timing is the authority; generation just needs to cover it.

## HAND-DRAWN BOARD INTAKE — board exports → rough shot list
The repeatable "run the system on my hand-drawn board" path. Vince draws panels in Storyboard Pro,
times them to the VO, and exports four things into one folder:
- **panel images** (`*-S-P.jpg`, labelled scene-panel)
- **a CSV** (`SceneName,PanelName,Transition,SceneFrames,PanelFrames`) — the panel timing
- **the VO audio** (`*.wav`) — the real interview voice (the treasure)
- **a description** (`storyboard_description.txt`) — Vince narrating each panel's action

### Step 1 — transcribe the VO (precise word timestamps)
```bash
source ~/.hermes/"Story Studio"/.venv-stt/bin/activate     # the studio STT venv (faster-whisper)
python scripts/transcribe.py "/abs/path/vo.wav"            # -> vo.words.tsv / .segments.tsv / .srt / .json
```
- **Model choice: faster-whisper large-v3, word timestamps ON.** Chosen over insanely-fast-whisper
  because we need PRECISE per-word times to align VO to panel boundaries; ifw is faster but its
  timestamps are chunk-level/loose. For short studio VO, precision > speed. (Upgrade path if word
  alignment ever drifts: WhisperX.) Runs on the 3090 (float16) or falls back to CPU int8 — either
  way a 79s clip is seconds-to-a-minute. Model auto-downloads (~3GB) on first run to the HF cache.
- `vo.words.tsv` (start⇥end⇥word) is the **alignment authority**; `.srt` is for a quick listen-along.

### Step 2 — build the rough shot list (timing + VO + no-cut grouping)
```bash
python scripts/board_intake.py --csv board.csv --words vo.words.tsv --scene 2 > rough.md
# board predates the no-cut convention? pass explicit panel merges:
python scripts/board_intake.py --csv board.csv --words vo.words.tsv --scene 2 --nocuts "6+7,8+9,10+11" > rough.md
```
Emits a panel-level table (exact CSV durations + audio-accurate VO per panel) and a **panel→shot
grouping**. Then hand-curate the prose (the script's word-split is rough at boundaries — snap to
sentence sense, and honor the drawn intent, e.g. a detonation line held on one ECU panel).

### No-cut reconciliation (panels → shots) — the core gotcha
Storyboard Pro exports **one numbered panel per drawing**, but the film has fewer **shots** than
panels: a "no-cut" is the *same camera setup* with an action/expression change inside it (head lifts,
Dad sits, hand dials). Those panels are **one shot** → **one conditioning image** at the image stage,
with the change rendered as a *motion beat*, NOT a second drawn panel. Reconcile, in priority order:
1. **[PREFERRED] Encode cuts in the Scene/Panel hierarchy.** In Storyboard Pro, make **each cut its
   own Scene** and keep no-cut beats as **multiple Panels within that Scene**. Then the CSV's
   `SceneName` column *directly* gives the shot grouping — `board_intake.py` groups by scene, zero
   guessing. This is a ~30s habit change in the drawing tool and makes the board self-describing.
2. **Fallback `--nocuts "6+7,8+9"`** — explicit panel-number merges, for boards drawn as one big
   scene (like the pilot's Scene 2, which is all "Scene 2"). Carry the merge list from Vince's notes.
3. (The `Transition` CSV column could also mark cuts, but empty-vs-cut is ambiguous — prefer #1.)

## EXPORT — assets + timing → a watchable timeline in Resolve
Build an FCP XML that holds each asset for its timed duration on the video track + the VO on the
audio track. Drop into DaVinci Resolve (File → Import → Timeline) → it auto-builds; press play.

```bash
# assets.tsv:  duration_seconds<TAB>absolute_path   (one per shot, in order)
python3 scripts/build_timeline.py assets.tsv /abs/path/vo.wav out.xml --fps 24 --w 1080 --h 1920
```
- **Tier 1 (now):** point assets at hand or generated PNG **stills** → an animatic with VO at real pace.
- **Tier 2 (later):** point at Seedance **video clips** → the animated film at your timing. Same script.
- Durations come from the intake (or the shot list). Paths must be absolute and reachable by Resolve.

## The round-trip discipline (so it stays safe)
- **The XML carries TIMING + ASSETS only.** Captions, crew per-dimension entries, story meaning live
  in the shot list / Notion — Resolve has no field for them. Two synced layers, never merged.
- **Re-time in Resolve → export XML → re-intake** closes the loop: the new durations flow back via
  `timing.py`. Structure travels; meaning stays home (same rule as storyboard-vs-prompt).
- **One timing authority at a time.** If Vince re-times in Resolve AND in Storyboard Pro between
  intakes, last export wins — pick one as the source for a given pass.

## Why DaVinci Resolve for watchback
Resolve is the NLE (free, robust XML/AAF import, smooth playback of stills+audio or video+audio).
Storyboard Pro is the drawing inlet; Resolve is the watch/edit outlet. The system speaks XML to both.

## Pitfalls
- Flattened export (one video clipitem) → no per-panel timing. Re-export with per-panel clips.
- Assuming Seedance can hit arbitrary durations — it can't; round up + trim.
- Letting captions/meaning ride the XML — they get lost; keep them in the shot list/Notion.
- Relative asset paths in the export — Resolve needs absolute, reachable paths.
- Frame-rate mismatch — always read fps from the XML, don't assume 24 (this board IS 24, others may differ).
- **Treating panels as shots.** Storyboard Pro numbers every drawing; no-cut beats are ONE shot.
  Reconcile before image generation or you'll draw redundant conditioning frames. See no-cut section.
- **Trusting the script's raw VO word-split.** Midpoint assignment splits words awkwardly at panel
  boundaries; always hand-curate the prose against `.srt`/`.segments.tsv` and the drawn intent.
- **A shortened/edited transcript ≠ the real audio.** Always transcribe the actual VO `.wav`; don't
  fill the dialogue column from a hand-trimmed extract (the pilot's first pass had this exact error).
- **STT venv, not the gateway python.** transcribe.py needs `~/.hermes/"Story Studio"/.venv-stt`
  (faster-whisper). The gateway's system python does NOT have faster-whisper on its path.

## Verification
- `timing.py parse` shows the right panel count and plausible durations (held beats long, inserts ~1s).
- `moments.tsv` round-trips through the clip-extractor and cuts audio at the same timecodes.
- The exported XML imports into Resolve and plays the panels at board timing with the VO synced.
- Generated Seedance targets round UP to allowed values; edit trims to board exact.
