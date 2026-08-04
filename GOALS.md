# GOALS — Hearthlight's North Star

*The stable document. Changes only when Vince deliberately changes the product's direction —
never because the implementation moved. No agent may rewrite this file autonomously.*

Last human review: **NEVER — awaiting Vince's first ratification.**
Derived 2026-08-03 from `AGENTS.md`, `HANDOFF.md` §1, `AUDIENCE-CONTEXT.md`, `profile/TASTE.md`.

---

## Who it is for

**Primary user: Vince, directing.** Hearthlight is a single-operator studio. Every design choice
assumes one human with taste and final say, not a team and not a self-serve consumer app.

**Beneficiary: whoever the film is for** — declared per project, never assumed. Hearthlight is the
**engine**; a *client* (e.g. Talefeather, the grief / living-legacy service) is one thing running on
it. The engine must not know or care who is watching. `client: none` is the normal case.

> ⚠️ **NEEDS VINCE** — Is Hearthlight ever intended to be operated by someone other than Vince
> (a hired editor, a second director, a customer)? Every "the machine drafts, Vince approves" law
> assumes not. If the answer is yes, the gate protocol needs a role model it does not currently have.

---

## The core problem it exists to solve

Two problems, stacked:

1. **Generic output.** Competing "record your parent's story" services produce work their own
   customers describe as *"a list of answers, not a story"* and *"every book looks the same."*
   They capture facts and flatten the texture that made the person specific.
2. **The crew Vince doesn't have.** Making an authored film alone means the era research, world
   population, prompt assembly, continuity holding, and honest critique either don't happen or eat
   the time that should go to direction.

Hearthlight exists so that **one person with taste can make an authored film that reads as
authored** — not as plausible-generic AI gloss.

## The primary outcome

A finished illustrated narrative film that **feels like the person who made it and the person it is
about**, produced with Vince's time running roughly **80% direction and approval, 20% mechanics.**

If that ratio inverts, the instruction layer is wrong — not the operator. That inversion is the
single clearest signal the product is failing.

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
5. **Nothing exists only in chat.** Every artifact lands on disk in the project.
6. **Gates fail cheap; skipping them fails expensive.** A wrong call caught at the outline costs a
   paragraph. Caught at Stage 6 it costs paid renders.
7. **The instruction layer gets smarter every project.** A general correction gets written back into
   the relevant skill; an aesthetic verdict gets written into `profile/TASTE.md`.
8. **Protect the charged register.** Whatever a project names as emotionally load-bearing is never
   compressed, flattened, or handled carelessly.

---

## Explicit non-goals

- **Not a render farm.** Throughput is not the metric.
- **Not an app that spits out a video.** No one-click path from recording to film; the gates are the
  point, not friction to be optimized away.
- **Not autonomous creative judgment.** The system never fills a charged slot, never advances a gate,
  never decides story, feeling, visual grammar, or shot selection.
- **Not a multi-tenant SaaS product.** Hearthlight is one operator's studio. Talefeather may be a
  commercial service, but *the engine* is not the thing being sold.
- **Not a systematizer of everything.** Real vs. generated VO is deliberately left as a per-project
  production decision. Some choices are meant to stay human and unautomated.
- **Not a documentation project.** Governance exists to expose drift, not to accumulate Markdown.

---

## Does this feature advance the North Star?

Ask in order. A "no" at 1 or 2 is disqualifying regardless of how good the idea is.

1. **Does it protect the pen?** Does it leave every charged decision with Vince, or does it quietly
   make one for him? *(Fails → reject, however convenient.)*
2. **Is it engine-level or client-level?** Does it hold for a project that declares
   `client: none` — or does it smuggle in an audience? *(Client-level → belongs in
   `profile/clients/{client}/`, not in a skill.)*
3. **Does it fight drift or add it?** Does it strengthen the single source of truth, or create a
   second place where the same fact can be stated and diverge?
4. **Does it shift the ratio toward direction?** Does it remove mechanics from Vince's plate — or
   does it add a thing he must remember to invoke?
5. **Is there an active use case today?** Can you name the project or the moment that needed it?
   *(No → it is speculative. Speculative is allowed, but it must be labelled EXPERIMENTAL in
   `SKILL-INVENTORY.md`, not quietly absorbed into the pipeline.)*
6. **Does it survive the seam test?** The handoffs between stages break more often than the stages.
   Does this make a handoff more reliable, or add one?

---

## Open North Star questions

These cannot be answered from the repository. They shape everything downstream and are the highest-value
thing Vince can resolve.

> ⚠️ **NEEDS VINCE — 1. Is the deliverable the film, or the engine?**
> `HANDOFF.md` frames success as the McConaughey pilot proving craft. `AUDIENCE-CONTEXT.md` frames
> Hearthlight as reusable infrastructure with clients on top. These imply different priorities: the
> first says finish one film; the second says make the second film cheaper than the first. Both are
> being built simultaneously and they compete for the same hours.

> ⚠️ **NEEDS VINCE — 2. What does "done" look like for v1?**
> No success criteria exist anywhere in the repository. Without one, no checkpoint can honestly say
> whether work is converging. A single sentence would fix this — e.g. *"v1 is done when one complete
> film has passed every gate without a manual workaround."*

> ⚠️ **NEEDS VINCE — 3. Is Talefeather the only client, or the first of several?**
> The engine/client split was built to support many. Only one exists. If Talefeather is in fact the
> only intended client, the split is speculative architecture and several abstractions could collapse.

> ⚠️ **NEEDS VINCE — 4. Does the product have a commercial shape?**
> `HANDOFF.md` cites competitors and pricing behaviour, implying a business. Nothing else in the
> repository reflects one. If Hearthlight is commercial, non-goal "not multi-tenant SaaS" may be
> wrong; if it is personal, the competitive framing should stop influencing craft decisions.
