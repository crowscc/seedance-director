<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</p>

# seedance-director

> 用即梦做视频，提示词不知道怎么写？交给你的 AI 导演。

一个 [Agent Skill](https://agentskills.io)，在 Claude Code 里帮你走完从创意到即梦提示词的全流程。

## 安装

```bash
npx skills add https://github.com/crowscc/seedance-director
```

安装后直接聊你的视频创意。提到「即梦」「Seedance」「分镜」「运镜」「视频延长」等关键词时自动激活。

## 工作流

<p align="center">
  <img src="assets/workflow_zh.svg" alt="seedance-director 工作流" width="700">
</p>

### Phase 1-2：理解创意 & 深度挖掘

收到你的创意后，自动扫描 5 个维度的完整度：**主题**、**时长**、**风格**、**素材**、**声音**。

缺什么问什么 — 通过 `AskUserQuestion` 弹出结构化选择题，**选项根据你的创意动态排序**（优先级：主题 > 叙事结构 > 风格 > 时长 > 素材 > 声音）。比如你说「咖啡广告」，叙事结构会优先推荐「对比型」和「AIDA营销型」，而不是把所有选项平铺。最多问 3 轮，剩余维度自动决策。

叙事结构**始终讨论**，即使其他维度都已明确。

### Phase 3：素材制备

检查你手上有没有视觉参考素材。**素材齐全？自动跳过。检测到缺失？** 你来选：

- **生成参考图** — 角色三视图、场景概念图、关键帧（提升跨镜头一致性）
- **不需要，直接写提示词** — 自己准备素材或纯文生视频

多个素材通过 subagent **并行生成**。

### Phase 4：生成分镜脚本

根据前面确定的所有信息，输出专业分镜表（景别、运镜均中英双语标注）。

**质感取向**在这一步决定 — 根据内容类型、目标平台和你选的风格，导演判断用**真实生活感**（手持、自然光、微动作）还是**精致制作感**（稳定器、专业布光、精确构图）。你显式选择的风格始终优先。

| 时长 | 策略 |
|------|------|
| **≤ 15s** | 单段生成 |
| **16-30s** | 拆 2 段，第 2 段用**视频延长** |
| **31s+** | 每段**独立生成**，用角色三视图 + 场景图 + 上段末帧作为参考 |

分镜完成后通过 `AskUserQuestion` 让你确认或调整。

### Phase 5：即梦提示词 + 操作指引

把确认后的分镜转化为**可直接粘贴到即梦平台**的提示词。每段提示词遵循固定的**六板块结构**：

```
## 角色 + 参考图
  角色A（主角）：@图片1 — [外貌、服装描述]
  场景参考：@图片3 — [环境描述]

## 背景介绍
  [前情、环境、情绪氛围]

## 镜头描述
  镜头1（0-3s）：[景别]，[画面]，角色A："[台词]"，[运镜]

## 声音设计
  BGM：[乐器、节奏变化]
  环境音：[按时间段标注]
  台词/旁白：[音色参考、语气]

## 风格指令
  [统一视觉风格：质感、色调、光线、景深]

## 禁止项
  禁止出现文字、水印、LOGO
```

单段输出 1 个推荐版本 + 可调整方向说明，多段逐段输出并附衔接指引。

输出后导演通过 `AskUserQuestion` 收集反馈 — 可以调整特定镜头、换风格、出变体。满意后生成**可视化 HTML 页面**（自动在浏览器打开），包含完整分镜表、提示词和操作指引。

## 30 秒看懂

```
你：帮我做一个 15 秒的咖啡产品视频，发小红书，温馨一点。

导演：[AskUserQuestion] 哪种叙事结构最合适？
      > AIDA营销型 — 吸引→兴趣→欲望→行动，种草经典 ✓
      > 日常切片型 — 生活中的一个瞬间，自然真实
      > 自定义 — 描述你想要的结构

你：AIDA

导演：[AskUserQuestion] 检测到缺少产品参考图，要生成吗？
      > ✅ 生成参考图
      > ⏭ 不需要，直接写提示词

你：不需要

导演：
  分镜脚本（单段，9:16，日系清新）：
    001 | 0-2s  | 第一人称POV  | 手持推进      | 手推开咖啡馆门，暖光涌入
    002 | 2-4s  | 近景 CU      | 手持跟拍      | 产品在桌面，浅景深
    003 | 4-6s  | 特写 ECU     | 缓推 Dolly In | 杯身细节，光斑
    004 | 6-8s  | 中景 MS      | 手持跟拍      | 使用产品，自然互动
    ...

  即梦提示词（直接粘贴）：
    ## 角色 + 参考图
    @图片1 作为产品实物参考

    ## 背景介绍
    午后的阳光咖啡馆，温暖而安静...

    ## 镜头描述
    镜头1（0-2s）：第一人称POV，手推开玻璃门，手持跟拍，轻微晃动
    镜头2（2-4s）：近景，产品在木桌上，窗边自然光
    ...

    ## 声音设计
    BGM：轻快原声吉他，温暖放松
    环境音：咖啡馆人声、杯碟轻响、门铃

    ## 风格指令
    日系清新，柔和自然光，暖色调，浅景深

    ## 禁止项
    禁止出现文字、水印、LOGO

  [自动在浏览器中打开可视化页面]
```

## 项目结构

```
skills/seedance-director/
├── SKILL.md                          # 核心流程引擎（~410 行）
├── references/
│   ├── platform-capabilities.md      # 即梦 10 种模式 + 技术参数 + @引用规范
│   ├── narrative-structures.md       # 16 种叙事结构及时间分配 + 选择指南
│   ├── scene-strategies.md           # 6 类场景策略及完整提示词示例
│   └── vocabulary.md                 # 镜头语言 + 视觉风格双语词汇表
├── templates/
│   ├── single-video.md               # 5 种分镜模板（A-E）
│   ├── multi-segment.md              # 30s/45s/60s+ 多段模板
│   ├── scene-templates.md            # 电商/仙侠/短剧/科普/MV/短视频
│   └── output.html                   # 可视化 HTML 模板（静态 + JSON 数据注入）
└── examples/
    ├── single-examples.md            # 6 个完整单段示例
    └── multi-examples.md             # 4 个完整多段示例
```

参考文件按需加载，核心 SKILL.md 保持精简。

## 豆包 AI 生成器（独立 Python 脚本）

除了 Agent Skill 流程，项目还提供一个独立的 Python 脚本，通过火山引擎调用豆包大模型来生成分镜和提示词。适合需要批量生成或在自己的工作流中集成的场景。

### 配置

```bash
cd scripts
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入你的火山引擎 API Key 和 Endpoint ID
```

API Key 和 Endpoint 获取方式：
1. 注册 [火山引擎](https://www.volcengine.com/) 并完成实名认证
2. 进入 [火山方舟控制台](https://console.volcengine.com/ark) → 密钥管理 → 创建 API Key
3. 模型广场 → 选择豆包模型（推荐 Doubao-1.5-pro）→ 创建在线推理接入点 → 获取 Endpoint ID

### 使用

```bash
# 仅生成分镜脚本
python doubao_generator.py storyboard --brief "15秒温情回家短片，电影写实风格"

# 根据已有分镜生成即梦提示词
python doubao_generator.py prompt --brief "15秒温情回家短片" --storyboard storyboard.md

# 一次性生成分镜 + 提示词（两步串联调用豆包）
python doubao_generator.py full --brief "15秒咖啡品牌广告，小红书，温馨风格"

# 流式输出（实时显示生成过程）
python doubao_generator.py full --brief "15秒咖啡品牌广告" --stream

# 保存到文件
python doubao_generator.py full --brief "15秒咖啡品牌广告" -d output/
```

脚本会自动加载项目中的参考文件（词汇表、模板、示例）作为豆包的上下文，确保生成结果符合 Seedance 平台的格式要求。

### 项目结构

```
scripts/
├── doubao_generator.py     # 主脚本
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
└── .env                    # 你的配置（不入版本控制）
```

## 致谢

灵感来自：

- [songguoxs/seedance-prompt-skill](https://github.com/songguoxs/seedance-prompt-skill)
- [elementsix/elementsix-skills](https://github.com/elementsix/elementsix-skills)

## License

MIT
