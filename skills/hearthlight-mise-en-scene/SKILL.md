---
name: hearthlight-mise-en-scene
description: Hearthlight Stage 3 (Gate 2) — the Mise-en-scène (Aesthetic Bible). The ONE organized source of truth every prompt-writing agent draws from. Two tiers: LOCKED illustration style (set in stone) + COMPOSED world (per-location props, layout, wardrobe, light — grounded in research, finalized by Vince). Consistency is the product; no sequence image before it's blessed.
version: 0.2.0
metadata:
  hermes:
    tags: [hearthlight, mise-en-scene, aesthetic, style, world, consistency, gate-2]
    category: hearthlight
---

# Hearthlight — Mise-en-scène (Aesthetic Bible) — Stage 3, Gate 2

## What this is (read first)
The single, organized aesthetic source of truth for a project. **Every prompt-writing agent — this one or another — draws from this doc when writing image/video prompts.** It replaces the older "Asset Bible" name; same job, clearer shape. It holds *all* aesthetic choices in two tiers:

- **TIER 1 — LOCKED (set in stone):** the illustration style itself. Does not change between scenes. Drift away from it is the failure.
- **TIER 2 — COMPOSED (research-informed, Vince's creative calls):** the world — per location: layout, props, wardrobe, light, vibe. Grounded in the period research; finalized by Vince; varies by scene.

A prompt is assembled as: **TIER 1 (verbatim, always) + the relevant TIER 2 location block + the specific beat.** That assembly rule is why this doc exists — so the look stays constant while the world stays specific.

Above both tiers sits an **OVERVIEW** — the visual thesis. It holds the *intent*: how the look and the world together argue the emotion of the story. Without it, an agent assembles technically-correct but dead frames ("a 1991 dorm room" instead of "the box he's trapped in while the world moves on"). The overview is what makes the props mean something.

## Why this stage exists
Consistency is the product. Drift — characters mutating between frames, the style sliding toward generic AI gloss — is a craft failure in any genre — and, for Talefeather work, the exact flaw customers punish competitors for (`profile/clients/talefeather/AUDIENCE-CONTEXT.md`). It is the failure that forced the hand-built grind. Blessed once, inherited everywhere. **Gate 2 is sacred: no sequence image before it's blessed.**

## Document layout
Lives at `03-bible/mise-en-scene.md` (+ `refs/`, `characters/`). Also mirrored to Notion as a child of the project page (it's a touch-point Vince glances at — via `hearthlight-notion-log` / `hearthlight-reference-report` patterns). Structure:

```
# Mise-en-scène — {project}

## OVERVIEW — the visual thesis  (the WHY; read before any prompt)
### Intent           ← how the look + world serve the arc (references the Vision Brief/Beat Sheet; does NOT redefine the story)
### Contrast spine    ← the deliberate juxtapositions (trapped/free, hesitant/established, private/public)
### Colour-as-emotion ← palette doing narrative work; how colour carries the turn
### Framing language  ← how characters are framed for meaning (small in frame, negative space = isolation)
### Motifs            ← recurring visual rhymes (sweat = "here it comes", light = approval)

## TIER 1 — LOCKED STYLE  (the rendered look; verbatim into every prompt)
### Style block        ← the exact ink-and-watercolour wording, LOCKED
### Palette            ← the film-wide colour discipline
### Animation/render register  ← motion feel, grain, paper, the constant aesthetic
### Style refs         ← 2–4 approved exemplar images (refs/)

## TIER 1 — CHARACTERS  (identity that must hold; also locked)
### {Character}        ← signature details (verbatim block) + approved turnarounds

## TIER 2 — WORLD, BY LOCATION  (composed from research; Vince's choices)
### {Location A — e.g. Matthew's UT room}
  - Layout / space
  - Props (named, specific, each earns its place)
  - Wardrobe (who wears what here)
  - Light & palette-in-this-room
  - Vibe / emotional register of the set
  - Establishing ref image
### {Location B — e.g. Dad's family home}
  ...

## LOCATION SHEETS — generate for the angles you will actually need
The establishing ref image above is not decoration; it is the asset every shot in that location is
built from. How it is shot decides whether the location holds.

- **3/4, never frontal.** A frontal sheet becomes flat wallpaper on wides, and past its edges the
  model invents new surroundings every time. A 3/4 view gives depth to read and covers nearly a full
  circle of angles.
- **Leave a physical anchor** — a column, a lamp, a sofa — and tie all staging to it.
  *"The hero at the lamp, facing the door"* works. *"The hero in the room"* is a lottery.
- **One light logic per sheet.** One source, one shadow direction. **Never two suns**, or every new
  angle re-invents the lighting.
- **Keep the film look out of the sheet in the same way Tier 1 keeps it out of a character
  turnaround** — the sheet supplies space and texture; the shot prompt supplies light.

### Reverse angles
**A — generate the corner.** Generate a corner of the same room in an image model, matching the soft
focus and grade of the original sheet.

**B — walk the empty room.** Generate a *video* of the empty location with the camera slowly walking
through the space; the video model draws the other sides consistently with your sheet. Screenshot the
angle you need, take it to an image model, and prompt it to improve texture and lighting. **A full
location sheet out of a single image** — the stronger of the two, and what makes a single-image
location viable when there is no conditioning still (`workflows/WF-B-storyboard-to-video.md`).

Day, night and rain are **separate assets**, not one sheet with modifiers — see
`hearthlight-conventions` § EVERY STATE IS A SEPARATE ASSET. No location locks until it passes the
stress test in that same skill.

## SOURCES & DECISIONS
  - links to research-deck + reference-report; [stylized — Vince decides] calls; rights note
```

## OVERVIEW — the visual thesis (write this FIRST; it gives the details meaning)
This is the holistic layer: how the look and the world together *argue* the story's emotion. It owns the **visual**, not the story — it references the arc in the Vision Brief / Beat Sheet and says how the *pictures* serve it. It must NOT redefine what happens (that's the Beat Sheet's job — keep the boundary or the MES quietly becomes a second script).

Five parts:

**Intent.** A short paragraph: what this piece looks like *because of* what it means. Link the Beat Sheet's detonation beat and name how the visuals build to it. (McConaughey: a son risking the true thing out loud — the visuals hold private tension against an unaware, carrying-on world, until a father's voice lets the held breath out.)

**Contrast spine.** The deliberate juxtapositions that give each location its reason to look the way it does. Every set earns its design from a tension:
- *Trapped / free* — Matthew framed inside the dorm window; outside, sunny campus life moves on without him, indifferent.
- *Hesitant / established* — Matthew's nervous, provisional space vs. Dad's domestic life: carfree, settled, a beer on the couch, the unaware warmth of someone who has already arrived.
- *Private / public* — the most private sentence of his life said while tethered (the cord) to a shared room.

**Colour-as-emotion.** Palette doing narrative work (distinct from the factual period palette in Tier 1). How colour carries the turn — e.g. the dorm cool, blue-grey, isolating; Dad's home warm, golden, incandescent; the emotional release is the moment warmth *reaches* Matthew. Name the colour journey, not just the colours.

**Framing language.** How characters are framed for meaning, so it isn't improvised per panel: Matthew *small* in the window with the world wide around him; negative space (the watercolour's white paper) as isolation and as room-to-listen on the VO-heavy beats; the camera close and boxed on him, wide and unbothered on the campus. Tie framing to the contrast spine.

