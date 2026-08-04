# GOALS — Hearthlight's North Star

*The stable document. Changes only when Vince deliberately changes the product's direction —
never because the implementation moved. No agent may rewrite this file autonomously.*

Last human review: **2026-08-03 — Vince defined v1 (see below). Open questions 1, 3, 4 still stand.**
Derived 2026-08-03 from `AGENTS.md`, `HANDOFF.md` §1, `AUDIENCE-CONTEXT.md`, `profile/TASTE.md`.

---

## What "done" looks like for v1 — CONFIRMED by Vince, 2026-08-03

**v1 is one finished short film — the Yu-Gi-Oh! project — plus the version-one system architecture
that made finishing it possible.** Both halves, or it is not done.

Two tests, and neither alone is sufficient:

1. **The film exists.** `yugioh` is complete, from storyboard through final video output.
2. **The pipeline is established.** v1 of every skill and the system architecture that carried that
   one film end to end — a repeatable path, not a one-off rescued by manual workarounds.

**Current position (2026-08-03):** image generation. The image pipeline is being built as it runs —
**style composition → likeness → final input image**. After that, video: turning the project documents
into a working video-generation prompt, then refining that process against real output. Later, an
ElevenLabs pass for the film score.

---

## Who it is for

**Primary user: Vince, directing.** Hearthlight is a single-operator studio. Every design choice
assumes one human with taste and final say, not a team and not a self-serve consumer app.

**Beneficiary: whoever the film is for** — declared per project, never assumed. Hearthlight is the
**engine**; a *client* (e.g. Talefeather, the grief / living-legacy service) is one thing running on
it. The engine must not know or care who is watching. `client: none` is the normal case.

---

## The core problems it exists to solve

The enemy is not a competitor. It is **AI filmmaking itself** — generations that come out wrong,
prompt craft that differs per model, styles that drift, and workflows that go obsolete before
they are learned.

1. **Iteration is slow.** Generations come out incoherent or flawed. Hearthlight's UI and skills let
   the filmmaker point at what is wrong and have the prompt intelligently corrected — rather than
   rewriting it by hand and hoping.
2. **Style will not hold, and every model wants a different prompt.** Aesthetic consistency across
   shots, and descriptive prompts shaped for each image, video, and audio platform, are the two
   craft problems the generation stage actually fails on.
3. **AI output reads generic.** Authoring a film alone means doing the era research, populating the
   world, writing acting description, and holding continuity. A crew of agents supplies that
   richness in service of the filmmaker's vision, so his attention goes to the vision and not the
   atmospheric detail.
4. **Workflows live in one person's head.** A workflow that worked should be systematized into
   Hearthlight, not remembered. A workflow that failed should leave a lesson behind.
5. **The ground keeps moving.** New models obsolete old workflows. Hearthlight is expected to grow
   into new ones, **retire skills that no longer earn their place**, and adapt what remains — this
   is a goal, not maintenance.
6. **The filmmaker drifts from his own story.** As creative decisions stack, the film can wander
   from the original intent and accumulate complexity. Hearthlight holds the narrative goals and
   says so when a choice pulls away from them. *(Vince: this sentence was truncated in your draft —
   confirm the wording.)*

Hearthlight exists so that **one person with taste can make an authored film that reads as
authored** — not as plausible-generic AI gloss.

## The primary outcome

1. **Translation.** The core idea and the narrative material become a systematized set of documents.
   Hearthlight is administrator and secretary: it keeps them organized and **fetchable by agents**,
   so the filmmaker's thinking is enriched by AI input rather than buried in filing.
2. **Idea to output, without logistics.** Hearthlight owns the prompt-writing and asset-generation
   plumbing. **No more hand-typing prompts into a web UI or wiring a ComfyUI graph for every
   one-off.**
3. **Documents become prompts.** Those same documents are reformatted into what image, video, and
   audio generation each need.
4. **A visual overview of the film.** A UI showing the whole film and the current state of
   production, so the filmmaker can see where it is not working and make creative choices against
   it. This is what makes the process highly iterative.

---

## Product principles

1. **The pen stays in Vince's hand.** The machine drafts; Vince places the heart. The ambition is to
   make the big decisions *with* him, better than he'd make them alone — never to take them off his
   plate. Autonomy lives *between* gates, never *through* them.
2. **Consistency is the product, not polish on top of it.** The locked style block, the character
   signature strings, the single aesthetic source of truth — those *are* the deliverable. Drift is
   the failure mode the whole system is built against.
3. **A partner, not an intern.** It researches tirelessly, argues honestly, remembers Vince's taste,
   and pushes back when he's about to make a weaker choice. Compliance is a bug.
4. **The engine is client-agnostic.** Format, client, and charged register are *declared* by each
   project and *obeyed* by the engine. Assuming a client — especially defaulting to grief — is a
   bounded-context leak and is treated as a defect.
5. **The instruction layer gets smarter every project.** A general correction gets written back into
   the relevant skill; an aesthetic verdict gets written into `profile/TASTE.md`.
6. **Protect the charged register.** Whatever a project names as emotionally load-bearing is never
   compressed, flattened, or handled carelessly.

---

## Keeping features tight

Four questions. Ask them before building, and again before keeping.

1. **Does it fight drift or add it?** Does it strengthen the single source of truth, or create a
   second place where the same fact can be stated and diverge?
2. **Does it shift the ratio toward direction?** Does it remove mechanics from Vince's plate — or
   does it add a thing he must remember to invoke?
3. **Is there an active use case today?** Can you name the project or the moment that needed it?
   *(No → it is speculative. Speculative is allowed, but it must be labelled EXPERIMENTAL in
   `SKILL-INVENTORY.md`, not quietly absorbed into the pipeline.)*
4. **Does it survive the seam test?** The handoffs between stages break more often than the stages.
   Does this make a handoff more reliable, or add one?

**And the prior question, before all four:** does it move the Yu-Gi-Oh! film toward finished, or
harden the pipeline carrying it? If not, it is parked — not built.

---
