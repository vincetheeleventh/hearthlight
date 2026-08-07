---
doc: PRD-SHOT-WORKSPACE
role: proposal
authority: draft
owner: vince
updated: 2026-08-07
answers:
  - what the Shot Workspace rework must build
  - which parts already exist and must be surfaced rather than rebuilt
  - how design state and production state stay separate without splitting the record
not_here:
  the improvement backlog: PROPOSALS.md
  the authoring contracts: skills/hearthlight-image-prompts/references/
  the routes to a clip: workflows/, guides/
supersedes: Vince's draft of 2026-08-07 (kept in archive/prd-shot-workspace-v1.md)
---

# PRD — Shot Workspace rework

## 0. The correction that reorganizes this document

The original draft proposed a narrative layer, a visual-specification layer, a Current-Truth
model and a decision history. **Most of that is already built and running.** It is invisible,
which is a real and serious problem — but it is a *surfacing* problem, not a modelling one.

What exists today, in `projects/{slug}/`:

| The draft called it | It already exists as | Where |
|---|---|---|
| Narrative Intent | `one_liner`, `expanded` | `05-storyboard/shot-narrative.json` |
| Design Rationale | `why_this_shot` | same |
| Sequence membership | `beat` | same |
| Motifs | `motifs[]` | same |
| Avoid | `never[]` | same |
| Visual Specification | `staging.surfaced` / `staging.ambient` | same |
| Emotional register | `charge`, and film-level `value_axis` | same |
| Must Preserve / Avoid, per character | `must_hold[]`, `review_reject_if[]` | `03-bible/characters/*/character.json` |
| Current Truth | `current_visions()` folding an append-only ledger | `04-images/shot-vision.jsonl` |
| Decision History | the same ledger, with `previous_vision` and `previous_revision` | same |
| Director Input, interpreted and confirmed | `vision-rant-applied` events carrying `confirmed_by_user` | same |
| Design Lock | `confirmed_by_user: true` on the current Vision | same |
| A typed shot relationship | `shared_setup_owner_shot_id` | `05-storyboard/shots.json` |

The film currently has 38 Vision events across 32 shots, 6 confirmed by Vince, and one
`vision-rant-applied` batch sourced `vince-rant:2026-08-04:shots-2-3-5-6-7`. **The loop the draft
proposes as new has already run in production.**

**Therefore this PRD is not "define a narrative model." It is "make the model that exists
visible, complete the three things genuinely missing from it, and never create a second one."**

That distinction is not pedantic. Hearthlight has already paid once for a second source of
truth: the shot-list workbook, which held prompts a spreadsheet could show and JSON could not.
Retiring it cost a migration, a repair pass, an extraction tool and a verifier that nearly
shipped sharing a bug with the thing it verified. **A "Narrative Intent" field in a new UI store,
alongside `one_liner` in `shot-narrative.json`, is that same mistake with better typography.**

## 1. Problem

Not a lack of information, and — correcting the draft — **not primarily cognitive overload
either.** The overload is the symptom.

The disease is that **the record and the view have different shapes.** The record is a
gate-governed, append-only, contract-hashed specification. The view is a flat page that shows
fields. So the filmmaker cannot see, in the UI:

1. Which facts are authoritative and which are superseded baseline.
2. Whether the current Vision has been confirmed or is still a machine draft.
3. What the current candidate fails to satisfy, stated as a checkable list.
4. Whether a proposed change is a production correction or a design change.
5. What else breaks if the design changes.

Points 1, 2 and 5 are *existing state the UI does not render*. Points 3 and 4 are *genuinely
missing from the system*. Keeping those two categories apart is the whole discipline of this
rework.

## 2. North Star

**The filmmaker should be able to leave a shot for three weeks and return without reconstructing
anything.** Why it exists, what must be true, what is wrong now, what to do next — all readable
without opening a prompt, a ledger, or a JSON file.

Second, and equal in weight, and absent from the original draft:

**The view must never become a way to be confidently wrong.** Shot 5 rendered generic trading
cards while every narrative field on its page was correct and well written. The cause was a stale
registry binding handing the author the father's and mother's sheets. A workspace that surfaces
intent beautifully while the bindings rot is a more comfortable way to get the same bad render.
**Correctness indicators are a first-class surface, not a diagnostics panel.**

## 3. Core principle

> **Director input is prose. System state is structured. The structure already exists — the UI's
> job is to show it and to let prose edit it.**

