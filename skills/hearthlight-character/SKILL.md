---
name: hearthlight-character
description: Hearthlight character creation — meaning-first interrogation producing a terse human dossier (CHARACTER.md) plus a machine record (character.json) that agents read for prompt assembly. Owns the signature string, the reviewer's reject-list, and the lighting-neutral turnaround sheet wired to image2 on every video job. Use when a project needs characters designed, or an existing one reads generic or machine-drafted.
metadata:
  hermes:
    tags: [hearthlight, character, design, turnaround, model-sheet, consistency]
    category: hearthlight
---

# Hearthlight — Character Creation

## When to Use
Stage 3, or whenever a character reads generic, drifts between frames, or was machine-drafted
and never interrogated. This skill owns **making** a character. `hearthlight-mise-en-scene` owns where
the result is filed.

## Why it exists
Four skills consumed a character sheet and none made one: `mise-en-scene` defined the slot,
`image-prompts` quoted the string, `comfyui-graph` wired it to `image2`, `shot-runner` attached it. The
gap got filled by model defaults — which is how a project ends up with "a lean man in a dark olive
military uniform, short cropped hair, tired eyes": fluent, factually wrong, dramatically inert.

**The sheet is a live production input**, wired to `image2` on every Seedance job. Anything baked into
it — a body type, a lighting scheme, a wrong uniform — is inherited by every clip.

---

## TWO DOCUMENTS, ONE CHARACTER

Split by reader. Agents should never load prose they can't use, and Vince should never read JSON.

| File | Reader | Holds |
|---|---|---|
| `CHARACTER.md` | Vince | meaning, look, never-list, wardrobe, expressions, refs, decisions |
| `character.json` | agents | signature string, turnaround prompt, generation settings, must_hold, review_reject_if, continuity, expressions, shots, refs |

**`character.json` is what prompt-assembling agents read.** Do not make them parse markdown.
When the two disagree, reconcile immediately — they are one character, not two.

### Writing CHARACTER.md — terse, no commentary
Vince reads these. Write in fragments. **No justification prose, no restating the skill's reasoning,
no explaining why a rule exists inside the document.** The reasoning belonged in the conversation; the
document holds the decision.

- Three opening lines: **Means / Cannot say / Tension.** One or two sentences each. Nothing else.
- Everything after is bullets and small tables.
- `## Decided` is a list of one-line verdicts, not a narrative.
- If a section needs a paragraph to explain itself, the decision isn't finished yet.

Target: **one screen.** If it scrolls twice, cut.

---

## THE LAW OF MEANING FIRST

Never begin with what a character looks like. A look chosen before a meaning is decoration, and
decoration is what reads as machine-made even when every word is accurate.

1. What does this character **mean**? What idea do they carry?
2. What is their **tension** in the contrast spine? A character who can't name one is a costume.
3. What can they **not say**? Nearly every Hearthlight character is defined by an unsayable thing.
   What do they do instead?
4. What features **accentuate** that? Appearance enters here, as an argument.
5. What would **contradict** it — and is the contradiction better?

### The contradiction pass (mandatory)
Generate at least one reading that opposes the director's instinct, argued at its strongest. The first
idea is usually the *legible* one; the opposing reading is often the one that ambushes an audience.

Worth testing every time:
- The sensitive character who doesn't look sensitive. Visible fragility pre-announces emotion.
- The strong character who is soft-bodied.
- The single accessory carrying the characterization (glasses for inner life, a scar for a past). If
  one prop is doing the work, the character isn't there yet.
- Two characters written as opposites — test them as the same person at different ages, and vice versa.

Name the trade-offs. **The director decides.**

### Verify inherited descriptions
Machine-drafted character strings are frequently period-wrong. A wrong uniform or vehicle propagates
into every frame and is expensive to discover late. Research before it becomes canon.

---

## THE LAW OF ABSTRACTION SURVIVAL

Flat, minimal, illustrated styles destroy face geometry. A signature built on "round face, kind eyes"
drifts every frame.

| Survives | Does not |
|---|---|
| Body proportion, posture | Face shape, nose, jaw |
| Hair silhouette | Hair texture |
| Wardrobe shape (oversized, bloused) | Fabric detail |
| A repeated emblem (a scab, a graphic) | Eye colour, freckles |
| Where the hands go | "kind" / "tired" as adjectives |

**Test:** at two inches, in flat ink, would I still know who it is?

---

## THE REJECT-LIST (not a negative prompt)

**The observed Krea 2 schema has no negative-prompt field** — only `prompt`, `aspect_ratio`,
`resolution`, `creativity`, `intensity`, `complexity`, `image_style_references`, `styles`, `moodboards`.
Verify live before assuming otherwise. Where no negative field exists:

1. **Phrase positively in the prompt.** "bare feet" beats "no shoes". "sand-brown undershirt" beats
   "not white". Models handle negation badly; a stated positive is enforceable, a negation is a hint.
2. **Keep a few high-risk negations inline anyway** as a hedge — "no text or labels", "no cast shadows".
3. **Everything else becomes `review_reject_if`** in the JSON: a reviewer's checklist, machine-readable,
   consumed by `hearthlight-shot-runner`'s Stage A review.

Write it from one question: **what will the model add that I did not ask for?** Generators fail toward
the *stereotype of the role*, not toward noise. A soldier gets body armour. A mother gets prettified.
A sensitive boy gets glasses. This is the highest-value section in the file.

---

## THE TURNAROUND SHEET

### Lighting-neutral law
**The sheet must be flat and neutrally lit, never in the film's dramatic light.** It is `image2` on
every video job; bake in a hard backlight or a coloured shadow and every clip inherits it, making the
per-scene lighting design unenforceable. **The sheet supplies identity. The shot prompt supplies light.**

