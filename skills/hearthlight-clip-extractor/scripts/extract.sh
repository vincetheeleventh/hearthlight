#!/usr/bin/env bash
# Hearthlight clip extractor — audio master + per-moment audio/video clips for storyboarding.
# Usage:
#   bash extract.sh master <source-video> <project-slug>
#   bash extract.sh clips  <source-video> <project-slug> <moments.tsv> [pad_seconds]
#
# moments.tsv (tab-separated, one moment per line):
#   NN<TAB>start<TAB>end<TAB>slug
#   01	27:20	27:50	the-plan
# start/end accept mm:ss, hh:mm:ss, or raw seconds. pad_seconds (optional) adds lead/tail.
#
# Paths assume the standard project layout under ~/.hermes/Story Studio/projects/<slug>/.
set -euo pipefail

STUDIO="/home/vxi/.hermes/Story Studio"
MODE="${1:?mode: master|clips}"
SRC="${2:?source video path}"
SLUG="${3:?project slug}"
PROJ="$STUDIO/projects/$SLUG"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found"; exit 1; }
[ -f "$SRC" ] || { echo "source not found: $SRC"; exit 1; }

# mm:ss / hh:mm:ss / seconds -> seconds (float)
to_sec() {
  local t="$1"
  if [[ "$t" == *:* ]]; then
    awk -F: '{ s=0; for(i=1;i<=NF;i++) s=s*60+$i; print s }' <<<"$t"
  else
    echo "$t"
  fi
}

base="$(basename "$SRC")"; stem="${base%.*}"

if [ "$MODE" = "master" ]; then
  mkdir -p "$PROJ/00-source/audio"
  # WAV is THE deliverable — PCM 48k, what Storyboard Pro / a DAW wants.
  ffmpeg -y -i "$SRC" -vn -c:a pcm_s16le -ar 48000 "$PROJ/00-source/audio/$stem-audio.wav"
  # Optional compressed archive — only if 4th arg is "m4a". Off by default (the
  # original video in 00-source/ already IS the archive; the copy is redundant).
  if [ "${4:-}" = "m4a" ]; then
    ffmpeg -y -i "$SRC" -vn -c:a aac -b:a 192k "$PROJ/00-source/audio/$stem-audio.m4a" \
      && echo "  (+ optional m4a archive)"
  fi
  echo "Audio master -> $PROJ/00-source/audio/$stem-audio.wav"
  exit 0
fi

if [ "$MODE" = "clips" ]; then
  TSV="${4:?moments.tsv path}"; PAD="${5:-0}"
  [ -f "$TSV" ] || { echo "moments file not found: $TSV"; exit 1; }
  OUT="$PROJ/01-intake/clips"; mkdir -p "$OUT"
  echo "# Clips manifest — $SLUG" > "$OUT/clips-manifest.md"
  echo "" >> "$OUT/clips-manifest.md"
  echo "| # | slug | source in | source out | dur(s) | audio | video |" >> "$OUT/clips-manifest.md"
  echo "|---|------|-----------|------------|--------|-------|-------|" >> "$OUT/clips-manifest.md"

  while IFS=$'\t' read -r NN START END CSLUG; do
    [[ -z "${NN:-}" || "$NN" == \#* ]] && continue
    s=$(to_sec "$START"); e=$(to_sec "$END")
    # apply pad, clamp start >= 0
    s=$(awk -v s="$s" -v p="$PAD" 'BEGIN{v=s-p; if(v<0)v=0; print v}')
    e=$(awk -v e="$e" -v p="$PAD" 'BEGIN{print e+p}')
    dur=$(awk -v s="$s" -v e="$e" 'BEGIN{printf "%.3f", e-s}')
    name="$(printf '%02d' "$NN")-${CSLUG}"
    # Audio: accurate seek (after -i), PCM 48k for Storyboard Pro / DAW
    # -nostdin is REQUIRED: without it ffmpeg consumes the loop's stdin (the TSV), so only row 1 runs.
    ffmpeg -nostdin -y -i "$SRC" -ss "$s" -to "$e" -vn -c:a pcm_s16le -ar 48000 "$OUT/$name.wav" 2>/dev/null
    # Video: accurate seek, re-encode (NOT -c copy — keyframe snap would shift the start)
    ffmpeg -nostdin -y -i "$SRC" -ss "$s" -to "$e" -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k "$OUT/$name.mp4" 2>/dev/null
    # Self-verify: clip should exist and be ~dur long (within 0.5s)
    got=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$name.wav" 2>/dev/null || echo 0)
    ok=$(awk -v g="$got" -v d="$dur" 'BEGIN{print (g>0 && (g-d<0.5 && d-g<0.5))?"OK":"CHECK"}')
    echo "| $NN | $CSLUG | $START | $END | $dur | $name.wav | $name.mp4 |" >> "$OUT/clips-manifest.md"
    echo "cut $name  ($START–$END, +${PAD}s pad)  audio_dur=${got}s [$ok]"
  done < "$TSV"
  echo "Clips -> $OUT  (manifest: clips-manifest.md)"
  echo "Spot-check: play one .wav and confirm it starts on the intended word."
  exit 0
fi

echo "unknown mode: $MODE (use master|clips)"; exit 1