The filmmaker writes or speaks freely. Hearthlight interprets into the *existing* schema, shows
the interpretation, and writes only on confirmation. This is exactly the `vision-rant-applied`
path that already ran. What is missing is the **confirmation step in a UI** — today it happens in
chat, which is why it is invisible and unauditable to the filmmaker after the fact.

## 4. The layers, and how they connect to what exists

The draft's three layers are the right decomposition. What it never says is **where each layer
lives, who writes it, and what reads it** — so the layers float free of the system and the UI has
to invent storage for them. That invention is the whole risk.

### 4a. The connection, stated once

> **The Shot Workspace renders `source_bundle(root, [shot_id])` — the same function that feeds
> the prompt author.**

This is the architectural answer, and everything else in this section follows from it.
`prompt_authoring.source_bundle()` already assembles, for one shot: the current Vision and its
revision, the authority resolution, the storyboard baseline, the narrative record, adjacent-shot
continuity, bound characters, bound assets, bound props, special visual laws, the shared-setup
owner, and a set of provenance hashes.

That is the three-layer model, already assembled, already versioned, already the thing the model
sees.

Two consequences, both load-bearing:

- **The UI cannot drift from the machine.** A field the page shows is a field the author
  received. A field the author received is a field the page can show. There is no third list.
- **"What was the model actually given?" becomes directly answerable** — today the only way to
  answer it is to read a packet JSON. It is the single most useful debugging question in the
  system and it currently has no surface.

The bundle needs one addition for UI use — the production layer (§4d), which does not feed the
author because the author runs *before* a candidate exists. Extend the bundle with a
`production` block rather than building a parallel assembler.

### 4b. Layer 1 — Narrative intent

| | |
|---|---|
| **Answers** | Why does this shot exist? |
| **Seed** | `05-storyboard/shot-narrative.json` → `one_liner`, `expanded`, `why_this_shot`, `beat`, `charge`, `motifs[]`, `never[]` |
| **Live state** | `04-images/shot-vision.jsonl`, folded by `current_visions()` |
| **Written by** | Vince, in prose, via director input → a `vision-rant-applied` event |
| **Read by** | `source_bundle` → `shots[].vision`, `shots[].narrative` |
| **Authority** | Rank 2 — **creative authority**. Supersedes the storyboard on conflict |
| **Film-level** | `value_axis` (`"expression ↔ bottling up"`) — the contrast spine |

**The UI edits this by writing prose, never by editing fields.** The fields are the
interpretation; the prose is the input. A form here would invert the core principle.

### 4c. Layer 2 — Visual design

| | |
|---|---|
| **Answers** | How does the shot communicate that intent? |
| **Storage** | `shots.json` → `text.*`, `image_direction.*`; `shot-narrative.json` → `staging.surfaced` (shot type, camera move, character actions, setting) and `staging.ambient` (lighting, sound) |
| **Relationships** | `shared_setup_owner_shot_id` today; the edge list in §6c |
| **Evidence** | `panel.path` — the hand-drawn board, tier 3 |
| **Read by** | `source_bundle` → `shots[].storyboard`, `shots[].adjacent_continuity` |
| **Authority** | Rank 3 — **supersedable baseline**. Concrete, and concreteness is not authority |

The UI must render rank 3 *as* rank 3. When the Vision has displaced a storyboard fact, the
displaced fact should read as superseded rather than sit beside its replacement looking equally
true. `supersedes` already comes back from the author for exactly this.

### 4d. Layer 3 — Production

This is where the draft is thinnest and where the connection genuinely does not exist yet.

| Sub-layer | Storage | Status |
|---|---|---|
| **Target** — what must be true of the image | `04-images/shot-targets.json`, keyed by `shot_id`, carrying `derived_from` hashes | **NEW** (§7) |
| **Prompt** — the current instruction | `shots.json` → `prompt.still`, `prompt.action`, `prompt.revision` | exists |
| **Candidates** — every generation | `04-images/generations.jsonl` → `generation` events | exists |
| **Hero** — the chosen one | same ledger → `selection` events, `purpose: hero` | exists (§10) |
| **Problems** — why a candidate is wrong | `04-images/shot-problems.jsonl` | **NEW** (§6b) |
| **Bindings** — which sheets reach this shot | `03-bible/assets.json`, `03-bible/props.json` | exists, now by `shot_id` |
| **Inputs health** | computed, never stored | **NEW** (§8) |

