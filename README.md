<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</p>

# seedance-director

> AI video director for the Seedance (即梦) platform. Idea in, production-ready prompts out.

An [Agent Skill](https://agentskills.io) that guides you from a rough idea through asset preparation, storyboarding, and prompt generation — all inside Claude Code.

## Install

```bash
npx skills add https://github.com/crowscc/seedance-director
```

Then describe your video idea. Activates on keywords like "Seedance", "即梦", "storyboard", "分镜", "运镜", etc.

## Workflow

<p align="center">
  <img src="assets/workflow.svg" alt="seedance-director workflow" width="700">
</p>

### Phase 1-2: Understand & Dig

Scans your input for 5 dimensions: **topic**, **duration**, **style**, **assets**, **audio**.

Missing info gets filled via `AskUserQuestion` — options are **dynamically ranked** by relevance to your idea. Say "coffee ad" and narrative structures like "Contrast" and "Process Journey" get prioritized over "Suspense." Up to 3 rounds, then moves on.

### Phase 0: Asset Preparation

Before any storyboard gets generated, checks what visual references you have. **Have them? Skip. Don't? Generate:**

- **Character turnaround sheet** — front + side + back views, locks character appearance across all shots
- **Scene concept art** — locks environment style, lighting, color palette to prevent drift across segments
- **Key frames** — first frame for each segment, ensures seamless segment-to-segment continuity

The director asks via `AskUserQuestion` which assets to generate. You can always provide your own instead.

### Phase 3: Storyboard

Generates a professional shot-by-shot storyboard (shot sizes and camera moves labeled in both Chinese and English). Duration determines the generation strategy:

| Duration | Strategy |
|----------|----------|
| **≤ 15s** | Single generation |
| **16-30s** | 2 segments — segment 2 uses **video extension** (extension's sweet spot) |
| **31s+** | Each segment generated **independently** — uses turnaround sheets + scene art + previous segment's last frame as references. Avoids error propagation and style drift. Assemble in CapCut/editor. |

Storyboard is confirmed via `AskUserQuestion` before moving on.

### Phase 4: Seedance Prompts

Converts confirmed storyboard into **copy-paste-ready prompts** for the Seedance platform. Every prompt follows a fixed **five-section structure**:

```
## Characters + References
  Character A: @Image1 — [appearance description]
  Scene ref:   @Image3 — [environment description]

## Background
  [Context, environment, emotional atmosphere]

## Shot Descriptions
  Shot 1 (0-3s): [shot size], [content], Character A: "dialogue", [camera move]
  Shot 2 (3-6s): ...

## Style Directives
  [Unified look: texture, color tone, lighting, depth of field, fps, aspect ratio]

## Negatives
  No text, watermarks, logos
```

Each character is bound to its own reference image. Dialogue lines always tag the speaker. All @references use Chinese labels with purpose annotations.

Single-segment gets 2-3 prompt variants. Multi-segment outputs one prompt per segment.

### Phase 5: Operation Guide

Step-by-step Seedance platform instructions: upload order, parameter settings, segment stitching workflow, post-generation checklist. For 3+ segments, includes CapCut assembly guide.

## See It in Action

```
You: I want a 30-second coffee brand ad. Cinematic, warm tones. I have 3 product photos.

Director: [AskUserQuestion] Which narrative structure fits best?
          > Process Journey — bean to cup, matches your product story ✓
          > Contrast — before/after, good for taste reveal
          > Custom — describe your own

You: Process Journey

Director: [AskUserQuestion] You're missing scene references. Generate them?
          > Generate scene concept art
          > I'll provide my own

You: Generate scene concept art

Director:
  Scene concept prompt → "Coffee plantation at sunrise, golden hour..."

  Storyboard (2 segments, 16:9, cinematic warm):
    001 | 0-4s  | Macro CU    | Dolly In | Bean texture, golden backlight
    002 | 4-8s  | Close-Up    | Tilt Down| Beans into grinder
    003 | 8-12s | Medium Shot | Static   | Pour-over, steam rising
    ...

  Segment 1 prompt (paste into Seedance):
    ## Characters + References
    角色：@图片1 — Coffee beans, golden texture
    场景参考：@图片2 — Plantation at sunrise

    ## Background
    A journey from bean to cup, golden hour warmth...

    ## Shot Descriptions
    镜头1（0-4s）：Macro CU, bean texture, Dolly In
    镜头2（4-8s）：CU, beans into grinder, Tilt Down
    ...

    ## Style Directives
    Cinematic, warm tones, 16:9, 24fps

    ## Negatives
    No text, watermarks, logos

  Operation guide:
    Upload photo → 15s, 16:9 → Generate
    → Screenshot last frame → First-frame ref for segment 2
```

## Project Structure

```
skills/seedance-director/
├── SKILL.md                          # Core workflow (273 lines)
├── references/
│   ├── platform-capabilities.md      # 10 Seedance modes + tech specs + @reference rules
│   ├── narrative-structures.md       # 5 narrative structures with timing
│   ├── scene-strategies.md           # 5 scene-type strategies with full prompt examples
│   └── vocabulary.md                 # Camera + visual style bilingual vocabulary
├── templates/
│   ├── single-video.md               # 5 storyboard templates (A-E)
│   ├── multi-segment.md              # Multi-segment templates for 30s/45s/60s+
│   ├── scene-templates.md            # E-commerce / Xianxia / Drama / Education / MV
│   └── output.html                   # Visual output template (storyboard + prompt viewer)
└── examples/
    ├── single-examples.md            # 6 complete single-segment examples
    └── multi-examples.md             # 4 complete multi-segment examples
```

References are loaded on demand — the core SKILL.md stays lean.

## Acknowledgments

Inspired by:

- [songguoxs/seedance-prompt-skill](https://github.com/songguoxs/seedance-prompt-skill)
- [elementsix/elementsix-skills](https://github.com/elementsix/elementsix-skills)

## License

MIT
