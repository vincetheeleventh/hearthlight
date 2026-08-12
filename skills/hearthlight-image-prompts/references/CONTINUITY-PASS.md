---
doc: CONTINUITY-PASS
role: contract
authority: canon
owner: vince
updated: 2026-08-07
answers:
  - what the film-level continuity agent is for
  - what it may report and what it may never do
not_here:
  how one prompt is written: PROMPT-AUTHOR.md
  what a drawing is authoritative for: PANEL-READING.md
---

# The continuity pass — one agent, the whole film in view

Every other reviewer in Hearthlight sees **one shot**. That is deliberate: a narrow packet
keeps an author honest and keeps a review cheap. But it makes one class of defect
structurally invisible.

Shot 1's prompt read *"a pile of Yu-Gi-Oh trading cards."* Shot 5 — which declares itself
a re-use of shot 1's setup — read *"a pile of trading cards."* Both prompts are individually
correct. The per-shot reviewer passed both, because at no point was shot 1 in the room when
shot 5 was judged. The render came back with generic cards and the error was only caught by
eye, after the spend.

**This agent exists to have both shots in the room.** It is the only agent in the system
whose packet is the whole film.

## Wide and shallow

The packet carries **every shot**, and almost nothing else: title, the still prompt, the
action prompt, bound characters, bound props, the declared setup owner. No bible. No style
block. No film laws. No Shot Visions.

That omission is the design. A packet with the bible in it invites the agent to re-litigate
creative decisions; a packet with only the shots in it can do exactly one thing, which is
notice that two shots disagree. Depth is what the per-shot reviewer is for. **Do not add
richness to this packet** — every field added makes the agent worse at its one job.

## What it reports

| Finding | Example |
|---|---|
| `prop_drift` | The same object named specifically in one shot and generically in another |
| `identity_drift` | A character described with different fixed traits across shots |
| `setup_drift` | Shots sharing a setup that describe the space differently |
| `geography_drift` | Screen direction, or left/right placement, that reverses without a cut motivating it |
| `light_drift` | Time of day or light direction inconsistent across a continuous scene |
| `binding_gap` | A shot whose prompt names a character or prop that is not bound to it in the registries |
| `count_drift` | A countable thing that changes number without an action causing it |

Every finding names **both** shots and quotes the exact disagreeing phrases. A finding
without both sides quoted is not actionable and should not be emitted.

## What it must never do

- **Never resolve.** It reports that shot 1 and shot 5 disagree. It does not decide which is
  right. That is the same posture as the panel reader, and for the same reason: the agent
  with the widest view has the shallowest context, so it is the worst-placed thing in the
  system to make a creative call.
- **Never rewrite a prompt.** No suggested replacement text.
- **Never flag intentional change.** A film is allowed to move. Light changes because time
  passes; a character's shirt changes because he changed. Where the shot text or the action
  gives a reason, there is no finding. **Deliberate contrast is the craft, not a defect** —
  if two shots are set against each other on purpose, that is a `contrast` note at most,
  never an issue.
- **Never flag wording variety for its own sake.** "A man in his forties" and "the father"
  are the same person. Prose need not be identical; **facts** must not disagree.

## Severity

- `block` — the render will be wrong. A named prop rendered generically; a character bound
  to the wrong shot.
- `warn` — probably wrong, needs a human eye. Light direction that may or may not be motivated.
- `note` — worth knowing, no action implied.

Only `block` should ever stop a batch. A continuity pass that cries `block` at variety will
be ignored within a week, and then it protects nothing.

## Where it runs

Before a render batch, on the **record** — not on rendered images. The whole point is to catch the
disagreement while a fix costs one edit instead of one regeneration.

```bash
python skills/hearthlight-image-prompts/scripts/continuity_pass.py run --project {slug}
```

Findings land in `04-images/continuity-findings.json`. They are advisory to Vince. As
everywhere else in Hearthlight, **the kill decision stays his**.