### 4e. Authority is already law — render it, don't restate it

From `PROMPT-AUTHOR.md`: film laws and aspect → **latest Shot Vision** → storyboard and panel →
adjacent-shot continuity → character/location/prop records → provider profile.

The UI must *render* that order. A workspace that lays the six sources out as six equal panels
is teaching a hierarchy the system does not have, and the filmmaker will act on what the layout
implies rather than on what the contract says.

### 4f. Sequence and beat are one concept — decided

**`beat` is the sequence.** No second grouping. Sequence-level intent attaches to a beat, and
shots inherit from their beat.

**When a shot's intent conflicts with its beat's, nothing resolves it — it is flagged to Vince.**
This matches the posture everywhere else in the system: the panel reader names conflicts and does
not settle them, the continuity agent reports and does not resolve. A UI that silently
reconciled a shot against its sequence would be the first component in Hearthlight allowed to
overrule a creative decision by inference.

### 4g. Design Lock is a gate — decided

It behaves like one, so it is one. It enters the gate ledger with the others (`status.yml`,
`hearthlight-dashboard`), and `confirmed_by_user: true` on the current Vision is its record.

Consequence worth stating: **a gate is crossed once and reopened deliberately.** That is exactly
the escape-hatch semantics in §12, so the two are now the same mechanism rather than two similar
ones.

## 5. Modes are lenses, not places

The draft proposes two modes. **Adopt the intent, reject the implementation.**

Two modes with two data surfaces produce two places to look for one fact, and a mode you must
remember to be in. The draft already has the better idea in §16 — *lenses* on the overview.
Apply that everywhere.

**One shot page. One record. The lens changes emphasis, never content.**

- **Story lens** — intent, audience state, sequence position, relationships, rationale foreground.
  Production controls collapse.
- **Production lens** — target, candidate, unmet criteria, problems, controls foreground. Narrative
  collapses to the one-liner and the `never[]` list, which stay visible because they are *binding
  during production*.

The lens should **default from state, not from memory**: a shot whose design is locked and whose
production is unfinished opens in the production lens. Never make the filmmaker set a mode to see
the thing they obviously came for.

## 5a. The information hierarchy — the actual rework

This is the centre of the work. Everything else in this document supports it.

The current page has no hierarchy: storyboard, prompt, image direction, narrative, vision,
references, stage, model, likeness, video motion and technical parameters all sit at one level.
The result is that **nothing is emphasised, so everything has to be read.**

The rule, applied without exception:

> **What decision is the filmmaker making right now?** Everything that serves it is persistent.
> Everything that serves a different decision is one interaction away. Nothing is deleted.

### Band 1 — persistent spine (always visible, both lenses)

Six things. The list is short on purpose; a seventh will be proposed within a month and should be
refused.

| | Field |
|---|---|
| **The board** | `panel.path` |
| **The hero** | latest `selection` event, `purpose: hero` |
| **Intent, one sentence** | `narrative.one_liner` |
| **Design · Production · Inputs** | `confirmed_by_user` · gate ledger · computed (§8) |
| **Blocking problems, count and worst** | `shot-problems.jsonl`, open entries |
| **What I asked for last** | latest director input, verbatim |

Board and hero **side by side, same size, always.** The comparison the filmmaker makes most is
"does the render match the drawing", and today that requires scrolling.

### Band 2 — lens-contextual (one band, swaps on lens)

**Story lens** — `narrative.expanded`, `why_this_shot`, `charge`, `beat` and its position,
`motifs[]`, relationship edges (§6c), the adjacent shots' one-liners.

**Production lens** — the target's Must Show / Must Preserve / Avoid, acceptance criteria with
met/unmet state, open problems, the asset strip, generation controls.

**Both lenses keep `never[]` visible.** It is the one narrative field that is *binding during
production*, and burying it in the story lens is how a violated Never survives to a render.

### Band 3 — collapsed (present, labelled, one click)

Full prompt text and `prompt.revision` · prompt history · the Vision ledger · generation
parameters, model, seed, dimensions · references and bindings · superseded storyboard facts ·
archived candidates · all hashes.

Collapsed is **not hidden**. Every drawer shows a one-line summary so the filmmaker knows whether
opening it is worth it: *"Prompt · rev 4 · edited by cowork 2 days ago"* beats *"Prompt ▸"*.

### What moves down from where it is today

