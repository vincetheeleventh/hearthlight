#!/usr/bin/env python3
"""
Hearthlight timing — parse a Storyboard Pro Final Cut XML (xmeml v4) export
that has ONE clipitem PER PANEL, and emit per-panel timing the pipeline consumes.

Verified against dont_halfass_it-4e182fb4.xml (24fps, 270x480 / 9:16):
  panel -2-1: 97 frames -> 4.04s ; -2-8: 27 -> 1.13s ; etc.

USAGE (WSL):
  python3 timing.py parse  <export.xml>                 # print the timing table
  python3 timing.py shotlist <export.xml> > timing.md   # markdown table for the shot list
  python3 timing.py moments  <export.xml> > moments.tsv  # for hearthlight-clip-extractor
  python3 timing.py seedance <export.xml>               # per-panel Seedance duration targets

Notes:
- Clips are named generically (dont_halfass_it-2-N); join to panels/shots by ORDER (N).
- Audio clips (the VO) are parsed separately so timing can also drive audio cuts.
"""
import sys, re, xml.etree.ElementTree as ET

# Seedance allowed durations (COMBO) — VERIFY against the actual node; edit if different.
SEEDANCE_ALLOWED = [5, 10, 14]

def frames_to_sec(frames, fps):
    return round(frames / fps, 3)

def get_fps(seq):
    tb = seq.find('.//rate/timebase')
    return float(tb.text) if tb is not None else 24.0

def parse(path):
    tree = ET.parse(path)
    root = tree.getroot()
    seq = root.find('.//sequence')
    fps = get_fps(seq)
    out = {'fps': fps, 'video': [], 'audio': []}
    # video track clips = the panels, in timeline order (by <start>)
    for track_kind, bucket in (('video','video'), ('audio','audio')):
        track = seq.find(f'.//media/{track_kind}')
        if track is None: continue
        for clip in track.findall('.//clipitem'):
            name = clip.findtext('name','')
            start = int(clip.findtext('start','0'))
            end   = int(clip.findtext('end','0'))
            dur   = int(clip.findtext('duration','0'))
            fnode = clip.find('file/name')
            fname = fnode.text if fnode is not None else ''
            out[bucket].append({
                'name': name, 'file': fname,
                'start_f': start, 'end_f': end, 'dur_f': dur,
                'start_s': frames_to_sec(start, fps),
                'end_s':   frames_to_sec(end, fps),
                'dur_s':   frames_to_sec(dur, fps),
            })
    out['video'].sort(key=lambda c: c['start_f'])
    out['audio'].sort(key=lambda c: c['start_f'])
    return out

def nearest_seedance(dur_s):
    # generate AT LEAST the panel duration (round up to nearest allowed), trim in edit
    for a in SEEDANCE_ALLOWED:
        if a >= dur_s: return a
    return SEEDANCE_ALLOWED[-1]

def cmd_parse(d):
    print(f"fps={d['fps']}  video panels={len(d['video'])}  audio clips={len(d['audio'])}")
    print(f"{'#':>3} {'start':>8} {'dur(f)':>7} {'dur(s)':>7}  name")
    for i,c in enumerate(d['video'],1):
        print(f"{i:>3} {c['start_s']:>8.2f} {c['dur_f']:>7} {c['dur_s']:>7.2f}  {c['name']}")
    total = d['video'][-1]['end_s'] if d['video'] else 0
    print(f"total video timeline: {total:.2f}s")

def cmd_shotlist(d):
    print("| panel | start (s) | duration (s) | source-name |")
    print("|-------|-----------|--------------|-------------|")
    for i,c in enumerate(d['video'],1):
        print(f"| {i:02d} | {c['start_s']:.2f} | {c['dur_s']:.2f} | {c['name']} |")

def cmd_moments(d):
    # NN<TAB>start<TAB>end<TAB>slug  (for hearthlight-clip-extractor)
    for i,c in enumerate(d['video'],1):
        slug = re.sub(r'[^a-z0-9]+','-', c['name'].lower()).strip('-') or f"panel-{i:02d}"
        print(f"{i:02d}\t{c['start_s']:.2f}\t{c['end_s']:.2f}\t{slug}")

def cmd_seedance(d):
    print(f"{'#':>3} {'board(s)':>9} {'generate':>9}  (trim to board in edit)")
    for i,c in enumerate(d['video'],1):
        gen = nearest_seedance(c['dur_s'])
        print(f"{i:>3} {c['dur_s']:>9.2f} {gen:>9}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, path = sys.argv[1], sys.argv[2]
    d = parse(path)
    {'parse':cmd_parse,'shotlist':cmd_shotlist,'moments':cmd_moments,'seedance':cmd_seedance}[cmd](d)
