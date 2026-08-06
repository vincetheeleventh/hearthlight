# Boundary audit — `hearthlight-asset-sheets`

*Requested by Vince, 2026-08-05: "is this a necessary separation?"*
Audited against `GOALS.md` § Keeping features tight. **Nothing has been changed.** The skill was
created earlier the same day by the same agent writing this audit — treat the finding accordingly.

---

## Verdict

**The separation is real. The boundary is drawn in the wrong place.**

The skill claims to own *"how the sheet gets made"* across all asset types. That claim collides
head-on with `hearthlight-character`, which already owns how a character sheet gets made — in more
detail, and first. Roughly **half the skill restates laws that already have an owner.**

The other half is genuinely homeless and worth having. So the answer is not "delete it" and not
"keep it" — it is **shrink it to the half that has no other home.**

---

## Evidence

### It fails criterion 1

> *"Does it fight drift or add it? Does it strengthen the single source of truth, or create a second
> place where the same fact can be stated and diverge?"*

Four laws now exist in two places each. Every one of these can diverge:

| Law | Real owner | Also restated in |
|---|---|---|
| Lighting-neutral / flat sheet | `hearthlight-character` | `asset-sheets` |
| No text or labels on a sheet | `hearthlight-character` | `asset-sheets` |
| Feet visible · hands inset · expression studies | `hearthlight-character` | `asset-sheets` |
| Sheets are immutable once approved | `hearthlight-conventions` | `asset-sheets` |
| Catch-light in the eye | `hearthlight-acting` | `asset-sheets` |
| An image never runs through a model twice in full | `video-prompts/references/prompt-architecture.md` | `asset-sheets` |

The last two are the most damning: **the same agent wrote both copies within the same hour.** If
duplication happens that fast under one author, it will happen faster across three agents.

Probe counts (occurrences per file): `lighting-neutral` character 1 / asset-sheets 2 · `no text`
character 3 / asset-sheets 2 · `feet visible` character 3 / asset-sheets 1 · `hands inset` character
2 / asset-sheets 1 · `immutable` conventions 2 / character 1 / asset-sheets 2.

### It passes criterion 3

> *"Is there an active use case today?"*

Yes, and a sharp one. WF-B is blocked on sheet quality, and this material has **no other home** —
zero occurrences anywhere else in `skills/`:

- The **ten-out-of-ten stress test** (the validation gate)
- **State splitting** as a discipline — `@char`, `@char_wet`, day/night/rain as separate assets
- **Believable over beautiful** as a selection criterion
- **Location sheet craft** — 3/4 not frontal, the physical anchor, one light logic / never two suns
- **Reverse angles via the empty-room video walk**
- **Prop state versions** — full / partial / hidden-with-constraint

`hearthlight-mise-en-scene` covers locations at the level of *what the world contains*; it says
"generate one establishing image per location" and stops. It does not own sheet production craft.

### Where the real seam is

The skill's stated boundary — *who* (character) / *what* (mise-en-scène) / *how* (asset-sheets) —
sounds clean and is not. "How a character sheet is made" was already `hearthlight-character`'s, and
splitting *who* from *how* for the same artifact means two files must agree about one PNG.

The seam that actually holds is different:

> **Per-asset-type craft** stays with the skill that owns that asset type.
> **Laws true of every generated asset, and the gate that validates them,** are cross-cutting.

That is the same shape as `hearthlight-terse` — a cross-cutting law-holder, not a stage.

---

## Recommendation — shrink, do not delete

Target: **253 lines → ~110**, containing only what has no other owner.

**Keeps (cross-asset, homeless):**

1. The stress test — the gate. Cross-asset by nature.
2. State splitting and its consequences.
3. The no-double-pass / point-change masking law. *Also remove it from `prompt-architecture.md`* —
   it is a law about images, not about prompts.
4. Selection criteria: believable over beautiful, catch-light as a hard reject. *Cross-reference
   `hearthlight-acting` rather than restating.*
5. Location sheet production craft (3/4, anchor, one light logic, reverse angles).
6. Prop state versions.

**Deletes, replaced by one-line pointers:**

- The entire *Character sheets → Composition* section → point to `hearthlight-character`, keep only
  the P-011 conflict note.
- *One tag dictionary* → point to `hearthlight-conventions` § THE REFERENCE NAMING LAW.
- *Amending a locked asset* immutability → point to `hearthlight-conventions`.
- *Layout* → point to `hearthlight-conventions`, which owns directory structure.

This is the pointer-stub pattern from D-002, applied inside the instruction layer: **one canonical
statement per law, referenced from wherever it is needed.**

## The alternative worth considering

Distribute all six keeps into existing skills — character craft to `hearthlight-character`, location
craft to `hearthlight-mise-en-scene`, state/tag discipline to `hearthlight-conventions` — and delete
the skill entirely.

**Argument for:** no new skill, no new boundary, nothing to keep in sync.
**Argument against:** an agent making a location sheet would have to read three skills to assemble
the craft, and the stress test — a gate that applies to every asset type — would have no owner at
all. Gates with no owner do not get run.

The shrink keeps a real conceptual unit; the distribution optimises for file count. On balance the
shrink is better, but not by a wide margin, and it is Vince's call.

## Honest caveat

Every classification above is one agent auditing its own work an hour after writing it. The
duplication counts are mechanical and checkable. The judgment that "the stress test needs an owner"
is not — it is an argument, and it is the argument that keeps the skill alive.