### Contents
- Three full-body views — front, side, three-quarter — consistent scale and eye-line.
- **Full body means feet visible.** If footwear or its absence is a signature, a bust-up sheet destroys it.
- Two expression studies, drawn from what the Beat Sheet actually needs. Not an emotion wheel.
- **A hands inset** where the project is hands-forward. Hands are the most drift-prone element in
  generated character work.
- One pose inset for a characteristic posture.
- **No text, labels or annotations** — models hallucinate type onto model sheets and it poisons `image2`.
- No scene props, location, dramatic action, or story lighting.

### Choosing from the batch — believable over beautiful
A generation returns several faces. **Pick the most believable, not the most beautiful.** A
beautiful-but-slightly-fake face passes a still review and shows its fakeness later in video, when it
is far more expensive to fix — and a plastic face cannot carry a performance no matter how good the
video prompt is (`hearthlight-acting`).

**Check the eyes before approving.** Even dark eyes need a small light reflection in the pupil — a
catch-light. Without it the face reads dead, and no video model can act with a dead face. This is a
**hard rejection criterion**, not a preference: the sheet is `image2` on every video job, so a dead
eye here is inherited by every clip in the film.

No character locks until it passes the stress test in `hearthlight-conventions`, run **alongside the
other characters it shares frames with** — a character stable alone often breaks in a two-shot.

### Prompt register — keyword-stacked, not prose
Krea prompts are dense comma-delimited phrases, not instructions. Do not write "Create a clean model
sheet showing…". Stack descriptors. Target **60–80 words**.

```
character model sheet, three full-body views — front, side, three-quarter — consistent scale,
feet visible, two expression studies, hands inset, [pose inset],
[SIGNATURE STRING], [wardrobe specifics], [posture],
flat even lighting, no cast shadows, plain white ground, no text or labels,
[STYLE BLOCK — verbatim from mise-en-scène Tier 1]
```

The style block goes in **verbatim**; everything else is compressed to phrases. Generation settings
(model, aspect ratio, moodboard + strength) live in `character.json`, not in the prompt body — **the
moodboard carries the aesthetic; never re-describe style in the prompt.**

---

## THE DIVERGENCE BATCH

Conversation refines what the director already suspects; generation surfaces what nobody thought of.
Run both. The batch is a controlled experiment, not "make me a character".

1. **Freeze the canon** — signature string, style block, moodboard, aspect ratio identical across variants.
2. **Swap exactly ONE variable per generation, and name it.** Body proportion, hair silhouette, wardrobe
   fit, posture, age read. More than one axis and the result is noise.
3. Cheap and small first — medium model, 1K, 4–6 images. Preflight cost on large batches.
4. Land in `candidates/`, named `{name}-candidate-{nn}-{variable}.png`.
5. **Present with the variable named**, so the verdict is legible. *"03 and 05, the heavier build"* is
   reusable taste. *"I like 3"* is not.
6. Record the **why**. Generalizable verdicts go to `profile/TASTE.md`; project-specific ones to `## Decided`.
7. Rejects to `candidates/_rejected/` — kept, never deleted.

---

## Layout

```
03-bible/characters/{name}/
  CHARACTER.md          ← human. terse.
  character.json        ← machine. what agents read.
  {name}-sheet.png      ← approved turnaround. image2. immutable once approved.
  candidates/
    {name}-candidate-{nn}-{variable}.png
    _rejected/
```

Reference images follow the Reference Naming Law and live in `03-bible/refs/` by category, indexed in
`refs/REFERENCE-MANIFEST.md` (`hearthlight-conventions`) — **not** in the character folder. The dossier
links; it does not hold.

`mise-en-scene.md` **mirrors the signature string only**, with the note *if these differ, the dossier
wins*. Never duplicate the dossier.

---

## Procedure
1. Read the Vision Brief / Beat Sheet, `mise-en-scene.md` (OVERVIEW), `profile/TASTE.md`, research deck.
   List characters and the expression range the Beat Sheet demands.
2. **Interrogate in chat** — five questions, contradiction pass, verify inherited descriptions.
3. Director decides → write `CHARACTER.md` (terse) and `character.json` (complete).
4. Optionally run a divergence batch before committing.
5. Generate the sheet. **Read the output back with vision before presenting it.**
6. **Approval** — Vince explicitly locks the signature string, reject-list, and sheet. These decisions all
   sequence work featuring that character.
7. On approval: set status in both files, mirror the string into `mise-en-scene.md`, register the sheet
   in `assets.json`, log it (`hearthlight-notion-log`).

## Pitfalls
- Designing before interrogating — the look arrives first and the meaning gets retrofitted.
- A signature built on face geometry.
- Story lighting baked into the turnaround.
- A bust-up sheet when footwear or stance is the signature.
- Skipping the reject-list; the model supplies the stereotype.
- Trusting an inherited machine-written description.
- More than one variable per divergence generation.
- **Prose in CHARACTER.md.** Commentary belongs in the conversation, not the document.
- **Prose in a Krea prompt.** Stack keywords.
- Letting `CHARACTER.md`, `character.json` and the mise-en-scène string drift apart.

## Verification
- MEANING precedes any appearance detail; `CHARACTER.md` fits roughly one screen.
- Every signature detail passes the two-inch-silhouette test.
- `review_reject_if` names the stereotype the model will reach for.
- Turnaround prompt: verbatim signature string, verbatim style block, neutral-lighting clause,
  no-text clause, keyword register, 60–80 words.
- Feet visible if footwear or its absence is a signature.
- `character.json` parses; sheet registered in `assets.json`; reachable as `image2`.
- Rejected candidates in `_rejected/`, not deleted.
