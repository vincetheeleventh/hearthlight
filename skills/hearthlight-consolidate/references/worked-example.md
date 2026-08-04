# Worked Example — a real rant, consolidated

This is an actual free-speak rant from Vince (June 2026, spoken while designing this very system). It demonstrates the expected output. Note: this rant happens to be mostly *production asides* — that is the point of including it. The skill must route system-design ideas away from story content even when the rant contains no story at all.

## Input (rant transcript, verbatim)

> "Okay, to clarify, in the initial user rant, the free speak, uh, a lot of the seeds of the ideas are already there, some important images, some important story beats, uh, but it's all, uh, I want this part to be extremely off the cuff and improvisational and free flowing. That's the point. Unstructured to capture ideas. So maybe we add another consolidation layer between writing... between... before the AI starts writing the script. Um, the AI first collects the free thoughts of the user. This stage also requires approval. There will be ideas that will be discarded, and the purpose of this step is to be laser focused on what, um, the primary story arc is, what the vision is. Next, Hi. I forgot to mention that I also want this agentic system to handle more detailed work. And what I mean by that is, let's say, it's a story that happens in the Midwest in the seventies. The user probably doesn't know much about that era. And so the AI has to do research into what a home might look like or what the, you know, architecture there looks like, what cars people drive, etc. So that the prompts are populated with rich details"

## Output (consolidation doc)

# Consolidation Doc — system-design rant (Stage 1.5 — awaiting selects pass)

## Arc candidates
- *(none — this rant contains no story content)*

## Production asides (routed out of story)
- Rant stage must stay "extremely off the cuff and improvisational and free flowing... Unstructured to capture ideas" [rant ¶1]
- "add another consolidation layer... before the AI starts writing the script" [rant ¶1]
- Consolidation "stage also requires approval. There will be ideas that will be discarded" [rant ¶1]
- Purpose: "be laser focused on what the primary story arc is, what the vision is" [rant ¶1]
- System should "handle more detailed work": research the era/place ("Midwest in the seventies") — "what a home might look like... architecture... what cars people drive" [rant ¶2]
- Research goal: "prompts are populated with rich details" [rant ¶2]

## Tensions (yours to resolve)
1. A: input must be "unstructured... free flowing" [rant ¶1] — vs — B: output must be "laser focused" on one arc [rant ¶1]
   *(Surfaced, not resolved. Vince resolved it by sequencing: freedom at capture, focus at the gate.)*

## Open questions
- Who performs era research when the user DOES know the era — skip or confirm? [gap noticed, not filled]

## What the skill did right here
- Quoted, did not paraphrase ("laser focused", "off the cuff" kept verbatim).
- Routed every item to Production asides instead of inventing a story around "Midwest in the seventies" (which is an *example* inside a system idea, not a story beat).
- Surfaced the freedom-vs-focus tension without resolving it.
- Wrote the noticed gap as an Open Question instead of answering it.
