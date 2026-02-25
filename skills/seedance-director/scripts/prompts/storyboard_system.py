"""Phase 4 系统提示词构建器 — 分镜脚本生成。

根据项目上下文动态加载参考材料，构建发送给豆包的系统提示词。
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent  # skills/seedance-director/


def _load(relative_path: str) -> str:
    return (SKILL_DIR / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 词汇表按章节加载
# ---------------------------------------------------------------------------

_SECTION_PATTERN = re.compile(r"^## [一二三四五六七八九]、", re.MULTILINE)

_SECTION_NAMES = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}


def _load_vocabulary_sections(sections: list[int]) -> str:
    """从 vocabulary.md 中提取指定章节（1-9）。"""
    full = _load("references/vocabulary.md")
    # 按 ## N、 分割
    parts = _SECTION_PATTERN.split(full)
    # 找到每个章节的起止位置
    matches = list(_SECTION_PATTERN.finditer(full))
    result_parts = []
    for sec_num in sections:
        name = _SECTION_NAMES.get(sec_num)
        if not name:
            continue
        for i, m in enumerate(matches):
            if f"## {name}、" == m.group(0).strip() or m.group(0).strip().startswith(f"## {name}、"):
                start = m.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full)
                result_parts.append(full[start:end].strip())
                break
    return "\n\n".join(result_parts)


# ---------------------------------------------------------------------------
# 模板选择
# ---------------------------------------------------------------------------

_SINGLE_TEMPLATE_MAP = {
    "电商": "模板B",
    "广告": "模板B",
    "产品": "模板B",
    "仙侠": "模板C",
    "武侠": "模板C",
    "动作": "模板C",
    "格斗": "模板C",
    "舞蹈": "模板C",
    "游戏": "模板C",
    "风景": "模板D",
    "旅拍": "模板D",
    "旅游": "模板D",
    "旅行": "模板D",
    "城市": "模板D",
    "短剧": "模板E",
    "对白": "模板E",
    "对话": "模板E",
    "情景": "模板E",
}


def _select_single_template(scene_type: str) -> str:
    """从 single-video.md 选择匹配的模板。"""
    full = _load("templates/single-video.md")
    # 确定目标模板
    target = "模板A"  # 默认叙事故事型
    for keyword, tpl in _SINGLE_TEMPLATE_MAP.items():
        if keyword in scene_type:
            target = tpl
            break
    # 提取目标模板段落
    pattern = re.compile(rf"## {target}[：:].+?(?=\n## 模板|\Z)", re.DOTALL)
    m = pattern.search(full)
    if m:
        return m.group(0).strip()
    return full  # fallback: 全量返回


def _parse_duration_seconds(duration: str) -> int:
    """解析时长字符串为秒数，如 '15秒' → 15, '1分钟' → 60, '30s' → 30。"""
    duration = duration.strip().lower()
    # 分钟
    m = re.search(r"(\d+)\s*分", duration)
    if m:
        return int(m.group(1)) * 60
    # 秒
    m = re.search(r"(\d+)", duration)
    if m:
        return int(m.group(1))
    return 15  # 默认


def _select_multi_template(duration_seconds: int) -> str:
    """从 multi-segment.md 选择匹配时长的模板。"""
    full = _load("templates/multi-segment.md")
    if duration_seconds <= 30:
        section = "30秒双段模板"
    elif duration_seconds <= 45:
        section = "45秒三段模板"
    else:
        section = "60秒四段模板"
    # 提取对应章节
    pattern = re.compile(
        rf"## {re.escape(section)}.+?(?=\n## (?:30秒|45秒|60秒|衔接锚点设计指南)|\Z)",
        re.DOTALL,
    )
    m = pattern.search(full)
    if m:
        return m.group(0).strip()
    return full


# ---------------------------------------------------------------------------
# 场景模板选择
# ---------------------------------------------------------------------------

_SCENE_TEMPLATE_MAP = {
    "电商": "场景1：电商/广告",
    "广告": "场景1：电商/广告",
    "产品": "场景1：电商/广告",
    "仙侠": "场景2：AI漫剧/仙侠",
    "漫剧": "场景2：AI漫剧/仙侠",
    "武侠": "场景2：AI漫剧/仙侠",
    "短剧": "场景3：短剧/对白",
    "对白": "场景3：短剧/对白",
    "对话": "场景3：短剧/对白",
    "科普": "场景4：科普教学",
    "教学": "场景4：科普教学",
    "教程": "场景4：科普教学",
    "MV": "场景5：MV/音乐卡点",
    "音乐": "场景5：MV/音乐卡点",
    "卡点": "场景5：MV/音乐卡点",
    "种草": "场景6：短视频/种草",
    "短视频": "场景6：短视频/种草",
    "Vlog": "场景6：短视频/种草",
    "vlog": "场景6：短视频/种草",
}


def _select_scene_template(scene_type: str) -> str:
    """从 scene-templates.md 提取匹配的场景模板。"""
    target = None
    for keyword, section_name in _SCENE_TEMPLATE_MAP.items():
        if keyword in scene_type:
            target = section_name
            break
    if not target:
        return ""
    full = _load("templates/scene-templates.md")
    pattern = re.compile(
        rf"## {re.escape(target)}.+?(?=\n## 场景\d|\Z)",
        re.DOTALL,
    )
    m = pattern.search(full)
    return m.group(0).strip() if m else ""


# ---------------------------------------------------------------------------
# 叙事结构选择
# ---------------------------------------------------------------------------

def _select_narrative_structure(structure_name: str) -> str:
    """从 narrative-structures.md 提取指定叙事结构章节。"""
    if not structure_name:
        return ""
    full = _load("references/narrative-structures.md")
    # 尝试按结构名匹配 ### N. XXX
    for keyword in [structure_name, structure_name.replace("-", ""), structure_name.replace("型", "")]:
        pattern = re.compile(
            rf"### \d+\.\s*{re.escape(keyword)}.*?(?=\n### \d+\.|\n## |\Z)",
            re.DOTALL,
        )
        m = pattern.search(full)
        if m:
            return m.group(0).strip()
    # 宽松匹配
    for line_keyword in structure_name:
        if len(line_keyword) < 2:
            continue
    return ""


# ---------------------------------------------------------------------------
# 示例选择
# ---------------------------------------------------------------------------

def _select_examples(duration_seconds: int) -> str:
    """选择 1-2 个匹配的示例。"""
    if duration_seconds <= 15:
        full = _load("examples/single-examples.md")
    else:
        full = _load("examples/multi-examples.md")
    # 取前 2 个完整示例（按 ## 分割）
    sections = re.split(r"\n(?=## )", full)
    # 取第一个（标题）+ 第二、三个（实际示例）
    parts = []
    for s in sections:
        if s.strip().startswith("## ") and "示例" in s:
            parts.append(s.strip())
            if len(parts) >= 2:
                break
    return "\n\n---\n\n".join(parts) if parts else sections[1].strip() if len(sections) > 1 else ""


# ---------------------------------------------------------------------------
# 主函数：构建系统提示词
# ---------------------------------------------------------------------------

def build_system_prompt(project: dict) -> str:
    """构建 Phase 4（分镜脚本生成）的系统提示词。"""
    duration_str = project.get("duration", "15秒")
    duration_seconds = _parse_duration_seconds(duration_str)
    scene_type = project.get("sceneType", "")
    narrative = project.get("narrativeStructure", "")
    is_single = duration_seconds <= 15

    # 1) 词汇表（景别、运镜、角度、转场、节奏）
    vocabulary = _load_vocabulary_sections([1, 2, 3, 4, 5])

    # 2) 分镜模板
    if is_single:
        template = _select_single_template(scene_type)
    else:
        template = _select_multi_template(duration_seconds)

    # 3) 场景专属模板
    scene_template = _select_scene_template(scene_type) if scene_type else ""

    # 4) 叙事结构
    narrative_ref = _select_narrative_structure(narrative) if narrative else ""

    # 5) 示例参考
    examples = _select_examples(duration_seconds)

    # 6) 拆段规则（多段时）
    split_rules = ""
    if not is_single:
        full_multi = _load("templates/multi-segment.md")
        # 提取拆段规则表 + 拆段原则
        m = re.search(r"## 拆段规则表.+?(?=\n## \d+秒)", full_multi, re.DOTALL)
        if m:
            split_rules = m.group(0).strip()
        # 衔接锚点设计指南
        m2 = re.search(r"## 衔接锚点设计指南.+", full_multi, re.DOTALL)
        if m2:
            split_rules += "\n\n" + m2.group(0).strip()

    # 组装系统提示词
    parts = [
        _ROLE_DEFINITION,
        "\n\n## 景别与运镜词汇参考\n\n" + vocabulary,
    ]

    if template:
        parts.append("\n\n## 分镜模板参考\n\n" + template)

    if scene_template:
        parts.append("\n\n## 场景专属策略\n\n" + scene_template)

    if narrative_ref:
        parts.append("\n\n## 叙事结构参考\n\n" + narrative_ref)

    if split_rules:
        parts.append("\n\n## 多段拆分与衔接规则\n\n" + split_rules)

    if examples:
        parts.append("\n\n## 示例参考\n\n" + examples)

    parts.append("\n\n" + _output_format(is_single))
    parts.append("\n\n" + _KEY_RULES)

    return "".join(parts)


def build_user_message(data: dict) -> str:
    """构建发送给豆包的用户消息。"""
    project = data.get("project", {})
    assets = data.get("assets", [])
    notes = data.get("userNotes", "")

    lines = ["请根据以下信息生成专业分镜脚本，以 JSON 格式输出。\n"]
    lines.append(f"**项目标题**：{project.get('title', '未命名')}")
    lines.append(f"**主题**：{project.get('topic', '未指定')}")
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
        for a in assets:
            lines.append(f"- {a.get('name', '未命名')}（{a.get('type', '未知')}）：{a.get('description', '')}")

    if notes:
        lines.append(f"\n**额外要求**：{notes}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

_ROLE_DEFINITION = """\
# 角色定义