Prompt text, model and stage are currently prominent. They are **implementation**, and the
draft's own non-goal says prompts are not the primary creative artifact. Demote all three to
Band 3. This is the single largest reduction in clutter available and it will feel wrong for
about a week.

### The one thing to add that does not exist anywhere

**A "what the model was given" view** — Band 3, rendering `source_bundle` for this shot exactly
as the author received it. When a render is inexplicable, this answers it in one click. Nothing
in the system surfaces this today, and it is the question most worth being able to ask.

## 6. What is genuinely new — build these three

Everything else in this PRD is surfacing. These are additions.

### 6a. Acceptance criteria (highest leverage; the draft buried it at §14)

A per-shot, checkable definition of done. **Required** and **Flexible**.

This is the antidote to a failure the system has already named: the ten-to-fifteen rule in
`workflows/README.md` — *"if a shot has not come together in that many iterations, the problem is
not the wording."* Today nothing states what "come together" means, so iteration has no
terminating condition and Gate 3 fatigue does the terminating instead.

**Derive, do not ask.** The first draft of the criteria is generated from what already exists:
`never[]` becomes Required-negative, character `must_hold[]` becomes Required, `staging.surfaced`
becomes Required-compositional, everything else defaults to Flexible. Vince edits the derived
list. **A form the filmmaker must fill from scratch will not get filled** — that is the draft's
own non-goal, and derivation is how you honour it.

Rule: **a candidate cannot be approved with an unmet Required criterion, and cannot be rejected
solely for a Flexible one.** The second half matters more than the first.

### 6b. The problem ledger

The draft's `Target → Candidate → Problem → Intervention → Result` loop, made durable.

Append-only, one entry per diagnosed problem, at `04-images/shot-problems.jsonl` — matching every
other ledger in the system.

**Constraint the draft misses:** the problem vocabulary must be **the same vocabulary** as the
continuity agent's finding codes (`prop_drift`, `identity_drift`, `setup_drift`,
`geography_drift`, `light_drift`, `binding_gap`, `count_drift`) plus the render-only codes the
draft adds (`anatomy`, `image_coherence`, `expression`, `style`). Two taxonomies for one
phenomenon means no query can ever cross them, and the learning loop in the draft's §10 — *"learn
what interventions resolve recurring problems"* — silently dies.

An intervention entry records what was changed and what happened. That is what makes the ledger
worth more than a notes field.

### 6c. Relationships as typed edges

`shared_setup_owner_shot_id` is already a typed edge and already reaches the continuity agent's
packet as `reuses_setup_of`. **Generalize it; do not invent alongside it.**

An edge list at `05-storyboard/shot-relationships.jsonl`: `{from, to, type, why}` with types
`match_cut`, `visual_echo`, `contrast`, `setup`, `payoff`, `escalation`, `reversal`, `reveal`,
`shared_setup`, `continuity_dependency`.

The value is not the diagram. It is that today this information sits in prose — shot 1's Vision
reads *"ends on a firm pulling hand for the match cut into Shot 2's bootlace pull"* — where no
agent can act on it and no warning can fire when shot 2 changes.

**Every edge feeds the continuity agent's packet.** That is the test of whether an edge is real:
if nothing downstream consumes it, it is decoration.

## 7. Production target

Derived from the locked design, confirmed by Vince, stable during production.

Fields: **Intent · Must Show · Must Preserve · Avoid · Continuity constraints · Reference.**

Two corrections to the draft:

- **Derived, not authored.** Must Show comes from `staging.surfaced` and the Vision's frame-one
  sentence. Avoid comes from `never[]` and the bound characters' `review_reject_if[]`. Continuity
  constraints come from the relationship edges and the bound registries. The filmmaker edits a
  draft; he does not compose one.
- **The target carries its provenance hash.** Like `author_guide` already does in the prompt
  packet. A target that no longer matches the Vision it was derived from must say so, loudly,
  rather than quietly governing production from a superseded design.

## 8. Production status and the two-axis state

Adopt the draft's split; it is correct and the record already supports it.

- **Design:** `Exploring` → `Designed` → `Locked` (`Locked` = `confirmed_by_user: true`)
- **Production:** `Not started` → `In progress` → `Needs fix` → `Candidate ready` → `Approved`

`Design: LOCKED · Production: NEEDS FIX` tells the filmmaker to fix the image, not the shot.
This is the single highest-value line on the page and should be rendered as such.

