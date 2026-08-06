---
name: hearthlight-acting
description: >
  Hearthlight performance writing — how to get a living performance out of a video model.
  Behaviour instead of emotion, muscle instead of adjectives, a locked master profile per character
  adapted per scene, and the eye-life rules that separate a living face from a dead one. Cross-cutting:
  used by both WF-A and WF-B, at Stage 5 (storyboard motion intent) and Stage 6 (video prompts).
  Use when writing any prompt in which a character acts, or when a generation comes back stiff,
  blank-faced, or emotionally flat.
---

# hearthlight-acting — writing a living performance

Adapted for Hearthlight from an outside production practice. Model-agnostic: written against
Seedance 2.0 but the craft holds for any video model that takes a text prompt.

**Owns:** how performance is written into a prompt.
**Does not own:** the prompt skeleton (`hearthlight-video-prompts`), the look
(`hearthlight-mise-en-scene`), or who a character *is* (`hearthlight-character` — this skill writes
how they *behave*).

---

## The one rule

> **Write behaviour, not feelings.**

Emotion words — "sad", "angry", "shocked" — make the model improvise, and it improvises shallow. A
living scene is a character who **wants something**, something **in the way**, and who **acts to get
it**. The emotion is a by-product of that fight, and it arrives on its own.

Give the model a goal and an obstacle, and change how the character fights across the shot: he jokes
→ it fails → he pushes → it fails → he begs. **Every change is a visible event** — a pause, a
posture shift, a tempo change. A character who does one thing all the way through plays flat.

## The five pillars

Every character in every scene decomposes into five things. Miss one and the performance falls apart.

1. **Objective** — what they want, *right now*, *from a specific person*. Always a verb aimed at the
   partner: *make him confess*, *beg a week's extension*. Never a state — "be angry" cannot be
   played.
2. **Obstacle and stakes** — what prevents it, external or internal. Answer *"what happens if I do
   NOT get it?"* The answer must frighten the character.
3. **Tactics** — the method being used right now: press, charm, shame, plead, provoke, bargain,
   stall. When a tactic fails a living person **changes it**. One tactic for a whole scene is dead
   acting.
4. **Beats** — the stretch during which they want one thing and pursue it one way. A beat ends when
   the objective lands, the tactic fails, new information arrives, or power shifts. **2–4 beat
   changes** in a good scene, each visible in the body.
5. **Subtext** — what they actually mean versus what they say. Not performed; it leaks when the
   character plays the true objective while speaking the false text. Buildable markers: questions
   that aren't questions, repetitions, abrupt topic changes, jokes at the wrong moment, answers that
   are too short.

## Write muscle, not adjectives

For anything deeper than a surface reaction, describe the **work of the body**: a tremble, a jaw
clenched and flexing, cheekbones drawn tight, a light exhale through the nose. Then add intention —
one line of inner monologue per stretch of action, marked `INNER (unspoken)`.

**Phased blinking** is the cheapest sign of a living face:
`one lazy blink → a quick DOUBLE-BLINK → one HARD reset-blink`.

**Micro-life rule** — against frozen faces in static shots: one visible micro-event every one or two
seconds. The breath lifts the chest, a nostril moves, a brow tenses and releases.

**Describe stillness as held tension, never as a freeze.** Calming phrases — "nobody moves", "they
stand still" — freeze the frame themselves.

## Eye life — mandatory, every character, every shot

Dead eyes are the number-one tell of AI-generated acting.

- **Gaze targeting and micro-saccades.** The gaze keeps moving — drifts, flicks away in thought,
  scans to a detail and settles back. Never locked frozen on one point.
- **Blink rate tied to state.** Rapid bursts under stress; slow calm lids in control; a
  blink-and-glaze on dissociation.
- **Live catch-lights.** Even dark eyes need a small reflection in the pupil. Without it the face
  reads dead, and no model can act with a dead face. *Check this on the character sheet too — a
  sheet with dead eyes poisons every clip made from it.*
- **Controlled stillness is chosen, never dead.** A near-unblinking predator calm keeps blinks rare,
  slow and deliberate — a decision, not a freeze — and the gaze still shifts with intent.
- **Eyes lead the thought.** The eyes reach the target a touch before the head turns.

## Three things that separate a living shot from a dead one

1. **The reaction starts before the line ends.** A listener gets the point mid-sentence and the face
   already answers. A neutral face until the partner finishes, then "switching on", is dead acting.
2. **Emotion does not switch off instantly.** After a heavy moment the breath is still uneven, the
   hands not yet steady. That tail carries into the next clip and stitches the cut.
3. **Keep the hands busy.** A character does not "have a conversation" — he fixes, counts, pours, and
   talks over it. **The strongest accent in a scene is the moment he stops that work** because of
   what he just heard.

## The master profile

Every recurring character gets **one** profile — the permanent source of truth for how they behave.
Written once, then **adapted per scene, never pasted**. 150–220 words, one paragraph, entirely
observable and filmable.

