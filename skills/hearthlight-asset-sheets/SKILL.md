---
name: hearthlight-asset-sheets
description: >
  The asset factory — how a character, location or prop sheet is actually manufactured and validated
  so it holds identity across every generated shot. Owns the production craft common to all asset
  types: sheet composition, the no-double-pass law, point-change masking, state splitting, the tag
  dictionary, and the ten-out-of-ten stress test that gates a sheet before any shot is generated.
  Use before any generation batch, when a sheet is being built or amended, or when a character or
  location drifts between shots. Blocking prerequisite for WF-B.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, assets, sheets, character, location, prop, consistency, stress-test]
    category: hearthlight
---

# Hearthlight — Asset Sheets

Adapted for Hearthlight from an outside production practice, platform-specific and proprietary
references removed. Every rule here exists because a shot failed without it.

## What this owns, and what it does not

| This skill | Owns |
|---|---|
| **`hearthlight-asset-sheets`** | The sheet as a **manufactured artifact** — composition, generation technique, amendment, validation. Uniform across characters, locations and props. |
| `hearthlight-character` | **Who the character is** — meaning-first interrogation, `CHARACTER.md`, `character.json`, the signature string, the reject-list, the lighting-neutral law. |
| `hearthlight-mise-en-scene` | **What the world looks like** — the locked style block, the composed world per location. |

Identity and meaning come from those. **This skill turns them into a sheet the model can actually
hold.** Where they disagree, they own the *what*; this owns the *how*.

---

## The load-bearing rule

> **Assets first. Not one shot generates until every character, location and prop is locked and
> stress-tested.**

This single rule saves more re-rolls than everything else combined. It is absolute for
[WF-B](../../workflows/WF-B-storyboard-to-video.md), which has no conditioning still to hide a weak
sheet behind — there, the sheets carry the entire load. It matters for WF-A too: the character sheet
is `image2` on every video job, so anything baked into it is inherited by every clip.

## An asset is a pair

**A descriptor (text) + a reference (image).**

The descriptor goes into every prompt **word for word**. The model has no memory; there is no such
thing as "as established earlier". The image anchors identity.

Neither works alone. A perfect image with a vague descriptor drifts; a precise descriptor with a
muddy image drifts differently.

---

## Universal laws

### 1. An image never runs through a model twice in full

Every full pass destroys texture and drifts colour. After two passes a face turns symmetrical,
plastic and lifeless — and **dead texture ruins the acting downstream**, because a plastic face
cannot carry a performance no matter how good the video prompt is.

**Amendments are made by masking, never by regeneration.** To add a jacket, a scar, blood:

1. Generate the point change on a **copy** of the approved sheet.
2. Composite **only the changed region** back onto the original, by hand, with a mask, in any editor.
3. Everything outside the mask is the untouched original. The original skin texture survives.

### 2. Keep the sheet boring on purpose

Neutral grey ground. Flat, even light. Real skin with visible pores, no retouch. **No film look.**

Bake grain, cinematic lensing, a hard backlight or a coloured shadow into a sheet and the character
carries it into every scene and **stops reacting to new light** — the per-scene lighting design
becomes unenforceable. The cinema look lives in the locations and the shot prompt.

> This is `hearthlight-character`'s lighting-neutral law, and it generalizes to every asset type.

### 3. Every state is a separate asset

Wet, wounded, changed clothes — separate assets, separate tags, separate descriptors:
`@roco`, `@roco_wet`, `@roco_blood`. Locations too: **day, night and rain are three assets**, not one
with modifiers.

Mix states inside one descriptor and the model mixes them between shots. **Splitting states is
cheaper than fighting the model.**

### 4. One tag dictionary for the whole project

The same `@name` in documents, prompts, the shot list and the UI. A second name for the same asset is
a drift vector. Tags live with the reference manifest (`hearthlight-conventions`).

### 5. Pick believable over beautiful

A creative model returns several faces from one prompt. **Choose the most believable, not the most
beautiful.** A beautiful-but-slightly-fake face passes a still review and shows its fakeness later in
video — when it is far too late and far more expensive to fix.

**Always check the eyes.** Even dark eyes need a small light reflection in the pupil — a catch-light.
Without it the face reads dead, and **no video model can act with a dead face.** This is a hard
rejection criterion, not a preference.

---

## Character sheets

### Composition

- **A large portrait in 3/4 view** — the face turned slightly, never straight-on. This is the single
  clean face source, and it is what models read best.
- **Full body, front — with no head.**
- **Full body, back.**

### Why the front figure has no head

It sounds insane. It fixes a whole class of broken shots.

On wide shots the model kept taking the face from the **small full-body figure**, where the face is
tiny and blurry — and the resulting wide had a smeared, subtly wrong face. Remove that head and the
model has exactly one place to take a face from: the large 3/4 portrait.

> ⚠️ **This refines `hearthlight-character` § THE TURNAROUND SHEET → Contents**, which currently
> specifies "three full-body views — front, side, three-quarter". That layout re-introduces the exact
> problem: three small faces competing with each other and none of them clean. **Amending that skill
> is AMBER** — see `PROPOSALS.md`. Until Vince rules, `hearthlight-character` governs; this section
> is the argued alternative, not an override.

