# Audience Context — MOVED (engine / client split)

This file used to hold Talefeather's audience research at the root of Story Studio, which meant every
Hearthlight session inherited a grieving audience whether the project had one or not. That was a
bounded-context leak: client assumptions living in the engine's constitution.

**Talefeather audience context now lives at:**
`profile/clients/talefeather/AUDIENCE-CONTEXT.md`

## The split

**Hearthlight is the engine.** A filmmaking pipeline: spoken story → outline → aesthetic bible →
conditioning stills → clips. Genre-agnostic and client-agnostic. Its laws are craft laws — gates,
no-drift, verbatim style blocks, nothing-exists-only-in-chat, the distribution spec as composition
law. None of them assume who is watching or why.

**Talefeather is one product running on the engine** — the grief / living-legacy service. Its
audience psychology, its cohorts, its pricing behavior, and its "never a generated voice" rule are
client facts, not engine facts.

## How a project declares itself

In `projects/{slug}/distribution-spec.md`:

```
format: short-film         # or: social-content, remembrance, commercial, <other>
client: none               # or: talefeather, <name>
charged_register: <what this project protects — e.g. "tenderness under a running clock">
```

`format:` is what kind of thing this is; its only wired effect is suggesting distribution defaults
(aspect, hook window, captions, sound-on assumption). `client:` tells you which profile under
`profile/clients/` to load, if any — **`none` is the normal value.** `charged_register:` tells
`hearthlight-terse` what content is emotionally load-bearing here and must never be compressed.

Current: `yugioh` → short-film / none. `mcconaughey-call` → social-content / talefeather.

A project with no client profile is normal, not broken. The engine works without one.

**Audio is not in here on purpose.** Whether a film uses real recorded VO or generated audio is a
production decision that follows available resources — confirmed per project, never systematized.
