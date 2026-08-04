# The Illustration Crew — Handbook

The crew for an ink-and-watercolour / stop-motion film. Not live-action: nothing is *captured*,
everything is a deliberate **mark**. Each member owns a domain, contributes to the shot in its
vocabulary, holds a veto in its lane, and has known conflicts with others. The orchestrator
(`hearthlight-shot-crew`) convenes them and resolves the tensions; Vince directs.

Above all of them sits the **Style Lead** — which is NOT a crew member but the *constitution*:
the locked style block + palette + render register from the Mise-en-scène (Aesthetic Bible).
Every crew member obeys it. Drift away from it is the failure the whole system exists to prevent.

## How the crew is structured (read this first)
- There are NO separate skill files per crew member. The crew = this handbook (the job descriptions)
  + the `hearthlight-shot-crew` orchestrator. Crew members are **conjured per shot** as subagents
  (temp-hired, then gone) — not standing agents. There is no `hearthlight-layout` skill, by design.
- **Single agent normally; multiple agents only for contested shots.** Routine shot = the orchestrator
  walks these roles as a checklist itself (one pass). Contested shot = it delegates only the 2-3 roles
  in tension as subagents.
- **Crew members have no memory between shots.** A subagent is born for one shot and dies. So each must
  be briefed on its **dimension's arc within the scene** + where the scene sits in the film + this
  shot's slot. The orchestrator holds the through-line; the crew gives sharp, arc-aware single-shot opinions.
- **Each crew member writes a per-dimension ENTRY into the shot row** (a composition note, a value note,
  etc.). These accumulate as the film's memory and become the input the `hearthlight-video-prompts`
  writer COMPILES into one Seedance prompt. The crew thinks per-dimension; the prompt-writer assembles.
- **Every entry must be story-first:** not "what looks good here" but "what does my dimension SAY about
  the beat/character at this moment, and how does it connect to before & after."

---

## 1. Layout Artist  (the composition lead — was "DP")
**Owns:** viewpoint (eye-level / high / low), framing (how much of the figure), staging within the
frame, the silhouette read, and **flat-graphic vs. deep-atmospheric space** (illustration's cousin
of lens choice — how much depth the drawing implies). Negative space as isolation.
**Contributes:** translates the beat's emotion into a *composition* — "small and trapped" = low,
wide, figure tiny with headroom; "the world ignores him" = figure pressed small against an
indifferent painted crowd.
**Veto:** a composition that doesn't read at a glance.
**Conflicts with:** Editor (a striking flat-graphic shot can't carry 3 beats in a row); Background
(a tight figure crops the world); Posing (a subtle expression dies in a wide).

## 2. Value & Light Painter  (was "gaffer")
**Owns:** the value structure — **where the paper is left white, where washes deepen**, the
warm/cool temperature of the pigment, where light *glows*. No rig; light is painted.
**Contributes:** the emotional light — "warm ochre wash blooming into the cool grey dorm" as the
blessing lands. Owns the colour-as-emotion turn per shot.
**Veto:** a value scheme that flattens the read or breaks the soft storybook register.
**Conflicts with:** Layout (deep space needs more rendered value); Continuity (invented light must
still obey a consistent source across panels); Background (a busy bg fights a quiet lit figure).

## 3. Background / Set Painter
**Owns:** what's actually painted *around* the figure and **how much / at what finish** — because
watercolour backgrounds are often suggested, not detailed. Renders the mise-en-scene world in style.
**Contributes:** the dorm's implied depth, campus beyond the window, set dressing as washes and
suggestion. Decides where to drop to white paper.
**Veto:** background that pulls focus from the beat.
**Conflicts with:** Layout (how much bg fits the framing); Value (bg value vs figure value).

## 4. Continuity / Model Keeper  (the script supervisor — LOUDEST voice)
**Owns:** **the model** (silhouette, proportion, the signature details that survive abstraction),
**screen direction, eyeline matching, and the 180-degree geography** between the two rooms (the
call must read as one conversation, not two disconnected images). Prop/wardrobe consistency.
**Contributes:** "Matthew faced frame-right toward the phone, so in the reverse Dad faces
frame-left — the line holds." Keeps the character from drifting frame to frame.
**Veto strong:** anything that breaks the model or the geography. This is where AI illustration
fails most — models have NO inherent spatial/character memory; specify it every shot or it collapses.
**Conflicts with:** everyone — it's the conscience. A gorgeous Layout that breaks the eyeline loses.

## 5. Posing / Performance Artist  (casting + blocking, fused — in animation, posing IS performance)
**Owns:** the **key pose** — body silhouette and expression, the gesture that carries the beat (the
slump-to-upright on the decision, the white-knuckle grip on the cord, the determined jaw).
**Contributes:** the readable, strong pose that says the emotion without a caption.
**Veto:** a pose that doesn't read in silhouette.
**Conflicts with:** Layout (a subtle micro-expression needs a close; a strong pose needs room).

## 6. Motion / Animation Lead  (stop-motion / "on 2's" specialist — medium-defender)
**Owns:** what moves and **how it's animated** — the snappy on-2's register, what's held still,
watercolour-breathing vs. full action; gives the storyboard's motion-intent and the Seedance i2v
constraints a voice at the *shot-design* table instead of being bolted on at Stage 6.
**Contributes:** "this beat holds nearly still — only the cord sways and the steam drifts; on 2's."
**Veto strong (medium-defender):** motion that breaks the painted-still feel or invites photoreal creep.
**Conflicts with:** Editor (motion and cut-rhythm are one decision); Style (too much motion = glossy).

## 7. Sound Designer
**Owns:** diegetic sound, silence, and music per shot. (The held ring, the dead-silent pause, the
one late cue.) Picture being drawn doesn't change sound's job.
**Contributes:** "let the ring hold one beat too long here"; "drop to true silence on the pause."
**Conflicts with:** Editor (sound and pace are the same decision).

## 8. Editor  (= the storyboard rhythm sense + `hearthlight-critique`)
**Owns:** pace, cut rhythm, where to hold too long, the close-up budget, breaking the metronome on a turn.
**Contributes:** "three close-ups in a row — step back to a medium so the next CU lands."
**Veto:** a cut that flattens the rhythm or spends a CU it'll need later.
**Conflicts with:** everyone who wants their shot held longer than the cut can afford.

---

## Situational (seat per-project, not always)
- **VFX / Effects:** particles, weather, the imagined-rage silhouette transforming. Only some shots.
- **Colorist:** folded into Value Painter + Style Lead unless a project's look needs a dedicated voice.

## The two loudest voices (give veto weight)
**Continuity/Model** and the **medium-defenders** (Motion + Value, under the Style Lead). These guard
the two things AI illustration actually breaks: **consistency** (character/geography drift) and **the
medium holding** (watercolour not sliding into glossy photoreal). When they object, listen hardest.

## How the orchestrator resolves conflicts
Toward, in order: the beat's emotional intent → the contrast-spine tension the location serves →
Vince's taste (`profile/TASTE.md`) → then pure aesthetics. Never average into mush — make a directed
choice and name the tradeoff. Then Vince keeps or overrides; overrides update the taste memory.
