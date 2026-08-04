#!/usr/bin/env python3
"""
Hearthlight timeline EXPORT — write a Final Cut XML (xmeml v4) that DaVinci Resolve
(or Storyboard Pro) imports to auto-build a watchable timeline: each panel/clip held
for its timed duration on the video track, the VO on the audio track. Drop in, press play.

This is the OTHER half of the round-trip: intake reads timing FROM Storyboard Pro;
export writes timing back out around whatever assets exist now —
  Tier 1: generated/hand panel STILLS (animatic with VO)
  Tier 2: Seedance VIDEO clips (the animated film at your timing)
Same script, different asset paths.

USAGE (WSL):
  python3 build_timeline.py <assets.tsv> <vo.wav> <out.xml> [--fps 24] [--w 1080] [--h 1920]

assets.tsv lines:  duration_seconds<TAB>absolute_path_to_image_or_video
  4.04   /path/01-the-call.png
  2.54   /path/02-window.png
(durations usually come from timing.py shotlist/seedance output)

Caveat: this carries TIMING + ASSETS only. Captions, crew notes, meaning live in the
shot-list/Notion, NOT here — Resolve has no field for them. Two synced layers, not one.
"""
import sys

def sec_to_frames(s, fps): return int(round(float(s) * fps))

def esc(t): return (t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

def build(assets, vo_path, fps, w, h):
    # video clipitems, chained back-to-back
    vclips, t = [], 0
    for i,(dur_s, path) in enumerate(assets, 1):
        df = sec_to_frames(dur_s, fps)
        is_vid = path.lower().endswith(('.mov','.mp4','.m4v'))
        start, end = t, t+df
        vclips.append(f"""
          <clipitem id="panel-{i}">
            <name>panel-{i:02d}</name>
            <duration>{df}</duration>
            <rate><timebase>{fps}</timebase></rate>
            <in>0</in><out>{df}</out>
            <start>{start}</start><end>{end}</end>
            <file id="file-{i}">
              <name>{esc(path.split('/')[-1])}</name>
              <pathurl>file://localhost{esc(path)}</pathurl>
              <rate><timebase>{fps}</timebase></rate>
              <duration>{df}</duration>
              <media><video><duration>{df}</duration>
                <samplecharacteristics><width>{w}</width><height>{h}</height></samplecharacteristics>
              </video></media>
            </file>
            <sourcetrack><mediatype>video</mediatype></sourcetrack>
          </clipitem>""")
        t = end
    total = t
    # one VO audio clip spanning the whole thing
    aclip = f"""
          <clipitem id="vo">
            <name>{esc(vo_path.split('/')[-1])}</name>
            <duration>{total}</duration>
            <rate><timebase>{fps}</timebase></rate>
            <in>0</in><out>{total}</out>
            <start>0</start><end>{total}</end>
            <file id="vo-file">
              <name>{esc(vo_path.split('/')[-1])}</name>
              <pathurl>file://localhost{esc(vo_path)}</pathurl>
              <rate><timebase>{fps}</timebase></rate>
              <duration>{total}</duration>
              <media><audio><samplecharacteristics><samplerate>48000</samplerate><depth>16</depth></samplecharacteristics>
                <channelcount>2</channelcount></audio></media>
            </file>
            <sourcetrack><mediatype>audio</mediatype></sourcetrack>
          </clipitem>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="hearthlight_timeline">
    <name>Hearthlight Timeline</name>
    <duration>{total}</duration>
    <rate><ntsc>FALSE</ntsc><timebase>{fps}</timebase></rate>
    <media>
      <video>
        <format><samplecharacteristics><width>{w}</width><height>{h}</height>
          <rate><timebase>{fps}</timebase></rate></samplecharacteristics></format>
        <track>{''.join(vclips)}
        </track>
      </video>
      <audio>
        <track>{aclip}
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>"""

if __name__ == '__main__':
    args = sys.argv[1:]
    fps, w, h = 24, 1080, 1920
    pos = []
    i = 0
    while i < len(args):
        if args[i]=='--fps': fps=int(args[i+1]); i+=2
        elif args[i]=='--w': w=int(args[i+1]); i+=2
        elif args[i]=='--h': h=int(args[i+1]); i+=2
        else: pos.append(args[i]); i+=1
    if len(pos) < 3:
        print(__doc__); sys.exit(1)
    assets_tsv, vo, out = pos[0], pos[1], pos[2]
    assets = []
    for line in open(assets_tsv):
        line=line.rstrip('\n')
        if not line.strip(): continue
        dur, path = line.split('\t',1)
        assets.append((dur, path))
    xml = build(assets, vo, fps, w, h)
    open(out,'w').write(xml)
    print(f"Wrote {out}: {len(assets)} panels @ {fps}fps, {w}x{h}. Import into DaVinci Resolve and play.")
