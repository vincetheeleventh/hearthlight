#!/usr/bin/env python3
"""
board_intake.py — Hearthlight hand-drawn board → rough shot list.

Takes the four exports of a hand-drawn Storyboard Pro sequence and produces a
panel-level timing+VO table plus a panel→shot (no-cut) grouping. The repeatable
core of "run the system on my hand-drawn board."

INPUTS (per scene):
  --csv      handdrawn_*.csv         Storyboard Pro panel CSV (SceneName,PanelName,Transition,SceneFrames,PanelFrames)
  --words    *.words.tsv             from transcribe.py (start<TAB>end<TAB>word) — the VO alignment authority
  --scene    N                       which SceneName to extract (e.g. 2). Omit = all scenes.
  --fps      24                      frame rate (match the board)

NO-CUT GROUPING (panels → shots), in priority order:
  1. If the CSV encodes cuts via the Scene/Panel hierarchy (each cut = its own Scene,
     no-cut beats = multiple panels in one Scene) -> group by SceneName. [PREFERRED]
  2. Else fall back to --nocuts "6+7,8+9,10+11" (explicit panel-merge list) for boards
     drawn before that convention.

USAGE:
  python board_intake.py --csv board.csv --words vo.words.tsv --scene 2 > rough.md
  python board_intake.py --csv board.csv --words vo.words.tsv --scene 2 \
        --nocuts "6+7,8+9,10+11" > rough.md

Word→panel assignment: each word goes to the panel whose [start,end) window contains the
word's MIDPOINT. The VO column is therefore audio-accurate, not guessed.
"""
import sys, csv, argparse
from collections import defaultdict, OrderedDict

def load_panels(path, fps, scene_filter):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    cum = 0; panels = []
    for r in rows:
        pf = int(r["PanelFrames"]); start = cum; cum += pf
        sc = r["SceneName"]; pn = int(r["PanelName"])
        panels.append({"scene": sc, "panel": pn, "frames": pf,
                       "start_s": start / fps, "end_s": cum / fps,
                       "trans": (r.get("Transition") or "").strip()})
    if scene_filter:
        panels = [p for p in panels if p["scene"] == scene_filter]
    return panels

def load_words(path):
    words = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                words.append((float(parts[0]), float(parts[1]), parts[2]))
    return words

def assign_vo(panels, words):
    def panel_idx(t):
        for i, p in enumerate(panels):
            if p["start_s"] <= t < p["end_s"]:
                return i
        return len(panels) - 1
    byp = defaultdict(list)
    for s, e, w in words:
        byp[panel_idx((s + e) / 2)].append(w)
    for i, p in enumerate(panels):
        p["vo"] = " ".join(byp.get(i, [])).strip()

def group_shots(panels, nocuts):
    """Return list of shots; each shot = list of panel dicts."""
    if nocuts:
        # explicit merges like "6+7,8+9": panel NUMBERS within the scene
        merge = {}
        for grp in nocuts.split(","):
            nums = [int(x) for x in grp.split("+")]
            for n in nums[1:]:
                merge[n] = nums[0]
        shots = OrderedDict()
        for p in panels:
            head = merge.get(p["panel"], p["panel"])
            shots.setdefault(head, []).append(p)
        return list(shots.values())
    # default: if multiple panels share a SceneName, they're one shot (no-cut beats)
    shots = OrderedDict()
    for p in panels:
        shots.setdefault(p["scene"], []).append(p)
    grouped = list(shots.values())
    # If every scene has exactly one panel (single-scene board), each panel is its own shot.
    if len(grouped) == 1 and len(grouped[0]) > 1:
        return [[p] for p in grouped[0]]
    return grouped

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--scene", default=None)
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--nocuts", default=None)
    args = ap.parse_args()

    panels = load_panels(args.csv, args.fps, args.scene)
    words = load_words(args.words)
    assign_vo(panels, words)
    shots = group_shots(panels, args.nocuts)

    def tc(s):
        return f"{int(s//60)}:{s%60:05.2f}"

    print("## Panel-level table  `[CSV timing + STT VO]`\n")
    print("| Panel | VO / Dialogue (real STT) | Dur | Frames | Abs TC |")
    print("|---|---|---|---|---|")
    total_f = 0
    for p in panels:
        total_f += p["frames"]
        vo = p["vo"] or "*(silence)*"
        print(f"| {p['scene']}-{p['panel']:02d} | {vo} | {p['frames']/args.fps:.2f}s | {p['frames']} | {tc(p['start_s'])}–{tc(p['end_s'])} |")
    print(f"\n**Total: {total_f} frames = {total_f/args.fps:.2f}s ({len(panels)} panels → {len(shots)} shots).**\n")

    print("## No-cut grouping (panels → shots)\n")
    print("| Shot | Panels | Combined dur |")
    print("|---|---|---|")
    for i, sh in enumerate(shots, 1):
        names = " + ".join(f"{p['scene']}-{p['panel']:02d}" for p in sh)
        dur = sum(p["frames"] for p in sh) / args.fps
        print(f"| S{i} | {names} | {dur:.2f}s |")

if __name__ == "__main__":
    main()
