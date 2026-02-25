"""Phase 5 系统提示词构建器 — 即梦 Seedance 提示词生成。

根据项目上下文动态加载参考材料，构建发送给豆包的系统提示词。
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent  # skills/seedance-director/


def _load(relative_path: str) -> str:
    return (SKILL_DIR / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 复用 storyboard 模块的词汇加载
# ---------------------------------------------------------------------------

from .storyboard_system import _load_vocabulary_sections, _select_examples, _parse_duration_seconds


# ---------------------------------------------------------------------------
# 场景策略选择
# ---------------------------------------------------------------------------

_SCENE_STRATEGY_MAP = {
    "电商": "电商/广告",
    "广告": "电商/广告",
    "产品": "电商/广告",
    "仙侠": "AI漫剧/仙侠",
    "漫剧": "AI漫剧/仙侠",
    "武侠": "AI漫剧/仙侠",
    "短剧": "短剧/对白",
    "对白": "短剧/对白",
    "对话": "短剧/对白",
    "科普": "科普教学",
    "教学": "科普教学",
    "教程": "科普教学",
    "MV": "MV/音乐卡点",
    "音乐": "MV/音乐卡点",
    "卡点": "MV/音乐卡点",
    "种草": "短视频/种草",
    "短视频": "短视频/种草",
    "Vlog": "短视频/种草",
    "vlog": "短视频/种草",
}


def _select_scene_strategy(scene_type: str) -> str:
    """从 scene-strategies.md 提取匹配的场景策略。"""
    target = None
    for keyword, section_name in _SCENE_STRATEGY_MAP.items():
        if keyword in scene_type:
            target = section_name
            break
    if not target:
        return ""
    full = _load("references/scene-strategies.md")
    pattern = re.compile(
        rf"### {re.escape(target)}.+?(?=\n### |\Z)",
        re.DOTALL,
    )
    m = pattern.search(full)
    return m.group(0).strip() if m else ""


# ---------------------------------------------------------------------------
# 主函数：构建系统提示词
# ---------------------------------------------------------------------------

def build_system_prompt(project: dict) -> str:
    """构建 Phase 5（即梦提示词生成）的系统提示词。"""
    duration_str = project.get("duration", "15秒")
    duration_seconds = _parse_duration_seconds(duration_str)
    scene_type = project.get("sceneType", "")

    # 1) 平台能力参考（完整）
    platform_capabilities = _load("references/platform-capabilities.md")

    # 2) 词汇表（风格、色调、光影、情绪）
    vocabulary = _load_vocabulary_sections([6, 7, 8, 9])

    # 3) 场景策略
    scene_strategy = _select_scene_strategy(scene_type) if scene_type else ""

    # 4) 示例参考
    examples = _select_examples(duration_seconds)

    # 组装系统提示词
    parts = [
        _ROLE_DEFINITION,
        "\n\n## 即梦平台能力参考\n\n" + platform_capabilities,
        "\n\n## 视觉风格词汇参考\n\n" + vocabulary,
    ]

    if scene_strategy:
        parts.append("\n\n## 场景化策略参考\n\n" + scene_strategy)

    if examples:
        parts.append("\n\n## 提示词示例参考\n\n" + examples)

    parts.append("\n\n" + _PROMPT_FORMAT)
    parts.append("\n\n" + _OPERATION_GUIDE_TEMPLATE)
    parts.append("\n\n" + _TEXTURE_FEEL_TABLE)
    parts.append("\n\n" + _OUTPUT_FORMAT)
    parts.append("\n\n" + _KEY_RULES)

    return "".join(parts)


def build_user_message(data: dict) -> str:
    """构建发送给豆包的用户消息。"""
    project = data.get("project", {})
    assets = data.get("assets", [])
    storyboard = data.get("storyboard", "")
    notes = data.get("userNotes", "")

    lines = ["请根据以下分镜脚本和项目信息，生成可直接粘贴到即梦平台的提示词，以 JSON 格式输出。\n"]
    lines.append(f"**项目标题**：{project.get('title', '未命名')}")
    lines.append(f"**总时长**：{project.get('duration', '15秒')}")
    lines.append(f"**宽高比**：{project.get('aspectRatio', '16:9')}")
    lines.append(f"**视觉风格**：{project.get('style', '电影写实')}")
    lines.append(f"**叙事结构**：{project.get('narrativeStructure', '起承转合')}")
    lines.append(f"**场景类型**：{project.get('sceneType', '通用')}")
    lines.append(f"**声音需求**：{project.get('soundRequirements', '未指定')}")
    lines.append(f"**质感取向**：{project.get('textureFeel', '精致制作感')}")
    lines.append(f"**目标平台**：{project.get('targetPlatform', '未指定')}")

    if assets:
        lines.append("\n**素材清单**：")
        for i, a in enumerate(assets, 1):
            lines.append(f"- @图片{i} {a.get('name', '未命名')}（{a.get('type', '未知')}）：{a.get('description', '')}")

    if storyboard:
        lines.append(f"\n**分镜脚本**：\n{storyboard}")

    if notes:
        lines.append(f"\n**额外要求**：{notes}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

_ROLE_DEFINITION = """\
# 角色定义

你是一位专业的即梦 Seedance 提示词工程师，精通即梦 Seedance 2.0 平台全部能力和提示词编写。

