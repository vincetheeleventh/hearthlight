# Video prompt architecture — the structured skeleton

Adapted for Hearthlight from an outside production practice, stripped of platform-specific and
proprietary references. Written against Seedance 2.0; the craft is model-agnostic.

**Use this when** a shot needs per-beat control: board2video variant B2, or any shot2video shot where the clip
keeps missing. **Do not use it** for board2video variant B1 (board image + plain instruction) — that
variant's whole value is skipping this.

Every rule here exists because a shot failed without it.

---

## The skeleton

Sections in this order. Omit any the generation UI already controls; do not omit the spatial ones.

```
SCENE CONTEXT          — EXACT N CHARACTERS — NO DUPLICATES; what happens; duration
ACTIVE REFERENCES      — asset tags with the role of each named
LOCATION MAP           — the geography of the place, in words
FIRST FRAME AND SPATIAL BLOCKING — who stands where in frame one
FORMAT MODE            — one take or hard cuts; duration; real time
OPTICS                 — field of view and focus plan
CAMERA                 — how it behaves, and what it never does
ACTION TIMING          — beat by beat, in seconds
PHYSICS                — weight, contact, inertia
LIGHTING               — one source logic, and its direction
AUDIO                  — voice descriptors, exact lines, SFX
CHARACTER ACTING       — from hearthlight-acting
STYLE                  — the locked style block, verbatim
QUALITY                — detail and stability requirements
POSITIVE CONSTRAINTS   — every count and ban, written as what IS in frame
```

**Ordering is load-bearing.** Spatial rules come before camera style; optics before aesthetic
language. Never bury placement rules inside style prose — the model weights what it reads first.

---

## Writing rules

- **Present tense. Short sentences.**
- **The camera is written inside the action**, not as a separate wish.
- **Up to three sentences per beat.** Overload a beat and the model smears it.
- **Length depends on the route, and the two are opposite.**
  - **board2video (no conditioning still):** the prompt is the only source of framing, blocking and world.
    Long is correct — the source practice ran 3,000–4,000 words. Length is not the enemy here; an
    overloaded beat is.
  - **shot2video (i2v from an approved still):** **short.** The still already carries composition,
    character, palette and style. Re-describing them invites the model to repaint the frame — see
    the parent skill's i2v section. A 3,000-word prompt on an i2v job is that invitation.
    Describe **only what changes**: the motion, its quality and pace, and what stays still.
- **Positive form only.** The model ignores "does NOT fall on his back", or does the opposite. Write
  "falls on his stomach". This applies to every constraint — hence *positive* constraints.
- **The character is in frame from frame one**, and never looks into the camera unless asked.
- **Never write age, in any language.** Content filters tighten sharply on any reading of a minor.
  Give role, clothing and action instead.
- **Keep a ban dictionary** of words the model punishes, and substitute: `dark` → `low key`,
  `jolting` → `rapid motion`. Add to it as you find them.
- **Density where control matters.** Identity anchors, blocking, first frame, gaze, hand and prop
  states, timing, optics, lighting, physics, dialogue — dense. Generic beauty, non-critical costume,
  background extras — sparse. Improvement comes from stronger signal, not more words.

## The character count header

Not a formality. Models add extra people and clone furniture.

```
EXACT 3 CHARACTERS — NO DUPLICATES: ROCO, JAX, REIN.
```

Only those whose references are in the prompt exist in the frame. Furniture and props get direct
bans: *"exactly ONE mannequin, NEVER render a second one."*

## Naming reference roles

References are assets only — characters and locations. **Name the role of each one in the prompt**,
or the model decides for itself and decides wrong: it copies composition instead of face, or face
instead of palette.

```
@roco for character reference
@loc_cave_front for location reference
```

**Location references carry a standing ban:**

> *do not use as a starting frame, do not inherit the composition, the angle or the colour — take
> only the space and the texture.*

Reference hierarchy: identity references control face, body, proportions, costume, unique anchors.
Location references control architecture, materials, geography, atmosphere, landmarks. Prop
references control shape, scale, material, hand contact, state. **A style reference never overrides
identity, blocking, action, optics or lighting.**

## GEO SPATIAL LAYOUT — the cure for teleporting