**Motifs.** Recurring visual rhymes that bind the piece and stay deliberate instead of accidental: the bead of sweat down the neck ("here it comes"); light as approval/blessing; the coiled cord as the physical line of tension (taut while he braces, easing when the blessing lands — a charged object that *changes*, tracked across the location's props in Tier 2).

Rule: every Tier-2 location section should trace back to a tension in the contrast spine. If a set can't name the tension it embodies, it's set dressing, not mise-en-scène.

## TIER 1 — Locked style (the set-in-stone half)
**Style block** — the exact language pasted *verbatim* into every prompt. Vince authors/locks it. Working draft pending his blessing:
> `hand-drawn ink and watercolour illustration, loose expressive ink linework with varied line weight, transparent layered watercolour washes, visible cold-press paper texture, pigment blooms at wash edges, muted warm palette, generous white-paper negative space, soft wet-in-wet backgrounds, confident dry-brush detail on figures, storybook realism`

Rules: concrete painter's language; no model-flattering tags ("masterpiece"), no generic tags ("cinematic"); 30–60 words. Once blessed → **LOCKED**; changing it re-opens Gate 2. This block is the single source of truth for the *look* — every other skill (image-prompts, video-prompts) quotes it, never redefines it.

**Style refs** — 2–4 exemplars Vince approves, in `refs/`. Passed as image inputs where the model supports them.

## TIER 1 — Characters (identity, also locked)
Per character at `03-bible/characters/{name}/`:
- **Signature details: 2–3 features that survive stylistic abstraction.** Not photographic likeness — a watercolour figure holds identity through silhouette and emblem, not face geometry (young McConaughey: lean frame, the specific hair, the era wardrobe). Verbatim phrase block, used unedited in every prompt featuring them.
- **Turnaround set: 3–5 approved images** — front, profile, the expression range the Beat Sheet needs. Approved BEFORE sequence work.
- Pilot rights note: stylized resemblance only, never photoreal likeness.

## TIER 2 — World, by location (the composed half)
This is the mise-en-scène proper — built FROM the research (`research-deck.md` + the reference report), finalized by Vince's creative choice. One section per recurring location. Each holds:
- **Layout / space** — how the room is arranged, what the camera sees (the dorm's bed/desk/window; Dad's couch/TV/kitchen).
- **Props** — named and specific, each earning its place (the coiled-cord phone, the beer on the side table, the desk clutter). The excavation principle: objects that feel like they were there before the camera arrived. Pull from research; never invent un-sourced period detail.
- **Wardrobe** — who wears what in this location (Matthew's college-1991 tee/jeans; Dad's evening-at-home look anchored to `father photo.png`).
- **Light & palette-in-room** — this set's specific light (brass-and-glass ceiling fixture, warm 2700K pool on the couch) within the film-wide palette.
- **Vibe** — the set's emotional register (the dorm's nervous privacy; the family room's unaware warmth).
- **Establishing ref** — one approved image that fixes the look of the location.

Every Tier-2 detail traces to research or is tagged `[stylized — Vince decides]`. Research populates the world, never the story.

## Procedure
1. Read the approved Vision Brief, outline docs, `research-deck.md`, and the reference report. List required characters, locations, and (from the Beat Sheet) the expression range per character.
2. **Overview first.** Draft the visual thesis: intent, contrast spine, colour-as-emotion, framing language, motifs. Propose it to Vince in chat — this is where his storytelling instinct leads (e.g. dorm-vs-campus). The details that follow should serve it.
3. **Tier 1:** draft the style block + 4–6 candidate style-ref prompts; generate, post to Telegram for selects. Build character signature details — propose in chat FIRST, approve, then generate turnarounds.
4. **Tier 2:** for each location, compose the world section from research, **anchored to its tension in the contrast spine**; surface every uncertain detail as a `[stylized — Vince decides]` choice. Generate one establishing image per location.
4. Assemble `mise-en-scene.md` in the two-tier layout; mirror to Notion.
5. **GATE 2:** post the bible summary to Telegram. Explicit ✅ required on: style block wording, style refs, each character's signature details + turnaround, each location's world section + establishing image.

## How prompt-writers use this doc (the touch-point contract)
- `hearthlight-image-prompts` and `hearthlight-video-prompts` assemble: **Tier-1 style block (verbatim) + Tier-1 character signature block (verbatim) + the beat's location Tier-2 details + the specific action.**
- Tier-1 blocks are COPIED, never paraphrased (paraphrase = drift). Tier-2 details are selected by which location the beat is in.
- If a prompt needs a world detail not in the doc → stop, add it to the relevant Tier-2 location (sourced or `[stylized]`), then prompt. The doc stays the single touch-point.
- **The overview drives composition.** A beat's prompt should realize the framing language and contrast spine, not just list props — e.g. a dorm beat composes Matthew *small in the window* with campus beyond, because the overview says so. Props place the world; the overview decides how the camera feels about it.

## Drift policy
- **Character drift** = a signature detail missing/mutated. **Style drift** = gloss creep (over-rendered, oversaturated, plastic skin, vanished paper texture), palette shift, mechanical linework. **World drift** = props/wardrobe inconsistent with the location's Tier-2 block.
- Drift caught at review → regenerate that image; fine.
- Drift recurring across 3+ images → the doc is underspecified. Stop; propose an amendment (re-opens Gate 2 for that component only). Never quietly mutate individual prompts to compensate — that's how the ChatGPT grind happened.

## Pitfalls
- **Skipping the overview and going straight to props** — that yields period-accurate, emotionally-dead frames. The thesis comes first; the details serve it.
- **Overview drifting into story** — it owns the visual, not the plot. If it starts inventing events or dialogue, it's overstepping the Beat Sheet. Reference the arc, don't rewrite it.
- A Tier-2 location that names no tension from the contrast spine — that's set dressing, not mise-en-scène.
- Treating Tier 1 and Tier 2 as the same — the look is locked, the world is composed; keep them visibly separate.
- Generating sequence images "to test" before Gate 2.
- Style blocks of model-flattering/generic tags instead of painter's language.
- Signature details that don't survive abstraction (eye colour drowns in a wash; silhouette survives).
- Un-sourced period props in a Tier-2 block; photoreal likeness on the pilot.
- Letting a second doc define style — this is the only aesthetic source of truth.

## Verification
- The OVERVIEW is present and leads the doc: intent (linked to the arc, not redefining it), contrast spine, colour-as-emotion, framing language, motifs.
- Every Tier-2 location traces to a tension in the contrast spine.
- `mise-en-scene.md` exists in the two-tier layout (+ overview); mirrored to Notion.
- Tier 1: style block marked LOCKED + approved refs; each character has a signature block + turnaround.
- Tier 2: every recurring location has a full world section + establishing image; every detail sourced or `[stylized]`.
- Gate 2 ✅ explicit in Telegram before any Stage 4 work.
- A prompt-writer can assemble a correct prompt using ONLY this doc + the beat.