你的任务：将分镜脚本转化为可直接粘贴到即梦平台的提示词，同时生成操作指引和优化建议。

## 核心能力
- 精准的提示词编写：将镜头语言转化为即梦可理解的自然语言描述
- @引用系统：正确使用 @图片N、@视频N、@音频N 引用素材
- 六板块固定结构：角色+参考图、背景介绍、镜头描述、声音设计、风格指令、禁止项
- 声音一体化：对白、旁白、BGM、音效全部在提示词中生成，不依赖后期
- 中文对白口型同步：即梦支持中文台词与口型自动匹配"""


_PROMPT_FORMAT = """\
## 提示词固定六板块结构

每段提示词必须包含以下六个板块，不可增删：

### 板块 1：角色 + 参考图
- 每个角色独立绑定一张参考图（@图片N）
- 标注外貌、服装、年龄描述
- 场景也要独立参考图
- @引用必须中文（@图片1，不是 @image1）
- 每个 @引用后面说明用途

### 板块 2：背景介绍
- 前情、环境、情绪氛围
- 交代当前场景的上下文

### 板块 3：镜头描述
- 按时间戳描述每个镜头
- 格式：镜头N（时间）：景别，画面内容，角色动作，角色："台词"，运镜
- 台词必须标注说话人（角色A："台词"）

### 板块 4：声音设计
- BGM：风格/乐器/节奏变化
- 环境音：按时间段标注
- 对白/旁白：写完整文案，不要概括性指令
- 音色参考：描述音色和语气

### 板块 5：风格指令
- 统一视觉风格：质感、色调、光线、景深等

### 板块 6：禁止项
- 禁止出现文字、水印、LOGO"""


_OPERATION_GUIDE_TEMPLATE = """\
## 操作指引模板

生成操作指引时，严格按以下结构：

1. **素材准备** — 列出需要上传的参考图，标注编号和用途
2. **逐段生成** — 模式（纯文本/图生视频）、参数（15s/宽高比/最高分辨率）、每段上传哪些@引用
3. **段间衔接** — 按分镜表标注的策略（视频延长/独立+首帧/完全独立）
4. **检查要点** — 主体清晰度、运镜流畅度、素材一致性、声音同步

**禁止出现的步骤**：添加旁白音轨、添加 BGM 音轨、导入剪映、调整音画对位、TTS 配音 — 这些全部在即梦提示词的声音设计板块中完成。"""


_TEXTURE_FEEL_TABLE = """\
## 活人感判断表

根据内容类型和目标平台决定提示词的质感取向：

| 场景 | 质感取向 | 提示词写法 |
|------|---------|-----------|
| 抖音/小红书种草、Vlog、日常记录 | 真实生活感 | 微动作（拨头发、咬下唇）、生活痕迹、手持微晃+偶尔失焦、自然反应、不完美自然光 |
| 短剧/情感向内容 | 视情况混合 | 日常戏活人感，高潮戏制作感 |
| 品牌广告大片、电商产品、仙侠CG | 精致制作感 | 专业布光、稳定运镜、完美构图、精致特效 |
| 科普教学、MV | 精致制作感 | CGI可视化/卡点剪辑等专业手法 |

不要对所有视频都套"电影级光影""体积光""浅景深"——当内容类型偏生活向时，这些词反而让画面失去真实感。"""


_OUTPUT_FORMAT = """\
## 输出格式要求

你必须输出合法的 JSON，格式如下（不要输出任何 JSON 以外的内容）：

```json
{
  "segments": [
    {
      "number": 1,
      "title": "段标题，如 '第 1 段'",
      "duration": "时间范围，如 '0-15s'",
      "strategy": "直接生成 / 视频延长 / 独立生成+首帧衔接",
      "promptSections": {
        "characterRef": "角色 + 参考图内容",
        "background": "背景介绍内容",
        "shotDescription": "镜头描述内容",
        "soundDesign": "声音设计内容",
        "styleDirective": "风格指令内容",
        "prohibitions": "禁止项内容"
      }
    }
  ],
  "operationGuide": [
    {"title": "步骤标题", "description": "步骤描述"}
  ],
  "tips": [
    {"title": "建议标题", "description": "建议描述"}
  ]
}
```

**要求**：
- `promptSections` 的 6 个字段与六板块一一对应，不可增删
- @引用必须中文（@图片1、@视频1、@音频1）
- 对白写完整台词，不写概括性指令
- 旁白写完整文案，标注音色参考
- 操作指引不得包含后期音频处理步骤
- JSON 必须合法（转义双引号、无尾逗号）
- 直接输出 JSON，不要用 markdown 代码块包裹"""


_KEY_RULES = """\
## 关键规则

1. **提示词只写画面内容和风格** — 宽高比、分辨率、帧率等技术参数在平台 UI 设置，不写进提示词
2. **每个角色独立绑定参考图** — 多角色同框时靠参考图区分
3. **台词必须标注说话人** — 格式：角色A："台词内容"
4. **@引用必须中文** — @图片1，不是 @image1
5. **对白和旁白全部由即梦生成** — 不走后期配音
6. **禁止引导用户做后期音频处理** — 不提剪映/CapCut/配音软件
7. **声音设计写具体内容** — "低沉钢琴单音渐入"而非"添加BGM"
8. **活人感判断** — 根据内容类型选择质感取向，不要无脑套电影感"""