The most expensive early failure: characters swap places, the camera jumps to the wrong side. The
cause is simple — **the model does not remember the previous shot.**

Write a floor plan once per scene and paste it unchanged into every shot of that scene. Landmarks
only. **No characters, no action.**

```
GEO SPATIAL LAYOUT (locked across every shot — pure spatial map):
— PLATFORM = raised circular ritual stone disc at the edge of a cliff.
— ALTAR-MONOLITH: at the cliff edge, MID-RIGHT relative to the platform.
— RITUAL CENTER: CENTER-LEFT, ~3 m from the altar.
— 180° AXIS: camera ALWAYS stays on the corpse-field side — it NEVER crosses the line.
— BACK-LIGHTING: crimson horizon glow from BEHIND the platform, rim-lighting silhouettes.
```

- **Sides exist only from the camera.** "Frame-left" and "frame-right". The model does not understand
  "to the left of the hero".
- **Position from landmarks, in metres.** "At the altar", "three metres away".
- **State which side the camera stands on and which line it never crosses.**
- **After every cut, name again who stands where and where they look.**
- **Give a static dialogue a corner, not a room.** Less space means less choice about where to put
  people.

GEO is only the map. The *look* still comes from the location asset's descriptor and reference.

## The one-second opening wide

Start the scene with one second of wide, no lines and no action. The model photographs the
arrangement — who is where, what lies where, where light comes from — and holds it through the
following shots. Remove it and characters start swapping places.

Have someone say one short word ("hm") during that second so the model treats it as a discrete shot.

**The wide need not be silent.** If the shot answers the previous one, feed the tail of the previous
clip's line into that first second — the actor answers the right thing in the right tone, and the two
clips glue at the seam.

Cost: one second of runtime. Saving: hours of reshoots.

## Framing — how much world is in the frame

**A drawn frame has no lens.** No bokeh, no focus plane, no sensor, no shutter. What survives from
photographic craft is the one thing that is really about composition: **how much of the world the
frame contains, and how close the viewer stands.**

Say that directly, in the film's own terms:

| Instead of | Write |
|---|---|
| 8° super-telephoto | the figure small and far, seen past something in the foreground |
| 18° telephoto close-up | tight on the face, the background reduced to a flat wash |
| 29° portrait | head and shoulders, little room around them |
| 47° normal | a natural distance — roughly what a person standing there would see |
| 84° wide | the figure with the room around them, readable to the frame edges |
| 107° very wide | the space dominant, the figure small within it |

**Never write:** millimetres · f-stops · ISO · lens names · bokeh · depth of field · chromatic
aberration · shutter or motion blur · "cinematic lens". These describe a camera the film does not
have, and asking for them is an instruction to abandon the medium.

### The illustrated register — say what the medium *is*

Banning photographic vocabulary leaves a hole. Fill it with the language of animation, which controls
the same thing — how motion reads — in terms the medium actually has.

From Vince's working `yugioh` Shot 1 prompt, which is the model for this:

```
Animation on 2s with noticeable line boil
```

Two terms, and they do more work than a paragraph of camera talk.

| Term | What it controls |
|---|---|
| **on 2s** (or 1s, 3s) | The animation cadence — how many frames each drawing is held. On 2s is the classic hand-drawn feel; on 1s is fluid and expensive-looking; on 3s is limited and deliberate |
| **line boil** | The characteristic wobble of redrawn linework. **The single strongest anti-photoreal signal available** — a boiling line cannot read as a photograph |
| **held cel / limited animation** | Only part of the frame moves; the rest is a held drawing |
| **paper texture constant** | The ground stays paper, not film |
| **wash edges / ink bleed** | How the colour meets the line |

**Reach for these before reaching for camera language.** *"Animation on 2s with noticeable line
boil"* defends the medium harder than any negative constraint, because it tells the model what to
make instead of only what to avoid — and positive control beats negative control everywhere else in
this file too.

**Keep one framing register per beat.** Tight face, wide geography and a macro detail in the same
beat will smear. If the scene needs all three, cut, and give each shot its own register.

> Live-action projects (`medium: live-action`) use the full photographic vocabulary instead —
> `references/live-action/optics-language-bank.md`. Do not open that folder for an illustrated film.

