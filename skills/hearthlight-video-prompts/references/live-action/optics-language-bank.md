# Optics language bank

> ## ⚠️ MEDIUM WARNING — READ BEFORE PASTING ANYTHING FROM THIS FILE
>
> **This practice was built for photoreal 8K live-action. Hearthlight films are painted.**
>
> `yugioh`'s locked style is *"confident dark ink linework, soft flat colour washes, minimal detail,
> cozy warm palette, background dissolving to clean white."* An ink-and-wash illustration has **no
> bokeh, no chromatic aberration, no razor-thin focus plane, and no lens.** Pasting these blocks
> verbatim into a painted shot is a direct invitation to photoreal creep — the exact failure
> `hearthlight-video-prompts` carries a preservation clause to prevent, and the one thing Vince
> watches for during clip review.
>
> **Use the lens blocks only where the film's locked style is photographic.** Otherwise take the
> *framing logic* — how close, how much environment, how isolated the subject — and express it in
> the film's own vocabulary:
>
> | Photoreal phrasing | Painted equivalent |
> |---|---|
> | creamy bokeh, background dissolved | background washes out to clean white at the edges |
> | razor-thin focus isolates the eyes | linework tightens on the face, everything else loses line |
> | background compressed flat behind subject | flatter colour field behind the figure, fewer layers |
> | chromatic aberration near frame edges | *(drop it — this is a lens artifact)* |
> | 180° shutter motion blur, atmospheric haze | *(drop both)* |
> | pore-level skin, vellus hair, capillary flush | *(drop — fights "minimal detail")* |
>
> **The FOV numbers and camera distances still work** — they control how much world is in frame,
> which is medium-independent. The optical *texture* language does not.

Ready-to-paste lens blocks and the decision tree behind them. Adapted for Hearthlight from an
outside production practice, platform-specific references removed.

**The premise:** video models respond to observable lens *results*, not to camera metadata. Avoid
millimetres, f-stops, ISO, lens brands and vintage model names as primary control. Control with
**diagonal field of view + physical camera distance + visible optical outcome.**

---

## Lens decision tree

Choose silently, before writing, based on what the beat actually contains.

**Face and portrait**

| Content | Lens |
|---|---|
| Close intimate face with environment visible | 84° intimate-wide |
| Medium portrait | 29° short telephoto portrait |
| Tight emotional close-up | 18° classic telephoto |
| Distant hidden observation | 8° super-telephoto with foreground occlusion |

**Environmental action**

| Content | Lens |
|---|---|
| Natural documentary action | 47° standard normal |
| Wide environmental action | 84° classic wide |
| Large-scale environmental geography | 107° wide rectilinear |

**Detail and macro** — 29° or 18°. Give it its own insert beat; do not mix macro with wide
environmental action.

**Observation at distance** — 8° for broadcast/wildlife/surveillance character; 18° or 8° with
foreground occlusion and atmospheric haze for a compressed surveillance portrait.

### Content–FOV alignment

Wide works for environmental, spatial, physical, immersive, body-near-camera content. Telephoto works
for portrait, observation, isolation, compression, distant watching. Macro works as its own beat.

**Do not mix content classes inside one lens beat.** Face portrait + environmental geography + macro
detail in the same beat causes lens drift. If the scene needs several, use controlled internal cuts
and assign a lens character per shot.

---

## The blocks

Paste one into the OPTICS or CAMERA section, verbatim.

### 47° Standard normal

```text
47° diagonal field of view, standard normal lens character, camera 3 to 5 meters from subject,
natural human-eye perspective. Zero obvious distortion, natural face and body proportions,
comfortable depth of field, background readable but not exaggerated, classic grounded cinema framing.
```

### 84° Classic wide

```text
84° diagonal field of view, classic wide-angle lens character, camera 1 to 1.5 meters from subject,
slight low angle if needed. Wide-angle lens with strong but natural perspective expansion, foreground
body presence feels larger and closer, environment remains visible to the frame edges, deep readable
spatial context, straight architectural lines stay rectilinear, no fisheye curve.
```

### 107° Wide rectilinear

