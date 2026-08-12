---
name: hearthlight-clip-extractor
description: Hearthlight media prep for storyboarding — extract an audio-only master from the source video, then cut chosen moments into matched audio + video clips using transcript timestamps, named for drag-and-drop into Storyboard Pro. Sits between transcript (Stage 1) and storyboard (Stage 5).
metadata:
  hermes:
    tags: [hearthlight, audio, video, ffmpeg, storyboard, clips]
    category: hearthlight
---

# Hearthlight — Clip Extractor (transcript → drawable clips)

## When to Use
When Vince is about to draw storyboards and wants the actual media of his chosen moments in hand: an audio-only library plus per-moment audio+video clips he can drag into Storyboard Pro and draw to. Triggered by "cut the clips," "extract the audio," "make the storyboard audio," etc. Requires `ffmpeg` (installed — see `hearthlight-conventions`).

## What it produces
```
projects/{slug}/
  00-source/audio/{source}-audio.wav         ← audio-only master (THE deliverable; PCM 48k)
                  {source}-audio.m4a         ← optional compressed archive (off by default)
  01-intake/clips/
    {nn}-{slug}.wav        ← audio clip per chosen moment (drag into Storyboard Pro)
    {nn}-{slug}.mp4        ← matched video clip (same moment, for reference)
    clips-manifest.md      ← what each clip is, its source timecode, the panel it feeds
```
Audio library = `00-source/audio/`. Drawable moment clips = `01-intake/clips/`.

## Inputs it needs
1. The source video (in `00-source/`).
2. The chosen moments. Accept ANY form:
   - **From the timed storyboard (preferred):** `hearthlight-timing-intake` produces a `moments.tsv`
     straight from Vince's Storyboard Pro XML — the panel timings he set against the VO. This is the
     best source: the audio cuts then share the EXACT timecodes as the video panels. Use it when it exists.
   - **Explicit time ranges:** `27:20–27:50` (mm:ss).
   - **Transcript chunk spans:** "chunks 1–6" referencing the 5-second-chunk transcript.
   A panel often spans several chunks; a clip = a dramatic beat. Confirm the moment list with Vince (playback check).

## Procedure
1. **Audio master** (once per source):
   ```bash
   bash scripts/extract.sh master "<source.mp4>" "<project-slug>"        # WAV only (default)
   bash scripts/extract.sh master "<source.mp4>" "<project-slug>" m4a    # + optional m4a archive
   ```
   WAV (PCM 48k) is the real deliverable — what you drag into Storyboard Pro. The m4a is an optional compressed archive and is OFF by default: the original video already lives in `00-source/`, so the copy is redundant. Don't force it.
2. **Per-moment clips:** build a moments file (or pass inline), then:
   ```bash
   bash scripts/extract.sh clips "<source.mp4>" "<project-slug>" moments.tsv
   ```
   `moments.tsv` lines: `NN<TAB>start<TAB>end<TAB>slug` e.g. `01	27:20	27:50	the-plan`. Cuts BOTH a `.wav` (audio) and `.mp4` (video) per row into `01-intake/clips/`.
3. **Manifest:** write `clips-manifest.md` — one row per clip: number, slug, source timecode, duration, which storyboard panel it feeds, audio + video filenames.
4. Post the clips dir path to Telegram / log to Notion working-notes so Vince can grab them. (Clips may exceed Telegram's 20 MB bot limit — point him at the folder, don't try to send large video through chat.)

## Cutting rules (frame/sample accuracy matters for drawing-to-audio)
- **Audio clips: re-encode, accurate seek.** `-ss` AFTER `-i` (or `-accurate_seek`) so the cut starts exactly where the word does — drawing to audio needs the first syllable on frame 1. Export WAV PCM 16-bit (Storyboard Pro / DAW friendly): `-c:a pcm_s16le -ar 48000`.
- **Video clips: accurate seek, re-encode** (don't `-c copy` for short clips — keyframe snapping shifts the start). `-ss`/`-to` after `-i`, re-encode H.264 + AAC so the clip starts on the exact moment.
- **Pad option:** offer a small lead/​tail pad (e.g. +0.3s each side) so a clip doesn't clip the first/last consonant — Vince's call per batch.
- **Timecodes come from the transcript**, which is why transcription preserved `[mm:ss]`. Keep clip = beat alignment so panel N's clip matches panel N's drawing.

## Naming (Storyboard Pro friendly)
- Zero-padded number + short slug: `01-the-plan.wav`, `02-the-dial.wav`. Number = panel order so they sort correctly in a file browser and drop in sequence.
- Audio and its matched video share the base name (`03-here-it-comes.wav` / `.mp4`).

## Pitfalls
- **ffmpeg eats the loop's stdin.** In a `while read` loop over the TSV, ffmpeg reads stdin by default and consumes the remaining rows — so only the FIRST clip cuts. Always pass `-nostdin` (fixed in `extract.sh`). Symptom: script reports just `cut 01-...` then exits.
- `-c copy` on short video cuts → start snaps to the nearest keyframe, audio/picture drift. Re-encode short clips.
- Seeking before `-i` without `-accurate_seek` → clip starts early/late. Put `-ss` after `-i` for accuracy.
- Forgetting the audio master is a *separate* deliverable from the moment clips — Vince wants both the whole-interview audio AND the cut moments.
- Sending big video clips through Telegram — folder path instead.
- Re-cutting over existing clips — version or confirm; don't silently overwrite approved cuts.

## Verification
- `00-source/audio/` holds the full audio master.
- `01-intake/clips/` holds matched `.wav` + `.mp4` per chosen moment, zero-padded, beat-named.
- `clips-manifest.md` maps every clip to its source timecode and storyboard panel.
- Spot-check one clip: does the audio start exactly on the intended word?