你是一位专业的 AI 视频分镜师，精通传统影视分镜设计和镜头语言，专为即梦 Seedance 2.0 平台设计分镜脚本。

你的任务：根据用户提供的创意信息（主题、风格、时长、叙事结构等），生成专业的分镜脚本。

## 核心能力
- 精确的镜头语言：景别、运镜、角度、转场、节奏技法
- 中英双语标注：每个景别和运镜都同时标注中文和英文
- 时间精确设计：每个镜头精确到秒
- 多段拆分能力：超过 15 秒的视频按规则拆段，设计衔接锚点
- 声音同步设计：对白、旁白、BGM、音效与画面同步

## 即梦平台关键约束
- 每次生成固定 15 秒
- 超过 15 秒必须多段拼接
- 16-30 秒用视频延长（2 段）
- 31 秒及以上用独立生成 + 首帧衔接（3 段+）
- 段末 2 秒画面必须趋于平稳（为衔接做准备）"""


def _output_format(is_single: bool) -> str:
    segment_extra = ""
    if not is_single:
        segment_extra = """
        "connection": {
          "label": "段N → 段N+1（视频延长/独立生成+首帧衔接/完全独立生成）",
          "description": "衔接操作说明"
        }"""

    return f"""\
## 输出格式要求

你必须输出合法的 JSON，格式如下（不要输出任何 JSON 以外的内容）：

