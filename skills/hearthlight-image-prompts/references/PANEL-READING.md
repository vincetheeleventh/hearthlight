# Panel Reading — the vision pass over the hand-drawn board

A drawing states framing, blocking and eyeline faster and more precisely than prose. It is the
densest thing Vince makes, and until now the prompt author could not see it.

This contract governs a **vision-model pass** that reads a panel and reports what it observes, so
the author (`PROMPT-AUTHOR.md`) composes with the drawing in hand.

**One job:** describe what the drawing shows, at the right level of confidence, in the author's
vocabulary. Do not write the prompt. Do not resolve conflicts. Do not invent.

---

## Where the drawing sits in the authority order

`PROMPT-AUTHOR.md` § Authority is unchanged. The panel reading enters at **tier 3 — storyboard
frame-one, camera and Notes as baseline execution evidence.**

> **The panel is baseline evidence, never a vote against the current Vision.**

This is the rule the whole pass depends on. A rough sketch is easy to over-trust because it is
concrete and visual, while a Vision is abstract and textual. **Concreteness is not authority.**

When the panel and the latest Shot Vision disagree, the Vision wins and the displaced panel fact is
named in `supersedes` — never averaged, never quietly dropped. A newer Vision may deliberately
replace an overhead with an oblique view, remove a person from frame one, or re-frame entirely.
Those are directions, not ambiguities.

`yugioh` shot 8 is the live case: its `storyboard_reference` reads *"panel re-purposed — Amendment
01."* The drawing is from a different intent. Read it, report it, and let the Vision govern.

---

## What the drawing IS authoritative for

These are the things a sketch conveys reliably, and where it should inform the prompt:

| Property | Read it as |
|---|---|
| **Framing and crop** | How close, and what the frame cuts off. A hand entering from the bottom edge is a crop decision |
| **Blocking** | Who is where in the frame, and their spatial relationship to each other |
| **Screen geography** | Frame-left / frame-right / foreground / background. The camera's side of the room |
| **Eyeline and gaze direction** | Where a figure looks, and whether looks meet |
| **Scale in frame** | How large a figure sits in the frame — the composition-as-argument layer |
| **Inclusion and exclusion** | What is deliberately *out* of frame. Often the most important thing a board says |
| **Posture and body attitude** | Hunched, planted, turned away — the gross shape, not the detail |

## What it is NOT authoritative for

A sketch is silent on these, and silence must never be read as instruction:

- **Wardrobe detail, colour, and palette** — the bible owns these
- **Light quality, direction and colour** — unless the panel explicitly draws a light source
- **Texture, rendering, medium** — the locked style block owns this absolutely
- **Facial likeness and identity detail** — the character record owns this
- **Period and prop specifics** — research and the mise-en-scène own these
- **Anything requiring a name** — a drawn figure is "a figure" until a source names them

### The blank-face rule

**Absence of detail in a sketch is not a direction.** A stick figure with no face does not mean
"render a faceless person." A panel drawn without a background does not mean "white void." An
unshaded panel does not mean "flat light."

Report absence as absence — `not depicted` — never as a positive instruction. This is the single
most likely way a rough board corrupts a prompt.

---

## Shared and missing panels

- **A panel may serve several shots.** `yugioh` shots 2 and 3 share panels 1–2. **Read per shot, not
  per panel:** the same drawing answers different questions for different shots, and the shot's own
  Vision decides which part of the drawing is load-bearing.
- **A shot may have no panel.** Several `yugioh` shots read *"no panel — shot added after boards."*
  That is normal and not a blocker. Report `panel: none` and let the author work from text.
- **A panel may be re-purposed.** Read it, flag the mismatch, and defer to the Vision.

---

## Output

Strict JSON. No prose outside it.

```json
{
  "shot": "8",
  "panels": ["board-panel-06.heic"],
  "framing": "medium close-up; frame cuts at mid-chest",
  "blocking": "single figure centred, angled to frame-left",
  "screen_geography": "door frame-left, off-frame; figure faces it",
  "eyeline": "down and away from camera, toward the lower frame edge",
  "scale_in_frame": "figure occupies roughly the central third",
  "excluded": ["the second figure", "the floor beyond the near edge"],
  "posture": "hunched forward over the hands",
  "not_depicted": ["wardrobe detail", "light source", "background"],
  "conflicts_with_vision": [
    { "panel_shows": "one figure alone",
      "vision_states": "father enters at 1.5s",
      "resolution": "Vision governs; panel predates Amendment 02" }
  ],
  "confidence": { "framing": "high", "eyeline": "medium", "posture": "low" },
  "blockers": [],
  "warnings": ["panel is re-purposed per storyboard_reference"]
}
```

### Confidence is required, per observation

`high` — unambiguous in the drawing. `medium` — legible but interpretable. `low` — a guess from a
rough mark.

**The author must treat `low` as absent.** A confidence field that is always `high` means the pass
is not doing its job; a rough sketch produces low-confidence readings and saying so is the value.

### Conflicts are reported, never resolved

The pass **names** the disagreement and states that the Vision governs. It does not rewrite either
side. Resolution belongs to the author, under the authority order; escalation belongs to Vince.

---

## What this makes possible

Not just a better prompt — a **script supervisor**. With the panel readable and adjacent shots in
the packet, the system can say things it previously could not:

- *"Shot 7 has the father entering frame-right; shot 8's panel puts him frame-left. One of these
  crosses the line."*
- *"Your Vision says his hands stay below frame. The panel draws them in shot."*
- *"Three consecutive panels are the same framing. Shot 12 was meant to be the register change."*

**A flagged contradiction is worth more than a fluent prompt.** The prompt can be regenerated for
pennies; a continuity error found after twenty clips are rendered cannot.

---

## Self-audit before returning

- [ ] Every observation is something visible in the drawing, not inferred from the text
- [ ] Absence recorded as `not_depicted`, never as a positive instruction
- [ ] Confidence assigned per observation, and genuinely varied
- [ ] Conflicts named with both sides quoted, and the Vision stated as governing
- [ ] Nothing about colour, texture, medium, likeness or period asserted
- [ ] No prompt text written — that is the author's job, not this pass's