**Add a third axis the draft omits — and it is the one that would have caught shot 5:**

- **Inputs:** `Ready` · `Stale` · `Broken`

`Stale` when a bound sheet changed after the last generation. `Broken` when a registry binds by
number, a bound panel file is missing, or the props registry has no entry for a prop the prompt
names. This axis is machine-computed, never set by hand, and **blocks generation when `Broken`.**

Design and production status describe what Vince thinks. The input axis describes whether the
machine is being fed correctly. The draft has no surface for the second, and the second is where
the bad renders actually come from.

## 9. Director input

Keep the draft's design. One addition and one sharpening.

**Addition — the interpretation is a diff, not a summary.** Show what changes *against current
truth*, field by field, with the old value struck through. "Cards should be substantially more
chaotic" is not reviewable; `staging.surfaced.character_actions: "searching with purpose" →
"searching with mounting disorder"` is.

**Sharpening — routing is a claim the filmmaker can correct before it lands.** The interpretation
must show *which layer* each item is going to, because that classification is the thing most
likely to be wrong and most expensive to discover later. Actions: **Apply · Edit · Cancel**, per
item, not for the whole block.

The raw note is preserved verbatim as source. Interpretation never replaces it.

## 10. Asset history, hero selection, and provenance links

Three functions, and — consistent with everything else in this document — **all three already
exist in the ledger and none of them has a control in the UI.**

`04-images/generations.jsonl` currently holds 44 events for the Yu-Gi-Oh! film: 39 `generation`,
4 `krea-submitted`, 1 `selection`. Every generation event already carries `version`,
`parent_version`, `workflow_stage`, `asset_path`, `sha256`, `dimensions`, `aspect_ratio`, the
`prompt` that made it, `prompt_sha256`, `model`, `references`, and **`krea_url` on 38 of 39.**

### 10a. Asset history

**Every candidate a shot has ever produced, in one strip, newest first.**

Per asset, from fields that already exist: thumbnail · version · workflow stage · the prompt that
made it (collapsed) · model · date · hero badge.

`parent_version` is already recorded, so the strip can render as a **tree** rather than a flat
list — which is the difference between "17 attempts" and "three lines of enquiry, one of which
went somewhere." That is the more useful shape and it costs nothing extra to store.

**Nothing is ever deleted.** Archiving is a view filter, never a file operation. The ledger is
append-only and an asset that looked wrong in August is evidence in October.

### 10b. Promote to hero — mostly already shipped

**This already works.** `productionAssetActions()` renders a **Use as hero** button on every
asset, disabled when it is already hero or is `stale`, posting to
`/api/productions/{slug}/shots/{shotId}/assets/{assetId}/select` — writing the same `selection`
event `set_shot_image.py` writes.

`set_shot_image.py`'s docstring — *"the Studio UI resolves a shot's hero asset automatically and
has no control for overriding it"* — is **out of date and should be corrected.** A stale comment
claiming a gap is how the same feature gets built twice.

The remaining gaps are narrower than the draft assumes:

- **No note is captured on promotion.** The single existing `selection` event carries *"boot
  insert; passes reject-list — no tags, no object, none of her hands"* — written by hand from the
  CLI. The UI path writes nothing. That sentence is exactly the reasoning that evaporates in three
  weeks, and it is one text field away.
- **No hero history.** Selections accumulate in the ledger and nothing shows what was hero and
  when. Reverting is another selection event, never an undo — a shot that has changed hero four
  times is telling you something.
- **`stale` disables the button with no stated reason**, which reads as a bug rather than a
  guard. The concept is already wired through the server and the JS, so the Inputs axis in §8 has
  a foothold rather than needing to be invented — but it has to *speak*.
- **Promotion should block on an unmet Required criterion** (§6a) once those exist — overridable
  visibly and with attribution, never silently.

### 10c. Drag and drop an outside image

Also already built. `set_shot_image.py --image <path>` copies the file to a properly-versioned
name, writes a `generation` event registering it, then a `selection` event promoting it. One
asset in the film arrived this way already (`origin_path` set, `source: set_shot_image.py`).

**Requirement: dropping a file onto the shot page calls that same path.** Not a new import route
— the same script, so a hand-made image is a first-class citizen of the ledger with a hash, a
version and a parent, rather than a loose file that happens to be displayed.

The dropped image will have no prompt. Record `prompt_known: false` — that field already exists
and is already honoured — rather than inventing a prompt to fill the column.

### 10d. Link every asset to its source

`krea_url` and `krea_job_id` are on 38 of 39 generations and appear nowhere in the UI. That is
pure surfacing: **an "Open in Krea" link on every asset that has one.**

One correction to make it durable. `krea_url` is provider-specific, and the film already contains
assets from three sources (`hearthlight-krea`, `hearthlight-krea-frame-one-v4`,
`set_shot_image.py`) with MiniMax H3 clips arriving next. Generalise:

```json
"provenance": {
  "provider": "krea",
  "job_id": "5d6636e1-…",
  "url": "https://gen.krea.ai/images/dff9707e-…"
}
```

Keep `krea_url` populated for backward compatibility; read `provenance.url` first and fall back.
A locally-generated ComfyUI clip has no URL and should show its graph and seed instead — the
field is *provenance*, not *link*, and a local render has provenance too.

**Where an asset has no provenance at all, say so on the card.** An image nobody can trace to a
prompt, a job or a person is exactly the thing that should not quietly become the hero.

## 11. Current truth vs history — already solved, with one gap

`current_visions()` folds an append-only ledger to the latest authoritative state. The draft's
requirement is met.

The gap: **contradiction detection across layers.** The ledger prevents contradictory *Visions*
accumulating. It does nothing about a Vision that now contradicts a character's `must_hold`, a
prop's `canon`, or a related shot. That is the continuity agent's job, and the UI should surface
its findings **on the shot page**, not in a separate report — which is where a report goes to be
ignored.

## 12. The escape hatch

Keep the draft's **Request Design Change**, secondary and explicit.

Add: **it must show consequences before it opens.** Changing a locked design touches every shot
on the other end of a relationship edge. The dialogue should name them — *"shot 2 depends on this
via match_cut; shot 5 reuses this setup"* — before Vince decides, not after.

## 13. Overview

Keep the draft's design. Add one lens: **Inputs lens** — which shots have stale or broken inputs.
It is the only lens that shows problems the filmmaker cannot see by looking at the images.

## 14. AI responsibilities — one important correction

The draft's §18 ends: *"AI should advise rather than block filmmaker decisions."*

**Half of that is right and half contradicts a hard-won law.** `PROMPT-AUTHOR.md` states: *"When
sources cannot be reconciled: block. Never average contradictions into vague prose."* And
`AGENTS.md`: *"Blockers are the product."* Those exist because a fluent prompt built on an
unresolved contradiction produces a confident wrong render — which costs a paid generation and a
review cycle to discover.

The distinction the draft collapses:

- **The AI must never block a creative decision.** Vince wants the shot redesigned, it gets
  redesigned. No warning gates that.
- **The AI must always block a generation on an unresolved contradiction, a broken input, or an
  unmet Required criterion.** Not advise — block.

Different verbs, different objects. Advising on judgment, blocking on incoherence. The UI should
make an override possible, visible and attributed — never silent and never default.

## 15. Migration — invert the draft's assumption

The draft says existing data *"should be interpreted and migrated."* The risk runs the other way.

**The existing data is already in the target shape.** `one_liner → Intent` is a rename, not an
interpretation. An LLM re-interpreting good structured data will paraphrase it, and paraphrase is
loss.

Rule: **where a mapping is 1:1, no model touches it.** Reserve interpretation for the genuinely
unstructured — free-text notes, `why_this_shot` prose containing relationship claims that need
extracting into edges. Flag those for review; migrate the rest mechanically and verify by hash.

The lesson is already written down in `workflows/board-intake.md`: *faithful migration is not the
same as correct migration* — and its inverse holds here. Re-authoring is not migration.

## 16. Non-goals

Keep all eight from the draft. Add three:

- **The UI must not become a required participant.** Every write it performs must go through the
  same script layer Hermes and Cowork use. A design state editable only in a browser makes the
  pipeline un-runnable headless and un-runnable by an agent.
- **No field exists that no downstream consumer reads.** If a new field does not reach a prompt
  packet, a continuity packet, a gate check or a criterion, it is documentation. Delete it.
- **The workspace must not become the place decisions are recorded but not enforced.** A
  Must-Preserve that nothing checks is worse than no Must-Preserve — it creates the belief that it
  is being honoured.

## 17. Success criteria — falsifiable versions

The draft's criteria are unmeasurable ("understand within seconds"). Replace with tests that can
fail:

1. **The three-week test.** Vince opens a shot untouched for 21 days and states its intent, its
   binding constraints, and the current blocker **without opening a prompt, a ledger or a JSON
   file.** Fails if he opens any.
2. **The routing test.** Given *"there's two soldiers, the left one should be his wife, don't
   change the composition"*, the interpretation routes all three items correctly — production
   correction, identity/count problem, composition preserved — with no design change proposed.
   Measured over 20 real notes; target ≥ 90% correct routing **before** confirmation.
3. **The shot-5 test.** A shot with a stale or wrong registry binding is visibly `Inputs: Broken`
   on the overview **before** a generation is spent. This is the one criterion that would have
   caught the defect that prompted the rework.
4. **The termination test.** Median iterations to an approved candidate falls after acceptance
   criteria ship. If it does not, the criteria are being written too loose to bind.
5. **The no-second-source test.** After the rework, `grep` finds exactly one storage location for
   each of intent, staging, motifs and never-list. Fails on any duplicate.

## 18. Sequencing

The draft implies one rework. Ship in an order where each stage is useful alone:

1. **The information hierarchy (§5a)** — three bands, prompt and model demoted, board and hero
   side by side, `source_bundle` rendered. No new storage at all. This is the rework the
   filmmaker actually asked for and it delivers most of the North Star on its own.
   **Sub-stage 1b, same sprint:** the note field on hero promotion, the provenance link, and
   `stale` stating its reason — three small surfacings of data already in the ledger.
2. **The inputs axis** — machine-computed, blocking. Smallest change, catches the shot-5 class.
3. **Acceptance criteria**, derived and editable. Gives iteration a terminating condition.
4. **The problem ledger**, sharing the continuity vocabulary.
5. **Relationship edges**, feeding the continuity packet.
6. **Director-input diff-and-confirm in the UI.** Last, because it is the only one that needs all
   the others to be worth confirming into.

Stage 1 alone is worth shipping and stopping to look at. If it does not measurably help, the
diagnosis in §1 is wrong and stages 2–6 should be re-argued rather than built.

## 19. Decisions — the four questions, closed

Vince ruled on 2026-08-07. Recorded here because the rest of the document depends on them.

1. **Sequence vs shot intent conflict → flag to Vince, never resolve.** Wired into §4f. This puts
   the workspace in the same posture as the panel reader and the continuity agent, and keeps the
   rule that nothing in Hearthlight overrules a creative decision by inference.
2. **Sequence and `beat` are the same concept.** One grouping. Wired into §4f.
3. **Design Lock is a gate.** It enters the gate ledger; `confirmed_by_user: true` is its record.
   Wired into §4g — and it collapses the escape hatch and gate reopening into one mechanism.
4. **Acceptance criteria: derivation authors, Vince edits, the reviewer consumes.
   `hearthlight-critique` does not own them.** — my call, with the reasoning below.

### Why not the critique pass

`hearthlight-critique` sits between Gate 1 and Gate 2, arguing about *story* grammar: buried
detonation beats, echo shots, close-up inflation, sentimentality. It runs before the production
object exists, so criteria it wrote would be predictions rather than tests.

The deciding constraint is mechanical. **A Required criterion must be checkable at Stage A by the
machine, which means it must resolve to a field the machine already reads** — a bound character,
a prop's `canon`, a `never[]` entry, a `staging.surfaced` value, a count. Derivation produces
exactly that because it starts from those fields. Critique produces prose, and prose is the thing
a checker cannot evaluate — which is how a Must-Preserve becomes the §16 non-goal: a constraint
nothing enforces, creating the belief that it is being honoured.

So: **derive at Design Lock, Vince edits the derived list at the same gate, and
`versioned-review.md` consumes it as the Stage A pass condition.** One author, one editor, one
consumer, no handoff.

The one thing critique *should* contribute is the Flexible list — knowing what does not matter is
its actual expertise, and getting that wrong is what produces endless iteration. Optional, and
after the derived draft exists, never instead of it.

## 20. Open questions remaining

1. **Does the hero-selection block on unmet Required criteria (§10b) apply to a dropped image?**
   A hand-made image bypasses generation entirely; blocking its promotion may be protective or may
   just be in the way.
2. **How long does `04-images/shot-targets.json` stay valid after its Vision changes?** §7 says a
   stale target must say so loudly. It does not say whether it may still govern a generation in
   flight, or must halt it.
