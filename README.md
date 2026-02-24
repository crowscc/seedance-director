<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</p>

# seedance-director

> Struggling with Seedance prompts? Let your AI director handle it.

Describe your idea. seedance-director takes it from **concept → storyboard → Seedance prompt → platform instructions** — so you can skip the guesswork.

## Without It vs With It

```
         Without seedance-director             With seedance-director
         ─────────────────────────             ──────────────────────

Input:   "Make me a coffee ad"                 "Make me a coffee ad"
                  │                                     │
You do:  Figure out story structure             Answer a few quick choices
         Look up camera terminology             Get a pro storyboard auto-generated
         Cobble together a prompt               Get a ready-to-paste prompt
         Trial-and-error on the platform        Get step-by-step instructions
                  │                                     │
Time:         30-60 min                              3 min
```

## Three Core Strengths

**Thinks like a director** — Doesn't just spit out prompts. First structures your story (three-act, hook-twist, contrast...), then breaks it into a professional shot list. Film methodology + AI video, combined.

**Short clips and long videos** — Up to 15s in one shot. Over 15s? Auto-splits into segments with anchor frames between them for visual continuity. Supports 60s+.

**Prompt to platform, end-to-end** — Not just prompts. Tells you exactly what to click, what to upload, and what parameters to set on the Seedance platform. Beginners welcome.

## Quick Start

```bash
claude skill add --url https://github.com/crowscc/seedance-director
```

Then just describe your video idea. Activates automatically when you mention "Seedance", "video", "storyboard", or "prompt".

## See It in Action

```
You:      I want a 30-second coffee brand ad. Cinematic, warm tones.
          I have 3 product photos.

Director: Got it. Which narrative structure?
          A. Hook → Reveal (steam close-up opener)
          B. Process (bean to cup journey)
          C. Lifestyle (cozy scene, enjoying coffee)

You:      B

Director:
  ┌──────────────────────────────────────────────────┐
  │  Storyboard: Coffee Origins                       │
  │  30s (2 segments) | 16:9 | Cinematic warm         │
  │                                                    │
  │  001 | 0-4s  | Macro     | Push In  | Bean texture │
  │  002 | 4-8s  | Close-Up  | Tilt     | Into grinder │
  │  003 | 8-12s | Medium    | Static   | Pour-over    │
  │  004 | 12-15s| Close-Up  | Push In  | Coffee drip  │
  │  ...                                               │
  ├──────────────────────────────────────────────────┤
  │  Segment 1 Prompt (paste into Seedance)            │
  │  @Photo1 中的咖啡豆在晨光中缓缓滚动，微距镜头...   │
  ├──────────────────────────────────────────────────┤
  │  Operation Guide                                   │
  │  1. Open Seedance → Image-to-Video                 │
  │  2. Upload photo, paste prompt                     │
  │  3. Duration 15s, ratio 16:9                       │
  │  4. Then → Video Extension → paste segment 2       │
  └──────────────────────────────────────────────────┘
```

## All 10 Seedance Capabilities

| Capability | What it does |
|-----------|-------------|
| Text-to-Video | No assets needed, just describe |
| Consistency Control | Lock character/scene across shots |
| Motion Reference | Copy camera moves from a reference |
| Effect Reference | Copy visual effects from a reference |
| Story Completion | AI fills in transitions |
| Video Extension | Continue an existing video |
| Voice & Audio | Dialogue, voice cloning, SFX |
| One-Take | Chain images into seamless long take |
| Video Editing | Swap characters, change plot |
| Music Sync | Visuals follow the beat |

## Long Videos? Auto-segmented

| Duration | What happens |
|----------|-------------|
| Up to 15s | Single generation |
| 16-30s | 2 segments, linked by video extension |
| 31-45s | 3 segments |
| 46-60s | 4 segments |
| 60s+ | Split by scene, assemble in editor |

Each segment boundary has an **anchor frame** — the ending of one matches the opening of the next.

## 5 Built-in Scene Templates

Ready to use, no starting from scratch:

- **E-commerce** — 360 rotation, macro detail, 3D render
- **Xianxia/Anime** — Magic effects, transformation, energy waves
- **Short Drama** — Multi-character dialogue, emotion tags, SFX
- **Educational** — Visualization, narration, explainer style
- **Music Video** — 2.35:1 widescreen, beat sync, fast cuts

<details>
<summary>Project Structure</summary>

```
seedance-director/
├── .claude/skills/seedance-director/
│   └── SKILL.md                 # Core: interaction logic + capability templates
├── templates/
│   ├── single-video.md          # Single-segment templates (5 types)
│   ├── multi-segment.md         # Multi-segment templates
│   └── scene-templates.md       # Scene templates (5 genres)
├── examples/
│   ├── single-examples.md       # Single-segment examples (6)
│   └── multi-examples.md        # Multi-segment examples (4)
├── references/
│   └── vocabulary.md            # Camera & visual style bilingual vocabulary
├── README.md / README_zh.md
└── LICENSE (MIT)
```

</details>

## Acknowledgments

Inspired by:

- [songguoxs/seedance-prompt-skill](https://github.com/songguoxs/seedance-prompt-skill) — Capability templates and multi-segment strategy
- [elementsix/elementsix-skills](https://github.com/elementsix/elementsix-skills) — Interactive guidance and modular architecture

## License

MIT