## Physics

Write weight, contact and inertia for everything that moves. Mass drags; momentum decays; carried
liquid tilts and steadies. Breath is audible work, not decoration. Without this, motion goes floaty
and the shot reads fake even when every frame is correct.

## Audio

Diegetic only. **"SFX only. No music."** is mandatory — music belongs to post-production, and a
generated soundtrack only obstructs the edit. Dialogue rules live in `hearthlight-acting`.

## Positive constraints — the closing block

Every count and every ban, written as **what IS in the frame**.

```
POSITIVE CONSTRAINTS
Exactly three people in the hall, and no one else. Exactly ONE crystal arm, on ROCO's right arm,
wrist to shoulder — never on the left, never spreading past the shoulder. FIVE smashed mannequins,
never re-rendered as intact, never multiplied. Two trays, never more. The camera stays on the door
side of the room for all twelve seconds.
```

Close with the technical tags:

```text
NON-IP. [aspect]. [duration]s. SFX only.
```

Then the medium's own preservation clause, verbatim from the parent skill — for an illustrated film
that is what holds the look through the motion.

> The source practice closed with `Photoreal. NO CGI. Cinematic.` **None of that belongs on an
> illustrated film**; `Photoreal.` in particular is the fastest single route to losing the medium.
> Those tags live with the live-action material.

**Aspect comes from `project.json`.** It is a composition law, not an export setting.

## Style block

The project's locked style block from `03-bible/mise-en-scene.md`, pasted **word for word**. Never
paraphrased, never summarized, never "improved" for the shot. Drift from it is the failure the whole
bible exists to prevent.

## Scale anchors

Anything much larger or smaller than human needs a size comparison in **every** prompt, plus a human
figure in frame to measure against. Without both, the model quietly shrinks a giant back toward human
height.

```
THE SCALE LAW — VISIBLE PROOF IN THE PICTURE: the stone guardian stands THIRTY METRES tall — his head
is lost in the darkness of the dome, his open palm is as wide as a family car, and ROCO at his foot
reaches just above the ankle. In every frame the guardian's silhouette is at least FIVE TIMES the
height of the human figure beside him, and the frame cannot hold both his feet and his head at once.
A guardian that reads as a large man = failed shot.
```

## Hard-won specifics

- **Complex action never sits in the middle of the timing.** A door that will not break means the
  action was buried. Open the prompt with it already underway — *"he is ALREADY mid-swing, the door
  ALREADY cracking"* — and make the approach a separate shot.
- **A crowd is one asset** with a range of heights and clothes; one or two lead extras get their own
  assets for close-ups. On medium shots state the number directly — "20+" — or you get three people
  in one take and a hundred in the next.
- **Transitions between two spaces hold on a threshold.** Both location assets in one prompt, with
  the seam a doorway carrying a light contrast: *"a warm amber room, a cold blue corridor beyond the
  arch."* The contrast explains the palette change and forgives small geometry errors.

## Iteration discipline

- **Change one thing at a time.** A prompt is a working mechanism — rewrite it whole and you lose the
  parts that worked. One line per iteration, everything else verbatim.
- **Log every iteration:** prompt version, what changed, verdict. Without the log a good shot cannot
  be repeated. This is the shot-runner's ledger.
- **Ten-to-fifteen rule.** If a shot has not come together in that many iterations, the problem is
  not the wording. **Simplify the shot** — split it in two, remove an action, change the angle.
- **Never re-run an approved image through a model to "clean it up."** That law lives in
  `hearthlight-image-prompts` § THE NO-DOUBLE-PASS LAW — amend by mask, never by regeneration.

## Pre-send self-check

- [ ] Exact character count in the header; no character present without a reference
- [ ] Every reference's role named; location reference carries the inheritance ban
- [ ] GEO block pasted unchanged from the scene
- [ ] First frame states who stands where and where they look
- [ ] Every constraint in positive form
- [ ] One lens character for the beat; content matches the FOV
- [ ] One light source logic; no second sun
- [ ] Style block verbatim
- [ ] Aspect matches `project.json`; duration matches the current shot record
- [ ] No age written anywhere
- [ ] Beats carry at most three sentences each
