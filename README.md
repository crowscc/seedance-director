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
  <img src="assets/workflow_en.svg" alt="seedance-director workflow" width="700">
</p>

### Phase 1-2: Understand & Dig

Scans your input for 5 dimensions: **topic**, **duration**, **style**, **assets**, **audio**.

Missing info gets filled via `AskUserQuestion` — options are **dynamically ranked** by relevance (priority: topic > narrative structure > style > duration > assets > audio). Say "coffee ad" and narrative structures like "Contrast" and "AIDA" get prioritized over "Suspense." Up to 3 rounds; remaining dimensions auto-decided.

Narrative structure is **always discussed** even when most dimensions are clear.

### Phase 3: Asset Preparation

Checks what visual references you have. **Have everything? Auto-skip. Missing something?** You choose:

- **Generate reference images** — character turnaround sheets, scene concepts, key frames (improves cross-shot consistency)
- **Skip, go straight to storyboard** — provide your own assets or use text-to-video

Multiple assets are generated in **parallel** via subagents.

### Phase 4: Storyboard

Generates a professional shot-by-shot storyboard (shot sizes and camera moves in both Chinese and English).

**Texture-feel decision** happens here — based on content type, platform, and your chosen style, the director decides between **realistic life feel** (handheld, natural light, micro-actions) and **polished production feel** (stabilized, studio lighting, precise framing). Your explicit style choice always overrides platform defaults.

| Duration | Strategy |
|----------|----------|
| **≤ 15s** | Single generation |
| **16-30s** | 2 segments — segment 2 uses **video extension** |
| **31s+** | Each segment generated **independently** with turnaround sheets + scene art + last-frame references |

Storyboard is confirmed via `AskUserQuestion` before moving on.

### Phase 5: Prompts + Operation Guide

Converts confirmed storyboard into **copy-paste-ready prompts** for Seedance. Every prompt follows a fixed **six-section structure**:

```
## Characters + References
  Character A: @Image1 — [appearance description]
  Scene ref:   @Image3 — [environment description]

## Background
  [Context, environment, emotional atmosphere]

## Shot Descriptions
  Shot 1 (0-3s): [shot size], [content], Character A: "dialogue", [camera move]

## Sound Design
  BGM: [instruments, rhythm changes]
  Ambient: [time-stamped sound effects]
  Dialogue: [voice reference, tone]

## Style Directives
  [Unified look: texture, color tone, lighting, depth of field]

## Negatives
  No text, watermarks, logos
```

Single-segment outputs 1 recommended version with adjustable directions. Multi-segment outputs one prompt per segment with connection guides.

After prompts, the director collects feedback via `AskUserQuestion` — adjust specific shots, swap styles, or generate variants. When satisfied, outputs a **visual HTML page** (auto-opens in browser) with the full storyboard, prompts, and operation guide.

## See It in Action

```
You: I want a 15-second coffee product video for Xiaohongshu. Cozy vibe.

Director: [AskUserQuestion] Which narrative structure fits best?
          > AIDA — attention → interest → desire → action, classic for product ✓
          > Daily Slice — a moment in life, natural and relatable
          > Custom — describe your own

You: AIDA

Director: [AskUserQuestion] Missing product reference. Generate?
          > ✅ Generate reference images
          > ⏭ Skip, go straight to prompts

You: Skip

Director:
  Storyboard (single, 9:16, Japanese fresh style):
    001 | 0-2s  | POV          | Handheld Push | Hand pushes open café door, warm light
    002 | 2-4s  | Close-Up     | Handheld      | Product on table, shallow DOF
    003 | 4-6s  | Macro CU     | Slow Push In  | Surface detail, light spots
    004 | 6-8s  | Medium Shot  | Handheld      | Using product, natural interaction
    ...

  Seedance prompt (paste directly):
    ## Characters + References
    @Image1 as product reference

    ## Background
    A warm afternoon in a sunlit café...

    ## Shot Descriptions
    Shot 1 (0-2s): POV, hand pushes open glass door, handheld, slight shake
    Shot 2 (2-4s): Close-up, product on wooden table, window light
    ...

    ## Sound Design
    BGM: Light acoustic guitar, warm and relaxed
    Ambient: Café chatter, cup clinks, door chime

    ## Style Directives
    Japanese fresh, soft natural light, warm tones, shallow DOF

    ## Negatives
    No text, watermarks, logos

  [Opens visual HTML page in browser]
```

## Project Structure

```
skills/seedance-director/
├── SKILL.md                          # Core workflow engine (~410 lines)
├── references/
│   ├── platform-capabilities.md      # 10 Seedance modes + tech specs + @reference rules
│   ├── narrative-structures.md       # 16 narrative structures with timing & selection guide
│   ├── scene-strategies.md           # 6 scene-type strategies with full prompt examples
│   └── vocabulary.md                 # Camera + visual style bilingual vocabulary
├── templates/
│   ├── single-video.md               # 5 storyboard templates (A-E)
│   ├── multi-segment.md              # Multi-segment templates for 30s/45s/60s+
│   ├── scene-templates.md            # E-commerce / Xianxia / Drama / Education / MV / Short-video
│   └── output.html                   # Visual HTML template (static + JSON data injection)
└── examples/
    ├── single-examples.md            # 6 complete single-segment examples
    └── multi-examples.md             # 4 complete multi-segment examples
```

References are loaded on demand — the core SKILL.md stays lean.

## Doubao AI Generator (Standalone Python Script)

In addition to the Agent Skill workflow, the project includes a standalone Python script that calls the Doubao (豆包) large language model via Volcano Engine to generate storyboards and prompts. Useful for batch generation or integration into your own pipeline.

### Setup

```bash
cd scripts
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Volcano Engine API Key and Endpoint ID
```

To get your API Key and Endpoint:
1. Register at [Volcano Engine](https://www.volcengine.com/) and complete identity verification
2. Go to [Volcano Ark Console](https://console.volcengine.com/ark) → Key Management → Create API Key
3. Model Plaza → Select Doubao model (recommended: Doubao-1.5-pro) → Create inference endpoint → Copy Endpoint ID

### Usage

```bash
# Generate storyboard only
python doubao_generator.py storyboard --brief "15s heartwarming homecoming, cinematic style"

# Generate Seedance prompt from existing storyboard
python doubao_generator.py prompt --brief "15s homecoming" --storyboard storyboard.md

# Full pipeline: storyboard + prompt (two-step Doubao calls)
python doubao_generator.py full --brief "15s coffee brand ad, Xiaohongshu, cozy vibe"

# Stream output (see generation in real-time)
python doubao_generator.py full --brief "15s coffee brand ad" --stream

# Save to files
python doubao_generator.py full --brief "15s coffee brand ad" -d output/
```

The script auto-loads project reference files (vocabulary, templates, examples) as Doubao context, ensuring outputs match Seedance platform format requirements.

### Script Structure

```
scripts/
├── doubao_generator.py     # Main script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── .env                    # Your config (git-ignored)
```

## Acknowledgments

Inspired by:

- [songguoxs/seedance-prompt-skill](https://github.com/songguoxs/seedance-prompt-skill)
- [elementsix/elementsix-skills](https://github.com/elementsix/elementsix-skills)

## License

MIT
