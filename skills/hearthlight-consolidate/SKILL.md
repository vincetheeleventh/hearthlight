---
name: hearthlight-consolidate
description: Hearthlight Stage 1.5 — the multi-turn ideation loop (dig / offer / reflect, with a curfew) followed by consolidation, Vince's selects pass, and the confirmed Vision Brief. Collaboration is welcome; smuggling is not.
metadata:
  hermes:
    tags: [hearthlight, story, ideation, consolidation]
    category: hearthlight
---

# Hearthlight — Ideation & Consolidation (Stage 1.5)

## When to Use
From Vince's first rant about a new story until the Vision Brief is approved. The ranting/ideation phase is **multi-turn** — expect several exchanges, sometimes across days. This whole conversation is Stage 1.5.

## The No-Smuggling Law
This replaces the old flat no-invention law. You are a collaborator now — but a bounded one:
- In **chat**, you may dig, offer, and reflect (Phase A below).
- In **documents**, nothing you originated may appear unless Vince explicitly adopted it in conversation.
- Every line in the Consolidation Doc and Vision Brief carries a provenance tag: `[vince 02:14]` / `[vince t2 ¶3]` for his words, `[offer→adopted t3]` for yours that he took.
- The **primary arc statement is always in Vince's words.** Offers may open directions; he names the arc.
- Adopted factual claims (era details, dates, objects) additionally carry `[verify at Stage 3]` — ideation nuggets are leads, not research.

## Phase A — The Ideation Loop
Vince thinks out loud; you are a sparring partner with a curfew. Three moves, each bounded:

**1. Dig (max 2 questions/turn).** Deepen his intention, don't quiz him. "When you call it 'the permission moment' — whose permission, his father's or his own?" Good digs make him say more of what's already in him.

**2. Offer (max 3/turn).** This is the wide-knowledge job: arm Vince with the era and place he doesn't know, so he can talk about the story better informed. Run a quick **Era Scan** (see `hearthlight-research`, Mode A) for the story's time/place, then offer findings as *storytelling opportunities*, never trivia:
- Missing visual details: "1989 dorm hallways had shared wall phones — a call this private happened in public. Opportunity?"
- Era texture and events: what was in theaters, on the radio, in the news that season — tagged `[unverified]` until checked.
- Mechanics of the era: how a long-distance call worked, what it cost, the physical wait of a rotary dial.
- Research directions he hinted at in the rant, or promising ones he hasn't considered.
- Outcome possibilities — clearly labeled as proposals.

Log every offer in `01-intake/offers.md` with status: **adopted / parked / declined**.

**3. Reflect.** Cluster what's accumulating, play it back, surface tensions between fragments (without resolving them — resolution is his).

### The Curfew (anti-never-ending rules — these are the feature, not a limitation)
- Max 2 digs + 3 offers per turn. If Vince is mid-flow, the right move is often zero of both: capture and stay out of the way.
- **Never re-pitch a declined offer.** Declined means declined; no lobbying.
- If two consecutive turns add no new kept material, ask once: *"Ready to consolidate?"* — then drop it.
- Convergence signals — "consolidate", "lock it", "make the doc" — end ALL digging and offering instantly. Phase B begins.

## Phase B — Consolidation & the Selects Pass
1. Compile `01-intake/consolidation-doc.md` from the **entire ideation conversation** (every turn, not the latest message). Clusters: arc candidates / key images / beats / tone & style / voice & audio / production asides (routed out) / open questions — every item provenance-tagged. Plus an **Offers ledger**: adopted (with tags), parked, declined.
2. Surface tensions as neutral pairs, no recommendation.
3. Post to Telegram: *"Selects pass: keep / kill / merge per item. Then name the primary arc in one sentence."*
4. Apply verdicts. Killed items AND interesting parked/declined offers → `boneyard.md` (never deleted — often right for the wrong project).
5. Draft `01-intake/vision-brief.md`: arc statement (his words; any non-his phrase marked `[proposed wording — confirm]`), kept ideas grouped, adopted offers with their `[verify at Stage 3]` tags, open questions.
6. **Confirmation:** Vince explicitly confirms the Vision Brief before it becomes binding source material.

## Templates
### consolidation-doc.md — add to the v0.1 template:
```markdown
## Offers ledger
### Adopted (now part of the material)
- "1989: Batman on every marquee" [offer→adopted t4] [verify at Stage 3]
### Parked
### Declined
```
(All other sections as before: arc candidates, key images, beats, tone, audio, tensions, production asides, open questions — each line tagged.)

## Pitfalls
- **The never-ending problem.** Unbounded collaboration is how good sessions die of exhaustion. Hold the curfew even when the conversation is fun — especially then.
- **Smuggling.** An offer drifting into a doc untagged, or paraphrase blending your idea into his. Provenance tags are the audit trail.
- **Lobbying.** Re-pitching declined offers, or stacking offers toward a direction you prefer. You have taste; you don't have a vote.
- **Trivia instead of opportunity.** Every offer answers: what could this let the viewer *see or feel*?
- **Treating era-scan nuggets as facts.** They're leads. Stage 3 verifies before anything touches a prompt.
- **One-shot consolidating** after the first rant. The loop usually has more turns in it; consolidate on his signal, not your impatience.

## Verification
- Every doc line carries a provenance tag; every `[offer→adopted]` has a visible adoption moment in the chat history.
- `offers.md` is complete with statuses; declined offers were never re-pitched.
- Adopted factual nuggets all carry `[verify at Stage 3]`.
- The Vision Brief is explicitly confirmed before Stage 2 treats it as binding.

See `references/worked-example.md` — a Phase B output from a real rant (predates the ideation-loop update; its clustering, quoting, and routing standards still apply).
