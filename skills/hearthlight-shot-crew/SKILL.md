---
name: hearthlight-shot-crew
description: Orchestrate an illustration/stop-motion CREW to design each shot — layout, value-light, background, continuity/model, posing, motion, sound, editor — each contributing in its domain and NEGOTIATING tradeoffs. Routine shots run as an internal checklist; contested shots delegate the conflicting roles to subagents, then the orchestrator reconciles into one coherent shot and shows its tradeoffs. Vince is the director; the kill decision is his.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, shot-list, crew, orchestrator, delegation, illustration]
    category: hearthlight
---

# Hearthlight — Shot Crew (orchestrator)

## The idea
AI illustration gets better when you stop treating the model like a slot machine and treat it
like a **crew** — each expert telling the story in ITS dimension (how layout expresses the beat,
how value carries the emotion, how motion holds the medium), the tensions resolved by a director.
The old filmmaking language is the best prompting interface we have — here in ink-and-watercolour /
stop-motion, not live-action. You are the **orchestrator** (head of department). Vince directs.

Crew roster, mandates, conflicts: **`references/crew-handbook.md`** (read it).

## CRITICAL: crew members are blind unless you brief them on the ARC
A subagent starts with ZERO context — it doesn't know it's shot 23, doesn't know shots 1-22 or
24-end exist. If you brief it with only "compose this shot," it makes a nice frame that BREAKS the
film (a Layout agent that doesn't know the window meant *prison* in shot 4 can't make it *release*
in shot 27). Each crew member must be comprehensive **in its own dimension across the story** — so
you brief it on the arc, not just the frame.

### Scene-windowing (how to brief without flooding)
Segment the film into **scenes** (4-8 shots each with their own pointed mini-arc). Brief each crew
member on:
1. **Its dimension's arc within THIS scene** — e.g. for Layout: how composition evolves across the
   scene and what this shot's framing must do in it.