Everything else from `hearthlight-character`'s Contents still holds: feet visible, expression studies
drawn from what the Beat Sheet needs, a hands inset where the project is hands-forward, **no text or
labels anywhere** (models hallucinate type onto sheets and it poisons `image2`).

### Voice and behaviour are locked here too

A character is not ready until its **voice descriptor** and **acting master profile** are locked
alongside the sheet — see `hearthlight-acting`. A sheet that looks perfect and acts like a mannequin
has failed the only test that matters.

---

## Location sheets

Locations are generated **for the camera angles you will actually need**, not as pretty pictures.

- **Shoot in 3/4, never frontal.** A frontal sheet becomes flat wallpaper on wides, and past its
  edges the model invents new surroundings every time. A 3/4 view gives depth to read and covers
  nearly a full circle of angles.
- **Leave an anchor** — a column, a lamp, a sofa — and tie all staging to it. *"The hero at the lamp,
  facing the door"* works. *"The hero in the room"* is a lottery.
- **One light logic per sheet.** One source, one shadow direction. **Never two suns** — or every new
  angle re-invents the lighting.

### Reverse angles

**Method A — generate the corner.** Generate a corner of the same room in an image model, matching
the soft focus and grade of the original sheet.

**Method B — walk the empty room.** Generate a *video* of the empty location with the camera slowly
walking through the space. A video model draws the other sides consistently with your sheet.
Screenshot the angle you need, take it to an image model, and prompt it to improve texture and
lighting. **A full location sheet out of a single image.**

Method B is the stronger of the two and the less obvious. It is also the one that makes a
single-image location viable for WF-B.

---

## Prop sheets

Props split by state like everything else — but the split is driven by **how the prop is shot**:

| Version | For |
|---|---|
| **Full** | Close-ups where the object is the subject |
| **Partial / altered** | A brief reveal — smaller, damaged, bloodied, in a palm |
| **Hidden** | Shots where it must be present but unseen |

A "hidden" version carries its own constraint in the prompt — the object is forbidden from view and
only its effect is allowed. *"The crystal is not visible; only blue light between the clenched
fingers."* Writing the constraint into the asset means it cannot be forgotten per shot.

---

## The stress test — the gate

**No asset is locked until it passes. No shot generates from an unlocked asset.**

1. **Ten generations**, varied poses and varied light.
2. **Recognizable in ten out of ten.** Not eight. Not "mostly".
3. **Not alone** — beside the other assets it will share frames with. A character that is stable
   alone often breaks when sharing a frame with someone.
4. **In the light of the scenes actually coming.** A sheet that holds in flat light and collapses
   under the film's key light has not been tested.

**If the test fails, the problem is the description, not the model.** Rewrite the words and test
again. Re-rolling the same descriptor is how a bad asset gets locked in.

Record the outcome — `10/10`, `7/10 — jaw drifts in profile` — beside the asset. A failed test is
evidence about the descriptor, and worth keeping.

---

## Amending a locked asset

1. Never edit an approved sheet in place. Approved sheets are immutable (`hearthlight-conventions`).
2. Make the point change by mask (law 1), producing a **new version** or a **new state asset**.
3. If the change alters identity rather than surface, it is a **new state** with a new tag, not a new
   version of the old one.
4. **Re-run the stress test.** An amended sheet is an untested sheet.

## Layout

Sheets live where `hearthlight-conventions` puts them:

```
projects/{slug}/03-bible/
  characters/{name}/
    {name}-sheet.png          ← approved. image2 on every video job. immutable.
    {name}-portrait-34.png    ← the large 3/4 face source
    states/{name}_{state}.png ← @name_wet, @name_blood — each its own asset
    candidates/               ← divergence batch; rejects kept in _rejected/
    ACTING.md                 ← master profile (hearthlight-acting)
  environments/{loc}/
    {loc}-sheet-34.png        ← 3/4, anchored, one light logic
    {loc}-{state}.png         ← day / night / rain as separate assets
    {loc}-reverse-{nn}.png    ← generated reverse angles
  props/{prop}/
    {prop}-full.png  {prop}-partial.png  {prop}-hidden.png
  refs/REFERENCE-MANIFEST.md  ← the tag dictionary
```

## Pitfalls

- Running a sheet through a model a second time "just to clean it up" — the fastest way to a plastic face.
- Baking the film look into a sheet, then wondering why every scene has the same light.
- One asset carrying two states, then wondering why the model mixes them between shots.
- A frontal location sheet, then wondering why wides invent architecture.
- Locking a sheet on a solo test, then discovering the drift only in two-shots.
- Choosing the most beautiful face in the batch.
- Text or labels on a sheet — it poisons `image2` and the model hallucinates type into clips.

## Verification

- [ ] Descriptor written, and it goes into prompts verbatim
- [ ] Sheet is flat-lit, neutral ground, no film look, no text
- [ ] Character: one large 3/4 portrait as the single clean face source
- [ ] Catch-light present in the eyes
- [ ] Each state is its own asset with its own tag and descriptor
- [ ] Location: 3/4, an anchor named, one light logic
- [ ] Tag matches the reference manifest exactly
- [ ] Stress test 10/10, run alongside other assets and in scene light
- [ ] Result recorded beside the asset