```text
107° diagonal field of view, wide rectilinear lens character, camera 0.5 to 0.8 meters from foreground
subject. Immediate foreground looms large, surrounding environment spreads wide to all frame edges,
deep edge-to-edge focus, straight lines remain straight, subtle chromatic aberration near frame edges,
no circular vignette, no fisheye bubble.
```

### 29° Short telephoto portrait

```text
29° diagonal field of view, short telephoto portrait lens character, camera 4 to 6 meters from subject.
Close framing achieved through lens reach, not physical proximity. Subject is razor-sharp, background
begins to compress closer behind them, face proportions are flattering and stable, background dissolves
into creamy soft bokeh, subject pops clearly from the environment.
```

### 18° Classic telephoto

```text
18° diagonal field of view, classic telephoto lens character, camera 6 to 8 meters from subject. Strong
background compression, distant elements appear stacked closer behind the subject, razor-thin focus
isolates the eyes and key facial features, foreground and background melt into soft bokeh, the image
feels observed from a distance.
```

### 8° Super-telephoto observation

```text
8° diagonal field of view, super-telephoto observation lens character, camera 20 to 25 meters from
subject. Extreme background compression, background flattened into a soft color wash, only the subject
is sharp, everything else dissolves into creamy bokeh. The image feels like distant paparazzi, wildlife
documentary, or sports-broadcast observation. Foreground occlusion is mandatory: blurred foreground
objects occupy the lower 30 to 45 percent of frame as oversized dark bokeh shapes, framing the subject
from far away.
```

---

## Visual outcome stacks

The block alone is not enough. Reinforce with observable phrases.

**Telephoto — include at least 4:**

- background completely blurred into a soft warm colour wash
- razor focus on the subject
- only the subject is sharp, everything else is soft
- creamy bokeh wash behind the subject
- background compressed flat behind the subject
- the subject pops sharply against a dissolved background
- close framing achieved through lens reach, not physical proximity
- camera positioned far from the subject in physical space
- atmospheric haze suspended between camera and subject
- foreground occlusion frames the subject as soft dark bokeh

**Wide-angle — include at least 3:**

- foreground body presence looms larger than natural
- environment remains visible around the subject
- deep edge-to-edge focus
- straight lines stay rectilinear
- wide spatial context visible to frame edges
- camera physically close to subject
- immersive close perspective
- no telephoto compression
- no creamy portrait bokeh unless explicitly wanted

---

## Anti-drift locks

Append when the shot is at risk of sliding toward a comfortable middle.

**Telephoto**

```text
No part of this shot becomes wide-angle or normal-lens coverage. Wider framing is achieved by the
camera being farther away with the same long-lens reach, not by switching lenses. The background
remains compressed and dissolved in every frame.
```

**Wide-angle**

```text
No part of this shot becomes telephoto portrait coverage. The environment stays visible around the
subject, the camera remains physically close, and the image keeps wide-angle spatial expansion with
deep readable context.
```

**Normal**

```text
No extreme wide distortion, no telephoto compression. The image stays natural, grounded, and
human-eye neutral.
```

---

## Multi-shot lens consistency

If a generation contains internal cuts, define lens character per shot.

**Same lens throughout:**

```text
LENS IS X° ACROSS ALL SHOTS. NOT NEGOTIABLE.
Each shot opens with: LENS LOCK SHOT A = X°.
Each shot closes with: LENS CHECK SHOT A: X° maintained, no drift.
```

**Mixed lenses:** a shot gets its own lens character only when the content type changes. Hard cuts
only between different lens characters. No smooth FOV transitions, no drift inside a shot, no change
of lens character without a new shot.

**Every internal cut preserves:** active characters · location geography · screen direction · gaze
line · body orientation · lighting direction · prop state · wound state · blood/snow/dirt continuity ·
world physics.

---

## Anti-patterns — do not write

- "extreme wide-angle lens" · "ultra wide-angle" · "super wide-angle"
- "wide shot" or "establishing shot" **as a lens instruction** (they are framings, not optics)
- "zoom out plus wide-angle"
- "tight wide framing"
- f-stop, ISO or lens-brand metadata as primary control
- compound camera movements in one shot
- mixed content classes inside one beat
- negative-only lens control
