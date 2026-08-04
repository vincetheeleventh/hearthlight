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

1. **Iteration speed** - Often ai image and video generations come out incoherent or flawed. Hearthlight's UI and agent skills allow user to quickly point out things to fix, intelligently tweaks the prompt to rectify this.
2. **Systematic workflow** - Establish a repeatable workflow that is ai assisted, solving current issues with AI filmmaking 
3. **Avoid AI genericness.** Making an authored film alone means the era research, world population, prompt assembly (especially acting descriptions), continuity holding, etc. A crew of agents handle the research and richness of details that support the filmmaker vision, reducing their workload in establishing atmospheric details.
4. **Solve current AI video generation issues** 
   1. achieving aesthetic style consistency
   2. writing good descriptive prompts for different image/video generation platforms
5. **Adapts to new AI advances** - New models come out, making older workflows obsolete. The Hearthlight system will grow with these new workflows, retiring old workflows and skills, and adapting its existing system to work with new models.
6. **Vince is free to experiment with workflows** - A successful workflow is not lost, its systematized into Hearthlight. Lessons are drawn from unsuccessful workflows.
7. **User drift** - As creative decisions stack, user may drift from the original story, or creep in complexity. Hearthlight tracks key narrative goals, and reminds user when 

Hearthlight exists so that **one person with taste can make an authored film that reads as authored** — not as plausible-generic AI gloss.

## The primary outcome

1. Hearthlight handles the Translation from the core film idea, the narrative ideas into a systematized collection of documents. It serves both as an administrator and secretary, and keeps all these documents organized and easily fetchable by AI agents so that the user can be enriched with AI input and ideas.

2. It makes it extremely easy for the user to go from idea to output, Hearthlight taking care of the prompt-writing and asset generation logistics. No more manually typing prompts in a webUI, creating comfyUI graphs for each one-off usecase, etc.

3. It takes these documents and then also processes them to be reformatted for use for image generation and video generation and audio generation

4. It provides a visual UI for the filmmaker to  see an overview of the film that they're making, the current state of production. This helps the user make creative choices and see where the film is not working, allowing a highly iterative process.

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



1. **Does it fight drift or add it?** Does it strengthen the single source of truth, or create a
   second place where the same fact can be stated and diverge?
2. **Does it shift the ratio toward direction?** Does it remove mechanics from Vince's plate — or
   does it add a thing he must remember to invoke?
3. **Is there an active use case today?** Can you name the project or the moment that needed it?
   *(No → it is speculative. Speculative is allowed, but it must be labelled EXPERIMENTAL in
   `SKILL-INVENTORY.md`, not quietly absorbed into the pipeline.)*
4. **Does it survive the seam test?** The handoffs between stages break more often than the stages.
   Does this make a handoff more reliable, or add one?

---
