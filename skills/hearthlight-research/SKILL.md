---
name: hearthlight-research
description: Hearthlight world & period research — build the sourced Research Deck that feeds period-true detail into prompts, and the family-questions list that turns uncertainty into interview material. Research populates the world, never the story.
metadata:
  hermes:
    tags: [hearthlight, research, period-detail, family-questions]
    category: hearthlight
---

# Hearthlight — World & Period Research

## When to Use
Two moments: during the **ideation loop** (Stage 1.5, Mode A) and during **Mise-en-scène work** (Stage 3, Mode B) — or whenever a prompt needs a period detail the deck doesn't yet hold.

## Mode A — Era Scan (Stage 1.5 ideation support)
A fast, breadth-first sweep of the story's time and place, run early so Vince talks about the story *better informed* — the goal is to place the viewer in an era Vince doesn't know, and that starts with placing Vince there.
- Sweep for: what was in theaters/on radio/in the news that season; the domestic objects of the year; public spaces; the *mechanics* of era life (how a long-distance call worked, what it cost, the physical wait of a rotary dial); light and color of the period.
- Be **proactive**: surface promising directions Vince hasn't asked about, and chase ones he hints at in the rant.
- Output: short findings framed as *storytelling opportunities*, delivered as offers through the ideation loop (see `hearthlight-consolidate` — its curfew and no-smuggling law govern delivery). Log the sweep to `01-intake/era-scan.md`.
- Tag everything not instantly sourced `[unverified]`. Era nuggets are seductive and often wrong-by-one-decade — the kind of error only verification catches.
- Mode A findings adopted by Vince enter Mode B's scope tagged `[verify at Stage 3]`: confirmed, corrected, or cut before any prompt may use them.

## Mode B — Research Deck (Stage 3, component 4)
The full sourced deck, built during Mise-en-scène work as below.

## The two laws
1. **Research populates the world, never the story — in documents.** In the ideation *chat*, research may point at story possibilities (that's Mode A's job: informing the teller). But research findings enter documents and prompts only as world — what things LOOK like — never as events, dialogue, or character choices. Story authorship runs through Vince's adoption, governed by the no-smuggling law in `hearthlight-consolidate`.
2. **Sourced, not hallucinated.** Every claim in the deck carries a source (URL or named reference) gathered by actual web research, with reference images saved to `03-bible/refs/` — **named per the Reference Naming Law and logged in `refs/REFERENCE-MANIFEST.md` (`hearthlight-conventions`). Rename on arrival; a source-site filename never lands on disk.** Record the licence per file; never assume it. Plausible-but-wrong period detail is a landmine, because the family are the world experts on the setting — grandma knows exactly what her kitchen looked like. Research gets to *plausible*; only the family gets to *true*.

## Procedure
1. **Scope from the outline docs.** List the period/place questions each beat actually raises (a phone-call story needs telephones, booths, the house's hallway — not the entire 1970s).
2. **Research by category** — for each: 3–6 specific findings, each with source + saved reference image where possible. **Write the finding even when no image can be obtained** — a prompt states facts in words, so "what the drawing must get right" (pattern, cut, colour, and especially *what the subject is NOT*) is usable immediately and beats a missing image. Log it against a `GAP` row in the manifest. Categories:
   - Architecture & interiors (house styles, wall colors, flooring, fixtures)
   - Objects & technology (the phone itself: model, mounting, cord length; appliances)
   - Vehicles
   - Clothing & grooming (per character's age/class/region)
   - Signage, typography, packaging (the only legitimate source for any rendered text)
   - Light (fixture types, color temperature of the era's bulbs, streetlight character)
3. **Confidence-tag every finding:** `[verified]` (multiple sources) / `[likely]` (single source) / `[uncertain]` (educated inference — must become a family question).
4. **Write `family-questions.md`:** every `[uncertain]` and every detail the family could personalize, phrased as warm, specific, answerable questions ("Did he drive a Ford or a Chevy?" "Was the phone in the kitchen or the hallway?"). This file doubles as an interview supplement — the research process deepening the relationship instead of replacing it. For the pilot (public figure, no family access), answer from the published record where possible; otherwise mark `[stylized choice — Vince decides]`.
5. **Compile `03-bible/research-deck.md`** organized by category, findings + sources + image refs, family questions cross-referenced.

## How the deck feeds prompts
- Stage 4 pulls named objects and light character from the deck — never from imagination. A prompt detail with no deck entry and no beat/bible source gets cut or researched.
- **Every detail earns its place**: researched texture serves the beat's emotional job. The deck is a pantry, not a checklist — no beat should read like an inventory of the era.

## Pitfalls
- Inventing events while researching ("phones had party lines, so maybe a neighbor overheard—" NO. World, not story).
- Unsourced "period flavor" from the model's priors dressed up as research.
- Letting research bloat: scope is set by the beats, not curiosity.
- Family questions phrased as fact-checking interrogation instead of invitation to remember.

## Verification
- Every deck entry: source + confidence tag.
- Every `[uncertain]` has a corresponding family question.
- No deck entry describes an event, choice, or line of dialogue.
