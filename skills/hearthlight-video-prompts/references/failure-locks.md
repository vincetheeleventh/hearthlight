# Failure locks — diagnose before you write, and again before you send

The prompt-director discipline: a silent diagnosis pass before writing, targeted locks only where a
risk is real, and a self-QA pass before output. Adapted for Hearthlight from an outside production
practice, platform-specific references removed.

**The principle throughout:** positive control beats negative control. Write the desired state first;
add the forbidden failure only if the desired state alone has already failed.

---

## The four-D pass

Run silently before writing. Nothing from this pass appears in the final prompt.

### D1 — Deconstruct

Extract **only this shot**. Identify: active characters · active reference tags · active location ·
props · vehicles · creatures · the action · dialogue · duration · aspect ratio · format mode · camera
mode · first visible frame · spatial layout · landmarks · movement path · lighting direction ·
emotional state · audio requirements · forbidden carryover.

Then **remove**: unused characters, unused tags, scene numbers, script headers, previous-scene
wording, old prompt fragments, production notes not meant for the model — and anything not visible or
audible in this exact shot.

> Never include a character, object, location, prop or tag unless it must appear in **this** shot.

### D2 — Diagnose

Before writing, ask what is likely to go wrong. Add a lock **only** where the answer is yes.

- Could the first frame come up empty?
- Could required characters arrive too late?
- Could the model open on a useless establishing shot?
- Could a character appear far from the landmark?
- Could the gaze line reverse?
- Could body orientation be ambiguous?
- Could left and right flip?
- Could the camera choose the wrong side?
- Could the lens drift to a comfortable middle?
- Could the shot go flat front-lit?
- Could the reference be overwritten by too much prose?
- Could a stale tag leak in?
- Could the model add extra characters or duplicates?
- Could a prop end up in the wrong hand?
- Could motion go floaty or physically fake?
- Could dialogue start at the wrong time?
- Could the location reference be used as framing instead of geography?
- Could an internal cut reset continuity?

### D3 — Develop

Build in the order given in `prompt-architecture.md`. **Spatial rules before camera style. Optics
before aesthetic language. Lighting as a priority lock, not decoration.** Never bury placement rules
inside style prose.

### D4 — Deliver

Output the finished prompt only. No QA, no reasoning, no checklist, no explanation, no notes about
how the prompt was written.

---

## Context isolation

**The prompt is a sealed current-shot document.** The model has no memory, and anything referring
outward is noise it will try to resolve.

Forbidden unless genuinely part of this shot:

scene numbers · episode labels · script headers · previous-scene summaries · unused character tags ·
unused location tags · characters mentioned only in prior dialogue · unseen props from older shots

And these phrases, always: *previously · again · same as before · continues · from last shot · as
above · "the other character"* without naming who.

---

## Negative constraints — used sparingly, placed locally

**Do not emit a standing NEGATIVE CONSTRAINTS block by default.** Use negatives only for likely
failure modes, and place each one next to the positive rule it protects.

Prefer:

```text
Faces remain in deep shadow; no flat front light.
```

Over:

```text
NEGATIVE CONSTRAINTS
No flat front lighting.
No beauty fill.
No studio key.
```

Giant generic negative lists are noise unless the shot has repeated, known failures.

**Negatives worth writing when the risk is real:** no duplicate characters · no extra people unless
specified · no unused tags · no empty first frame · no wrong gaze direction · no character facing away
from the intended subject · no character far from the landmark · no flat front lighting · no CG gloss ·
no game-engine look · no floating motion · no subtitles · no music unless requested.

**Always write the desired state first**, then the forbidden failure if it is still needed. If no
negative lock is necessary, omit negatives entirely.

> Hearthlight's own convention pushes further: the closing block is **POSITIVE CONSTRAINTS**, where
> every count and ban is phrased as what *is* in the frame. See `prompt-architecture.md`.

---

## Safe language

**Direct visual verbs:** stands · faces · looks · holds · walks · raises · touches · leans · breathes ·
drips · falls · slides · presses · turns · opens · closes · enters · reclines.

**Measurable language:** within 1 meter · screen-left · screen-right · foreground · midground ·
background · at hip height · at eye level · 47° diagonal field of view · 0:03 · one step · two
characters · three visible people.

**Avoid:** over-complex nested clauses; vague psychology that never becomes visible behaviour.

### Ban dictionary

Words the model punishes, and their substitutes. **Add to this as you find them** — it is a living
list, and the additions are worth more than the starting entries.

| Instead of | Write |
|---|---|
| dark | low key |
| jolting | rapid motion |
| *(add yours)* | |

---

## Quality suffix

Optional, only where it does not conflict with a deliberate choice:

```text
sharp clarity, natural colors, stable picture, no blur, no ghosting, no flickering.
```

**Not a substitute** for real camera, lighting or physics control. A prompt leaning on this instead
of on optics and physics has skipped the work.

---

## Silent self-QA before sending

Answer every one. If any answer is no, fix the prompt before sending.

- [ ] Are all active tags actually used in this shot?
- [ ] Are all stale tags removed?
- [ ] Is the first frame correct, and not empty?
- [ ] Are required characters visible immediately where needed?
- [ ] Is every character's position clear?
- [ ] Is every important gaze line clear?
- [ ] Is every body orientation clear?
- [ ] Is landmark proximity physically anchored?
- [ ] Is the camera side stated, and the line it never crosses?
- [ ] Is the lens character chosen by content type?
- [ ] Is the lens described by visual outcome, not metadata?
- [ ] Is the lens protected from drift?
- [ ] Is the lighting protected from going flat?
- [ ] Are props in the correct hands?
- [ ] Are the actions physically possible?
- [ ] Are the timing blocks internally consistent?
- [ ] Is dialogue clean — only the scripted line, everyone else silent?
- [ ] No scene numbers, no context leakage?
- [ ] Style block verbatim; aspect from `project.json`; duration from the current shot record?
- [ ] Is the QA itself absent from the output?
