---
doc: WF-B
role: workflow
authority: canon
owner: vince
updated: 2026-08-05
status: trial
answers:
  - how a shot goes from storyboard straight to clip, with no per-shot still
  - what the asset sheets must carry for this to work
not_here:
  the alternative route: workflows/WF-A-shot-image-to-video.md
  prompt craft: skills/hearthlight-video-prompts/references/prompt-architecture.md
  performance writing: skills/hearthlight-acting/
---

# WF-B — Storyboard → Video Direct

**Status: ACTIVE — parallel trial**, run against [WF-A](WF-A-shot-image-to-video.md) on the same
shots.

No conditioning still. The board goes to video directly, and identity is held by **key asset
images** — character sheets, location sheets, a style reference — instead of by an approved frame.

**What this buys:** one step from board to motion. No Gate 3, no still to drift.
**What it costs:** the model decides framing, and a weak asset sheet has nowhere to hide. **The
assets carry the entire load.**

---

## The load-bearing rule

> **Assets first. Nothing generates until every character, location and prop is locked and
> stress-tested.**

In WF-A a bad sheet can be papered over by an approved still. Here it cannot. This one rule saves
more re-rolls than everything else in this document combined.

An asset is a pair: **a descriptor (text) + a reference (image)**. The descriptor goes into every
prompt word for word — the model has no memory. The image anchors identity.

### Stress test before locking

Ten generations, different poses, different light. The character must be recognizable **ten out of
ten** — and not alone: next to the other assets, and in the light of the scenes actually coming. A
character that is stable alone often breaks when sharing a frame.

**If the test fails, the problem is the description, not the model.** Rewrite the words, test again.

### Every state is a separate asset

Wet, wounded, changed clothes — separate assets with separate tags and separate descriptors. Mix
states in one text and the model mixes them between shots. Locations are the same: day, night and
rain are three assets, not one with modifiers. Splitting states is cheaper than fighting the model.

Tags are one dictionary across the whole project — the same `@name` in documents, prompts, and the
UI.

### What the sheets must be

**Character sheets** — kept deliberately plain: neutral grey background, flat light, real skin with
visible pores, no retouch. **Do not bake the film look into the sheet.** Grain and cinematic lensing
baked into a sheet travel into every scene and stop the character reacting to new light. The cinema
look lives in the locations and the video prompt.

**Location sheets** — shot in 3/4, never frontal. A frontal sheet becomes flat wallpaper on wides and
the model invents new surroundings past its edges; 3/4 gives depth to read and covers nearly a full
circle of angles. Leave a physical **anchor** in every location — a column, a lamp, a sofa — and tie
staging to it. *"The hero at the lamp, facing the door"* works. *"The hero in the room"* is a
lottery. One light logic per sheet: one source, one shadow direction, never two suns.

> ⚠️ **Hearthlight's current sheets do not yet meet this standard.** `hearthlight-character` produces
> a lighting-neutral turnaround, which is close, and `hearthlight-mise-en-scene` holds the world
> per-location. The state-splitting, the 3/4 rule, the anchor rule and the ten-out-of-ten stress test
> are **not yet in those skills.** Filed as proposals — see `PROPOSALS.md`.

---

## Two variants

### B1 — Board image, plain instruction

The low-effort version, **already proven to work**: hand the model an **image of the storyboard
spreadsheet** — panels with scene descriptions in the cells — and tell it to create what the
storyboard depicts.

- **Inputs:** one image of the board/spreadsheet, plus the asset sheets as references.
- **When:** a sequence of connective shots; getting a whole beat moving quickly; testing whether a
  sequence reads before investing in per-shot control.
- **Strength:** almost no prompt-writing. The board carries the intent visually, which is exactly
  what a board is for.
- **Weakness:** no per-shot control of optics, timing or blocking. What you gain in speed you lose
  in the ability to fix one thing without re-rolling everything.
- **Log it anyway.** Cheap and vague still needs its prompt and verdict in the ledger, or a good
  result cannot be repeated.

### B2 — Per-shot structured prompt

Full control without a still. One structured prompt per shot, conditioned on asset references rather
than a conditioning frame. This is where the prompt architecture earns its keep:
`skills/hearthlight-video-prompts/references/prompt-architecture.md`.

- **Inputs:** the storyboard entry, asset descriptors + references, the locked style block, the
  scene's `GEO SPATIAL LAYOUT`.
- **When:** a shot needs specific optics, timing or blocking, but the frame does not need approving.
- **Strength:** per-beat control, and iteration is surgical — change one line, keep the rest verbatim.
- **Weakness:** prompt-writing effort approaches WF-A without the reassurance of an approved frame.

---

## The route

1. **Lock and stress-test the assets** (above). Blocking step — do not proceed past a failed test.
2. **Write the scene's `GEO SPATIAL LAYOUT`** — a floor plan in a few lines: landmarks, what is
   frame-left and frame-right, where the camera stands, which line it never crosses. **No characters,
   no action — only the place.** Written once per scene, pasted unchanged into every shot of that
   scene. This is the single cure for characters teleporting and swapping places between shots.
3. **Open the scene on a one-second wide.** No lines, no action — the model photographs the
   arrangement and holds it through the following shots. Removing it is why characters swap places.
   Have someone say one short word during it so the model treats it as a discrete shot.
4. **Write the shot** — B1 (board image + instruction) or B2 (structured prompt). Performance comes
   from `hearthlight-acting` either way.
5. **Generate** — `hearthlight-comfyui-graph`. Asset references replace the conditioning still;
   **name the role of every reference** or the model guesses and guesses wrong.
6. **Gate 5 — Vince approves the clip.** There is no Gate 3 on this route; the still review does not
   exist, so the clip review is the only quality gate. Weight it accordingly.

## Cost

**One approval loop per shot.** Cheaper per attempt than WF-A, but attempts can run higher because
framing is not pre-settled — the trial exists to find out whether the saved loop outweighs the extra
re-rolls.

## Known failure modes

- **The model copies the composition of a location reference** instead of reading it as space.
  Location references carry an explicit ban: *do not use as a starting frame, do not inherit the
  composition, the angle or the colour — take only the space and the texture.*
- **Extra people and cloned furniture.** The model adds characters and duplicates props. Every prompt
  opens with an exact character count and closes with positive constraints naming every count.
- **Characters teleport between shots.** The model does not remember the previous shot. Cured by the
  GEO block plus re-naming who stands where after every cut.
- **Identity drifts on wides.** The face is taken from whichever reference is easiest to read. Keep
  a large 3/4 portrait on the sheet as the single clean face source.
- **Complex action in the middle of a beat stalls.** The model shuffles and freezes. Open the prompt
  with the action already underway — *"he is ALREADY mid-swing, the door ALREADY cracking"* — and
  make the approach its own shot.
- **A weak asset sheet fails silently**, then fails in every shot at once. This is the failure mode
  WF-A does not have.

## Where it should win

Coverage and connective tissue. Establishing wides. Shots whose meaning is motion rather than
composition — a fall, a collapse, a fast reveal — where a still of the midpoint teaches the model a
pose instead of a movement. Sequences where speed of iteration matters more than per-frame control.

**Stated before the trial, so the trial can falsify it.**