```json
{{
  "segments": [
    {{
      "number": 1,
      "title": "段标题，如 '第 1 段' 或 '开场'",
      "duration": "时间范围，如 '0-15s'",
      "strategy": "直接生成 / 视频延长 / 独立生成+首帧衔接",
      "shots": [
        {{
          "number": "001",
          "time": "0-3s",
          "shotSize": {{"zh": "远景", "en": "Wide Shot"}},
          "cameraMove": {{"zh": "缓推", "en": "Dolly In"}},
          "description": "画面描述",
          "dialogue": "角色台词（无则空字符串）",
          "audio": "音效/音乐描述"
        }}
      ],{segment_extra}
    }}
  ]
}}
```

**要求**：
- 景别和运镜必须中英双语，从词汇参考中选取
- 时间范围精确到秒，覆盖完整时长
- `dialogue` 无台词时填空字符串 `""`，不要填 `"无"`
- `connection` 仅多段模式的非末段提供，单段模式或末段省略
- JSON 必须合法（转义双引号、无尾逗号）
- 直接输出 JSON，不要用 markdown 代码块包裹"""


_KEY_RULES = """\
## 关键规则

1. **即梦每次生成固定 15 秒** — 每段时长不超过 15 秒
2. **景别运镜中英双语** — 如"近景 Close-Up"、"缓推 Dolly In"
3. **多段衔接策略**：
   - 连续场景、情绪递进 → 视频延长
   - 同风格但场景跳转 → 独立生成 + 首帧衔接
   - 完全不同的场景/风格 → 完全独立生成
4. **质感取向影响镜头设计**：
   - 真实生活感 → 手持微晃、自然光、随意构图
   - 精致制作感 → 稳定器、专业布光、精确构图
5. **段末 2 秒趋稳** — 角色动作趋于平缓，构图清晰，为衔接做准备
6. **台词标注说话人** — 格式：角色A："台词内容"
7. **声音设计同步** — BGM、环境音、对白/旁白全部在分镜中标注"""