2. **A short note on where this scene sits in the whole film** — one line ("this is the resolution
   scene; the window framing pays off its setup from the waiting scene").
3. **This shot's slot** in that scene-arc.
A scene window keeps the brief tight (4-8 shots, not 28) while keeping the crew member story-aware.
(McConaughey scenes: the Waiting / the Call (intercut) / the Blessing+Jump.)

### Per-dimension through-lines live in the shot list
The shot list carries, per shot, a **crew-entry block** — one line per crew dimension
(Layout / Value / Background / Continuity / Posing / Motion / Sound). As crew members decide, their
entries accumulate in the shot row. This is the film's MEMORY (the temp-hired subagents have none):
shot 27's Layout agent inherits shot 4's window decision because it's written in the composition track.
The orchestrator maintains these tracks; Vince can see and edit them.

### The handoff to the prompt-writer (the keystone)
The crew does NOT write the final prompt. The crew fills each shot row's per-dimension entries with
*intent*. Then **`hearthlight-video-prompts` reads ALL the crew entries for a shot and compiles them
into one Seedance 2.0 prompt.** Crew thinks per-dimension; prompt-writer assembles. Clean division.

## When to Use
Building or refining a shot list / storyboard panel — "design this shot with the crew,"
"run the crew on the dorm beat," or any shot whose framing/continuity is non-obvious.

## Two modes (this is the hybrid — fast by default, rigorous when it matters)

### Mode A — Routine shot (internal checklist; ONE pass, no delegation)
For straightforward shots, walk the crew lenses yourself in order, writing the shot description as
you go. Fast and cheap. Order: **Continuity/Model → Layout → Posing → Value-Light → Background →
Motion → Sound → Editor check.** (Continuity first so the model/eyeline/geography is fixed before
anyone composes against it.) Output one shot row.

### Mode B — Contested shot (delegate the roles in tension)
When a shot has a real conflict the handbook flags, **delegate the 2-3 roles in conflict** as
subagents (max 3 by default). Each brief MUST carry the scene-arc package (not just the frame):

```
delegate_task(tasks=[
  { "goal": "As the LAYOUT artist, give the composition entry for shot 23: viewpoint, framing,
             staging, and WHAT IT SAYS about the beat. Connect it to the scene's composition arc.",
    "context": "<SCENE ARC: this is the Blessing+Jump scene (shots 26-28), the film's resolution.
                 Composition track so far: shot 4 window=isolation, shot 12 window=resolve. This
                 scene must invert the window to private joy. + the beat + VO + locked style block +
                 location Tier-2 mise-en-scene + 9:16 aspect + Vince's taste. Shot 23's slot: <...>.
                 Subagents know NOTHING else — pass all of this.>",
    "toolsets": ["file"], "max_iterations": 15 },
  { "goal": "As CONTINUITY/MODEL keeper, give the continuity entry: model/silhouette, eyeline,
             screen direction, 180-geometry; flag what would break it.",
    "context": "<same scene package + the PREVIOUS shot's framing/eyeline from the continuity track>",
    "toolsets": ["file"], "max_iterations": 15 },
  { "goal": "As VALUE-LIGHT painter, give the value entry: value structure, where paper stays white,
             warm-cool washes, and how it carries the scene's emotional turn.",
    "context": "<same scene package + the colour-as-emotion arc from the value track>",
    "toolsets": ["file"], "max_iterations": 15 }
])
```
Each subagent returns its **dimension entry**. You (orchestrator): write those entries into the
shot row's crew-entry block, resolve any direct conflict toward story intent → contrast-spine →
Vince's taste, and note the tradeoff. The entries persist in the shot list — they become the input
the prompt-writer compiles. A crew member's entry must always answer *"what does my dimension say
about the story here, and how does it connect to before & after"* — not just "what looks good."

## Delegation mechanics (verified — get these right)
- **Subagents start with ZERO context.** Pass the full shot brief in each `context` — the beat, VO,
  locked style block, the location's Tier-2 mise-en-scene, aspect ratio, the contrast-spine tension,
  and (for continuity) the prior shot's framing. They can't see this conversation.
- **Max 3 concurrent by default.** Pick the 2-3 roles genuinely in tension; don't convene all eight.
- **Subagents can't message Telegram or write memory.** They return a proposal summary; YOU report
  to Vince and write the shot file. Give them `toolsets: ["file"]` (read refs) — they reason, you decide.
- **Synchronous & not durable:** delegation blocks your turn; if Vince interrupts, children die. Keep
  each subagent goal tight (`max_iterations` low, e.g. 15) — they're giving a focused opinion, not researching.
- Don't delegate routine shots (Mode A) — it's slow and pricey for no gain.

## The negotiation rules (so a crew doesn't become a committee)
- Each member proposes ONLY in its domain; it doesn't pre-harmonize with the others (that's the
  orchestrator's job). The friction is the point.
- **Loudest voices** (give their concerns veto weight, because they're where AI illustration breaks):
  **Continuity/Model** (character drift, geography) and the **medium-defenders** (Motion + Value +
  Style — keeping the watercolour from going glossy/photoreal).
- Resolve conflicts toward: the beat's emotional intent → the contrast-spine tension → Vince's taste
  → then aesthetics. Never resolve by averaging into mush; make a *choice* and name it.
- **Argue, then defer.** Present the reconciled shot + the tradeoffs; Vince keeps or overrides. Log
  his overrides to `profile/TASTE.md`.

## Output
Per shot: the shot row (Image&Action / VO / Shot Type / Duration) PLUS, for contested shots, a
one-line **crew note** naming the tension and how you resolved it. Append to the project shot list.

## Pitfalls
- Convening the whole crew for a simple shot (slow, pricey). Mode A by default.
- Forgetting subagents are blind — a thin `context` yields a useless proposal.
- Averaging conflicts into a bland compromise instead of making a directed choice.
- Letting the crew design the *story* (that's locked upstream) — they design the *telling* of an approved beat.
- Filling an open creative slot — those stay Vince's.

## Verification
- Routine shots: one coherent pass, crew order respected (continuity first).
- Contested shots: only the in-tension roles delegated (≤3), each with full standalone context;
  reconciled into one shot with a tradeoff note.
- Continuity/medium concerns given veto weight; conflicts resolved by choice, not average.
- Vince's overrides logged to taste.
