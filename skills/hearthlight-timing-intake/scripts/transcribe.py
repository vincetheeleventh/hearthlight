#!/usr/bin/env python3
"""
transcribe.py — Hearthlight VO transcription (faster-whisper, word-level timestamps).

Why faster-whisper over insanely-fast-whisper: we need PRECISE word timestamps to
align VO to panel boundaries. faster-whisper (CTranslate2) gives true word_timestamps;
insanely-fast-whisper is faster but its timestamps are chunk-level and loose. For short
studio VO, precision beats speed. (Upgrade path if alignment ever drifts: WhisperX.)

USAGE (run inside the studio STT venv):
  source ~/.hermes/"Story Studio"/.venv-stt/bin/activate
  python transcribe.py /abs/path/vo.wav            # -> vo.words.tsv + vo.srt + vo.json next to audio
  python transcribe.py vo.wav --model large-v3 --device auto

Outputs (alongside the audio file, same basename):
  *.words.tsv  : start<TAB>end<TAB>word        (one row per word — the alignment authority)
  *.segments.tsv: start<TAB>end<TAB>text       (whisper's natural sentence segments)
  *.srt        : subtitle file (segments) for quick listen-along in any player
  *.json       : full result (segments + words) for programmatic use
"""
import sys, os, json, argparse

def fmt_ts(t):  # SRT timestamp
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--device", default="auto", help="auto|cuda|cpu")
    ap.add_argument("--lang", default="en")
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    audio = os.path.abspath(args.audio)
    base = os.path.splitext(audio)[0]

    # Device selection with graceful fallback (cuDNN/cuBLAS can be absent on a fresh GPU venv).
    def load(device, compute):
        return WhisperModel(args.model, device=device, compute_type=compute)

    model = None
    if args.device in ("auto", "cuda"):
        try:
            model = load("cuda", "float16")
            print("[device] cuda float16", file=sys.stderr)
        except Exception as e:
            print(f"[warn] cuda load failed ({str(e)[:120]}); falling back to cpu", file=sys.stderr)
            if args.device == "cuda":
                pass  # explicit cuda requested but failed; still try cpu so the run completes
    if model is None:
        model = load("cpu", "int8")
        print("[device] cpu int8", file=sys.stderr)

    segments, info = model.transcribe(
        audio, language=args.lang, word_timestamps=True,
        vad_filter=False, beam_size=5,
    )

    seg_list, word_list = [], []
    for seg in segments:
        seg_list.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        for w in (seg.words or []):
            word_list.append({"start": w.start, "end": w.end, "word": w.word.strip()})

    with open(base + ".words.tsv", "w", encoding="utf-8") as f:
        for w in word_list:
            f.write(f"{w['start']:.2f}\t{w['end']:.2f}\t{w['word']}\n")
    with open(base + ".segments.tsv", "w", encoding="utf-8") as f:
        for s in seg_list:
            f.write(f"{s['start']:.2f}\t{s['end']:.2f}\t{s['text']}\n")
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for i, s in enumerate(seg_list, 1):
            f.write(f"{i}\n{fmt_ts(s['start'])} --> {fmt_ts(s['end'])}\n{s['text']}\n\n")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump({"language": info.language, "duration": info.duration,
                   "segments": seg_list, "words": word_list}, f, indent=2)

    print(f"[ok] {len(seg_list)} segments, {len(word_list)} words")
    print(f"[ok] wrote: {base}.words.tsv / .segments.tsv / .srt / .json")

if __name__ == "__main__":
    main()
