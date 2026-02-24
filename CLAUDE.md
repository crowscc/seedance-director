# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Seedance Director 是一个 Agent Skill，帮助用户在即梦（Seedance）AI 视频平台上完成从创意到生产级提示词的全流程。纯文档系统，无代码依赖，采用 agentskills.io v2.0 标准架构。

## Architecture

核心引擎是 `skills/seedance-director/SKILL.md`（273行），定义了6阶段工作流和所有交互逻辑。参考文件**按需加载**，不要一次性读取所有文件。

### 按需加载矩阵

| 文件 | 何时加载 |
|------|---------|
| `references/platform-capabilities.md` | Phase 4 生成提示词时 |
| `references/narrative-structures.md` | Phase 2 讨论叙事结构时 |
| `references/scene-strategies.md` | 场景类型明确后 |
| `references/vocabulary.md` | Phase 3-4 编写分镜/提示词时 |
| `templates/single-video.md` | 单段视频（≤15s） |
| `templates/multi-segment.md` | 多段视频（>15s） |
| `templates/scene-templates.md` | 需要场景专属模板时 |
| `examples/single-examples.md` | 用户需要单段参考案例 |
| `examples/multi-examples.md` | 用户需要多段参考案例 |

### 关键设计模式

- **动态选项排序**：根据用户创意内容智能排序建议选项（不平铺所有选项）
- **素材自适应检测**：矩阵判断用户已有素材，只生成缺失部分
- **时长驱动策略**：≤15s 单段 / 16-30s 两段（视频延长）/ 31s+ 多段独立生成+首帧衔接
- **即梦提示词五板块**：角色+参考图 → 背景介绍 → 镜头描述 → 风格指令 → 禁止项

## File Roles

```
skills/seedance-director/
├── SKILL.md                  # 核心引擎：6阶段工作流 + 交互逻辑（改这里影响全局）
├── references/               # 只读知识库：平台能力、叙事结构、场景策略、词汇表
├── templates/                # 输出模板：分镜表、提示词格式、HTML可视化
└── examples/                 # 完整案例：10个可复制的端到端示例
```

## Editing Guidelines

- 修改 SKILL.md 时注意6阶段的依赖关系（Phase 0-5 顺序固定，但 Phase 0 可跳过）
- references/ 下的文件是知识库，更新时保持中英双语对照格式
- vocabulary.md 的9大分类结构（景别、运镜、角度、转场、节奏、风格、色调、光影、情绪）不要打乱
- templates/ 中的分镜模板（A-E）各有独立场景定位，新增模板用新字母编号
- output.html 使用变量占位符，修改时确保变量名与 SKILL.md 中的输出规范一致
- 所有提示词示例必须遵循五板块结构
