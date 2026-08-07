---
doc: GUIDE-ASSETS
role: guide
authority: canon
owner: vince
updated: 2026-08-07
answers:
  - how to make a character sheet, a location sheet, a prop entry
  - what "locked" means and how to tell when something is not
not_here:
  the rules a sheet must obey: skills/hearthlight-character/, skills/hearthlight-mise-en-scene/
  using the sheets to make a shot: guides/shot2video.md, guides/board2video.md
---

# Guide — making your sheets

**Read this one first.** Both routes to a finished clip stand on the sheets. A weak sheet does
not announce itself; it just quietly makes every shot slightly wrong.

There are three kinds, and they work the same way.

| Kind | What it is | Lives at |
|---|---|---|
| **Character sheet** | A drawing of a person from several angles, in flat light | `03-bible/characters/{name}/` |
| **Location sheet** | A drawing of a space from several angles | `03-bible/` + a reference image |
| **Prop entry** | Text only. The canon name and description of an object | `03-bible/props.json` |

---

## The thing to understand first

Every asset is **a pair**: words plus a picture.

The **words** go into every prompt, letter for letter, every single time. The model has no
memory — it does not remember that you said "brown hair" in shot 1. If the words are missing
from shot 5, shot 5 has no brown hair.

The **picture** anchors what the words can't carry: an actual face, an actual room.

Neither works alone. This is the single most useful thing to know about the whole system.

---

## Characters

1. **Talk it through with the bot.** Say who the person is, what they want, what their body has
   been through. The skill (`hearthlight-character`) interrogates you — it's meant to. A dossier
   written from your answers reads like a person; one written from a description reads like a
   stock photo.
2. **Two files come out.** `CHARACTER.md` is for you to read. `character.json` is what agents
   read — same person, machine-shaped.
3. **The signature string.** One block of text describing the fixed, unchanging traits. This is
   what gets pasted into every prompt. Keep it to things that are *always* true — not the outfit
   for one scene.
4. **The reject list.** Things that are wrong when you see them: *"black hair — must read brown."*
   This is how you teach the reviewer what a failure looks like. Add to it every time a render
   comes back wrong in a way you can name.
5. **Generate the turnaround sheet.** Flat, even light — no drama, no coloured lighting baked in.
   You're making a reference, not a picture. Dramatic light on a sheet poisons every shot made
   from it.
6. **Check the eyes.** There must be a small bright reflection in the pupil. A sheet with dead
   eyes produces clips that cannot act, and no prompt fixes it downstream.
7. **Pick believable over beautiful.** A slightly-too-perfect face survives a still review and
   falls apart the moment it has to move.

Expect to generate several before one is right. That is the normal shape of this, not a failure.

## Locations

Same idea, one extra rule: a location sheet is a record of **a space**, not a composition.

- Draw it from three useful positions, keeping geography, colours and light identical across all
  three. Same room, different angles — nothing else changes.
- No people in it.
- Keep one consistent light logic. If the window is on the left, it is on the left in every view.
- When you use it later, say what it's *for*: **take the space and the texture, not the framing.**
  Left unsaid, the model copies the reference's composition and you get the same picture again.

## Props

A prop belongs in `props.json` when its **identity has to survive across shots** and you cannot
trust the storyboard prose to carry it.

This registry exists because of a real failure. Shot 1's prompt said *"a pile of Yu-Gi-Oh trading
cards."* Shot 5 — the same setup, four shots later — said *"a pile of trading cards."* The render
came back with generic cards. Nothing was broken. The prompt author was fine. Nothing in the
system carried the noun.

Each entry has three parts:

- **`canon`** — the exact wording every prompt must use. Be specific: era, colour, condition.
- **`forbidden`** — what it must never be. *"generic playing cards"*, *"a pristine mint card —
  this one has been carried."*
- **`shot_ids`** — which shots it appears in.

```json
{
  "id": "prop-card-pile",
  "name": "the card pile",
  "canon": "a scattered pile of Yu-Gi-Oh trading cards, early-2000s stock — brown-backed cards with the ornate tan border",
  "forbidden": ["generic playing cards, poker cards, or unbranded trading cards"],
  "shot_ids": ["43712975-…", "07efafe4-…"]
}
```

---

## Binding a sheet to its shots

A sheet only reaches a shot if it is **bound** to it. Bindings live in `03-bible/assets.json`
and `03-bible/props.json`.

**Bindings use `shot_id`, never shot numbers.** Numbers are labels and labels get renumbered —
24 of the Yu-Gi-Oh! film's 28 shots have been renumbered at least once. A registry bound to
numbers rots silently the moment the edit changes, and it fails in the worst possible way: it
hands the prompt author the *wrong* sheets, confidently.

That is not hypothetical. Shot 5 — an overhead close-up of a boy's hands — was being handed the
father's sheet, the mother's sheet, and the parents' bedroom.

If you ever see a binding written as `"shots": [1, 5, 12]`, it is stale:

```bash
python skills/hearthlight-dashboard/scripts/rekey_assets.py plan  --project {slug}
python skills/hearthlight-dashboard/scripts/rekey_assets.py apply --project {slug} --epoch legacy-last
python skills/hearthlight-dashboard/scripts/rekey_assets.py verify --project {slug}
```

`plan` writes nothing and prints every binding with the shot's **title** beside it. Read that
list before applying — *"prop-warrior-card → Warrior Returning Alive"* is right, *"→ Cleaning
Up"* is not. If a number is ambiguous the tool refuses rather than guessing, and `--epoch` is
how you tell it which numbering the file was written in.

The prompt compiler now refuses to run against number-based bindings, so this cannot silently
rot again.

---

## When a sheet is "locked"

Locked means: **you have approved it, and nothing regenerates it.**

If a locked sheet needs a change, amend it — mask and repaint the part that's wrong. Do not
re-run the generation. A second pass gives you a *different person* who resembles the first, and
the drift is invisible until you cut two shots together.

## Telling whether your sheets are good enough

Ask: *if this sheet were the only thing the model saw, would the character come back right?*

For [board2video](board2video.md) that is literally the situation — there is no still to correct
course. For [shot2video](shot2video.md) a weak sheet can be papered over at the still stage,
which is comfortable and is also how weak sheets survive for months.