Lives at `projects/{slug}/03-bible/characters/{name}/ACTING.md`, beside the `CHARACTER.md` dossier
that `hearthlight-character` owns.

```
Character acting as [NAME]. [Age-free physical description: build, physique, posture — the body as
a document of their biography]. [The psychological engine in one clause — the drive that explains
the physicality]. Vocal profile: [pitch/timbre, accent/origin, pace and delivery, and how the voice
breaks under emotion]. Key physical habits and tics: [signature tic + its trigger; stress tic + its
trigger; concealment behaviour; the facial mask and the exact condition under which it cracks].
Walking style: ["named" gait, then unpacked — weight, rhythm, foot placement, what torso and arms
do]. However, when [emotional trigger], [the transformation — how posture, gait and face change].
[Optional: the one person or thing that makes the face genuinely soften].
```

**Rules:**

- **Only observable behaviour.** Never "he is nervous" — write the trembling lower lip, the heavy
  swallow, the long inhale through the mouth and sharp exhale through pursed lips.
- **Every tic has a trigger.** Not "he cracks his knuckles" but "he cracks his knuckles during
  mundane conversation to fake confidence". Tics without triggers are decoration.
- **Name the gait.** A coined name in quotes anchors the biomechanics — a "battering-ram stride", a
  "gallery walk" — then unpack it.
- **Build in the mask AND the crack.** Every profile carries at least one *"However, when X —"*
  clause. A character playing two truths at once is the difference between a puppet and a person.
- **One softening target.** Exactly one person, animal or object the face genuinely softens for.
  One, not two.
- **No wardrobe.** Costume lives in the scene block; the profile must survive a costume change.
- **No camera, no colour.** Acting drives performance, face, voice and motion only.
- **Physique carries biography.** Profession, past injuries and self-image should be readable in the
  build and posture.
- **Never write age, in any language.** Content filters tighten sharply the moment they read a minor.
  Give role, clothing and action instead.

## Voice is locked, never adapted

Lock every character's voice in pre-production, before any dialogue: register, tempo, accent, manner.
The voice descriptor is pasted into the audio field **verbatim, every time they speak**, and never
changes.

```
Voice: deep, gravelly bass-baritone; slow, calculated pacing; London street accent;
menacing calm — he never raises his voice.
```

Stress-test it the same way as the look: if it drifts between generations, the wording is not locked
hard enough.

Note: this concerns **generated** character voices. Whether a Hearthlight project uses real recorded
VO or generated audio is a per-project production decision — ask, note it, never silently flip it.

## Writing a dialogue line

Always the same four parts, in order:

**voice + emotion → the line in quotes → the physical action → the facial reaction**

- **Speech lives only in the audio section.** Not one word of dialogue inside the action block.
- **Hard block on invention:** everyone speaks ONLY the line in quotes; whoever has no line stays
  completely silent. Models love to add their own "uhm"s, chuckles and whole phrases.
- A "half-laugh" written in the action is a **facial expression with no sound** — say so explicitly.
- **Write the mix:** voices clean and close to the mic, ambience underneath, ambience dipping when
  someone speaks.
- **Rare names get a transcription** or the model mangles them.
- **Stitch the seams:** feed the tail of the previous clip's line into the first second of the next,
  and open a new generation with the line that closed the last one. The emotion crosses the cut with
  the text.

## Scene adaptation

The master profile is the source; each scene gets it **rewritten to the moment's posture and
action** — never pasted whole.

**A behaviour physically impossible in a scene is transferred, not deleted.** A pacer sat down on a
sofa keeps the same energy in swaying, finger-tapping and jagged gestures.

## Atlas of bad acting — diagnose before re-rolling

| Symptom | Cause | Fix |
|---|---|---|
| Blank, waxy face | Emotion words instead of muscle | Rewrite as physical work + `INNER` line |
| Dead eyes | No catch-light, no gaze plan | Add catch-lights, gaze targets, phased blinking |
| Flat scene, nothing develops | One tactic throughout | Add a beat change with a visible event |
| Actor "switches on" after the line | Reaction written after the cue | Start the reaction mid-partner-line |
| Frozen frame in a static shot | "Nobody moves" in the prompt | Held tension + one micro-event per 1–2s |
| Emotion snaps off between clips | No tail | Carry uneven breath and unsteady hands across the cut |
| Model invents dialogue | No speech block | Hard block: only the quoted line, others silent |
| Talking heads, no life | Hands unoccupied | Give a physical task, and stop it on the key line |

## Pre-send checklist

- [ ] Objective is a verb aimed at a person, not a state
- [ ] Obstacle named, and the stakes would frighten the character
- [ ] At least one visible beat change
- [ ] Emotion expressed as muscle, not adjectives
- [ ] One `INNER (unspoken)` line per stretch of action
- [ ] Eye life: gaze plan, blink phasing, catch-lights
- [ ] Micro-event every 1–2 seconds in any static shot
- [ ] Voice descriptor verbatim from the lock
- [ ] Speech only in the audio block; silence enforced for everyone else
- [ ] No age written anywhere
- [ ] Stillness written as held tension, never as a freeze
