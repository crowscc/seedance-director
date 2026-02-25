#!/usr/bin/env python3
"""
Seedance Director — 豆包 AI 视频导演

使用火山引擎豆包模型（doubao-seed-2-0-pro-260215），交互式生成即梦平台的分镜脚本和提示词。

使用前请设置环境变量：
  export ARK_API_KEY="your-api-key"

可选环境变量：
  export ARK_MODEL="doubao-seed-2-0-pro-260215"   # 默认值，可改为其他模型
  export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"  # 默认值

运行：
  pip install -r requirements.txt
  python doubao_director.py
"""

import json
import os
import pathlib
import re
import sys
import textwrap

from openai import OpenAI

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR / "skills" / "seedance-director"

DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("错误：请设置环境变量 ARK_API_KEY（火山引擎 API Key）")
        print("  export ARK_API_KEY=your-api-key-here")
        print()
        print("获取方式：https://console.volcengine.com/ark")
        sys.exit(1)
    base_url = os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    return os.environ.get("ARK_MODEL", DEFAULT_MODEL)


# ---------------------------------------------------------------------------
# 加载参考文件
# ---------------------------------------------------------------------------

def _load_ref(relpath: str) -> str:
    """加载 skill 目录下的参考文件，不存在则返回空字符串。"""
    fp = SKILL_DIR / relpath
    if fp.exists():
        return fp.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# 调用豆包 API
# ---------------------------------------------------------------------------

def _call_stream(
    client: OpenAI,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> str:
    """流式调用豆包 API，实时打印并返回完整文本。

    自动为 doubao-seed-2-0 系列模型关闭深度思考（thinking disabled），
    因为分镜/提示词生成属于创意写作而非推理任务。
    """
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    # doubao-seed-2-0 系列支持 thinking 参数；关闭深度思考以减少延迟
    if "seed-2" in model:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    try:
        stream = client.chat.completions.create(**kwargs)
        chunks: list[str] = []
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                chunks.append(delta.content)
        print()  # 换行
        return "".join(chunks)
    except Exception as exc:
        print(f"\n调用豆包 API 失败: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI 交互
# ---------------------------------------------------------------------------

_DIVIDER = "=" * 60


def _ask_choice(prompt: str, options: list[str]) -> str:
    """向用户展示选项列表，返回选中的文本。"""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print(f"  0. 自定义")
    while True:
        raw = input("\n请选择 (输入数字): ").strip()
        if raw == "0":
            custom = input("请输入: ").strip()
            if custom:
                return custom
            print("输入不能为空，请重试")
            continue
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("输入无效，请重试")


def _collect_params() -> dict:
    """交互式收集视频参数。"""
    print(_DIVIDER)
    print("  Seedance Director — 豆包 AI 视频导演")
    print(_DIVIDER)
    print("\n请描述你的视频创意（可以简单也可以详细）：")
    idea = input("> ").strip()
    if not idea:
        print("创意描述不能为空")
        sys.exit(1)

    duration = _ask_choice("视频时长：", [
        "15 秒（单段）",
        "30 秒（2 段）",
        "45 秒（3 段）",
        "60 秒（4 段）",
    ])

    aspect_ratio = _ask_choice("宽高比：", [
        "9:16 竖屏（抖音 / 小红书）",
        "16:9 横屏（B站 / YouTube）",
        "1:1 方形",
    ])

    narrative = _ask_choice("叙事结构：", [
        "起承转合 — 经典四段式，万能结构",
        "Hook-反转 — 开头即高潮，靠反转传播",
        "对比型 — Before/After 强反差",
        "悬念型 — 问题驱动，逐步揭秘",
        "教程型 — 结果先行，步骤简洁",
        "情绪浪潮型 — 情绪曲线驱动节奏",
        "POV 代入型 — 第一人称视角",
        "日常切片型 — 生活片段，不刻意叙事",
        "AIDA 营销型 — 注意→兴趣→欲望→行动",
        "清单盘点型 — 列表式，条目化呈现",
    ])

    style = _ask_choice("视觉风格：", [
        "电影写实 — 真实世界、电影级光影",
        "日系清新 — 柔光自然色调",
        "赛博朋克 — 霓虹、高科技、雨夜",
        "中国风水墨 — 水墨画风格、留白写意",
        "商业广告 — 精致布光、产品摄影",
        "3D CG 渲染 — 三维渲染、光追",
        "复古胶片 — 胶片颗粒、褪色暖调",
        "纪录片风格 — 手持跟拍、自然光",
        "Vlog 手持 — 生活感、随性",
        "氛围感 / 情绪向 — 情绪驱动画面",
    ])

    audio = _ask_choice("声音需求：", [
        "BGM + 环境音（无人声）",
        "旁白 + BGM",
        "台词对白 + BGM + 环境音",
        "纯 BGM",
        "无声",
    ])

    assets = _ask_choice("素材情况：", [
        "没有素材，纯文本生成",
        "有角色参考图",
        "有场景参考图",
        "有角色图 + 场景图",
        "有参考视频",
    ])

    return {
        "idea": idea,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "narrative": narrative,
        "style": style,
        "audio": audio,
        "assets": assets,
    }


def _format_params(params: dict) -> str:
    """将参数格式化为文本块。"""
    return textwrap.dedent(f"""\
        - 创意描述：{params['idea']}
        - 时长：{params['duration']}
        - 宽高比：{params['aspect_ratio']}
        - 叙事结构：{params['narrative']}
        - 视觉风格：{params['style']}
        - 声音需求：{params['audio']}
        - 素材情况：{params['assets']}""")


# ---------------------------------------------------------------------------
# Phase 4：生成分镜脚本
# ---------------------------------------------------------------------------

_STORYBOARD_SYSTEM = """\
你是一位专业的 AI 视频导演，精通传统影视制作方法论和即梦 Seedance 2.0 平台。
你的任务是根据用户的创意和参数，生成一份专业的分镜脚本。

## 分镜设计规范

### 质感取向
- 抖音/小红书种草、Vlog、日常记录 → 真实生活感（手持微晃、自然光、微动作）
- 品牌广告、电商、仙侠 CG → 精致制作感（专业布光、稳定运镜）
- 短剧/情感向 → 混合（日常戏活人感，高潮戏制作感）
- 用户显式选择的风格始终优先

### 即梦生成限制
- 每次生成 15 秒视频
- ≤15s：单段生成
- 16-30s：2 段，段 2 用视频延长
- 31s+：每段独立生成，用角色三视图 + 场景图 + 末帧参考衔接

### 输出格式

请直接输出分镜表，格式如下：

## 分镜脚本：[标题]

**叙事结构**：[类型] | **总时长**：[X]秒 | **宽高比**：[比例] | **风格**：[风格]

| 镜号 | 时间 | 景别 | 运镜 | 画面描述 | 角色 / 台词 | 音效 / 音乐 |
|------|------|------|------|----------|-------------|----------|
| 001 | 0-3s | 近景 Close-Up | 缓推 Dolly In | [描述] | [角色台词] | [音效] |

如果是多段视频（>15s），请：
1. 先输出完整故事大纲
2. 按段拆分（16-30s→2 段 / 31-45s→3 段 / 46-60s→4 段）
3. 每段都输出分镜表
4. 段与段之间标注衔接策略（视频延长 / 独立生成 + 首帧衔接 / 完全独立）

注意：
- 景别和运镜使用中英双语（如 "近景 Close-Up"、"缓推 Dolly In"）
- 台词标注说话人（角色A："台词"）
- 时间精确到秒
- 每镜头的画面描述要具体、可执行
- 全程使用中文输出

{vocabulary}

{narratives}

{scene_strategies}
"""


def _generate_storyboard(
    client: OpenAI,
    model: str,
    params: dict,
) -> str:
    vocabulary = _load_ref("references/vocabulary.md")
    narratives = _load_ref("references/narrative-structures.md")
    scene_strategies = _load_ref("references/scene-strategies.md")

    system = _STORYBOARD_SYSTEM.format(
        vocabulary=vocabulary,
        narratives=narratives,
        scene_strategies=scene_strategies,
    )

    user_msg = f"请根据以下信息生成分镜脚本：\n\n{_format_params(params)}"

    print(f"\n{'─' * 40}")
    print("⏳ 正在生成分镜脚本…\n")

    return _call_stream(client, model, [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ])


def _revise_storyboard(
    client: OpenAI,
    model: str,
    params: dict,
    storyboard: str,
    feedback: str,
) -> str:
    vocabulary = _load_ref("references/vocabulary.md")

    system = (
        "你是一位专业的 AI 视频导演。用户对之前的分镜脚本有修改意见，"
        "请根据反馈修改并输出完整的新分镜脚本，保持原有格式。\n\n"
        f"### 镜头语言参考\n{vocabulary[:4000]}"
    )

    user_msg = (
        f"## 项目参数\n{_format_params(params)}\n\n"
        f"## 当前分镜脚本\n{storyboard}\n\n"
        f"## 修改意见\n{feedback}\n\n"
        "请输出修改后的完整分镜脚本。"
    )

    print(f"\n{'─' * 40}")
    print("⏳ 正在修改分镜脚本…\n")

    return _call_stream(client, model, [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ])


# ---------------------------------------------------------------------------
# Phase 5：生成即梦提示词
# ---------------------------------------------------------------------------

_JSON_SCHEMA_EXAMPLE = {
    "project": {
        "title": "项目标题",
        "narrativeStructure": "叙事结构名称",
        "duration": "总时长，如 45秒",
        "aspectRatio": "宽高比，如 9:16",
        "style": "视觉风格",
    },
    "assets": [
        {
            "name": "素材名称",
            "type": "character|scene|keyframe",
            "purpose": "用途说明",
        }
    ],
    "segments": [
        {
            "number": 1,
            "title": "段标题",
            "duration": "时间范围，如 0-15s",
            "strategy": "直接生成|视频延长",
            "shots": [
                {
                    "number": "001",
                    "time": "0-3s",
                    "shotSize": {"zh": "近景", "en": "Close-Up"},
                    "cameraMove": {"zh": "缓推", "en": "Dolly In"},
                    "description": "画面描述",
                    "dialogue": "台词（无则空字符串）",
                    "audio": "音效描述",
                }
            ],
            "promptSections": {
                "characterRef": "角色 + 参考图内容",
                "background": "背景介绍内容",
                "shotDescription": "镜头描述内容",
                "soundDesign": "声音设计内容",
                "styleDirective": "风格指令内容",
                "prohibitions": "禁止出现文字、水印、LOGO",
            },
        }
    ],
    "operationGuide": [
        {"title": "步骤标题", "description": "步骤描述"}
    ],
    "tips": [
        {"title": "建议标题", "description": "建议描述"}
    ],
}


_PROMPT_SYSTEM = """\
你是一位专业的 AI 视频导演，现在需要将分镜脚本转化为可直接粘贴到即梦 Seedance 2.0 平台的提示词。

{platform}

## 提示词规范

每段提示词必须包含以下六个板块：

### 角色 + 参考图
- 每个角色独立绑定参考图（@图片N）
- 场景也要独立参考图

### 背景介绍
[前情、环境、情绪氛围]

### 镜头描述
镜头1（0-3s）：[景别]，[画面内容]，角色A [动作]，角色A："[台词]"，[运镜]

### 声音设计
- BGM：[风格/乐器/节奏变化]
- 环境音：[按时间段标注]
- 对白/旁白：[完整文案 + 音色参考]

### 风格指令
[统一视觉风格]

### 禁止项
禁止出现文字、水印、LOGO

## 关键原则
- 提示词只写画面内容和风格，技术参数在平台 UI 设置
- @引用必须中文（@图片1 不是 @image1）
- 台词必须标注说话人
- 对白和旁白全部由即梦生成，不走后期配音
- 必须写出实际要说的话，不能只写概括性指令

## 活人感判断
- 抖音/小红书种草、Vlog → 真实生活感：微动作、生活痕迹、手持微晃、自然反应
- 品牌广告、电商、仙侠 CG → 精致制作感：专业布光、稳定运镜、完美构图
- 短剧/情感向 → 混合

## 输出要求

请按以下顺序输出：

1. 每段的即梦提示词（六板块结构，可直接复制粘贴）
2. 操作指引（素材准备 → 逐段生成 → 段间衔接 → 检查要点）
3. 优化建议（2-3 条）

最后，请在输出末尾附上一个 JSON 数据块，用 ```json ``` 包裹。
JSON 格式严格遵循以下 Schema（字段不可增删）：

```
{json_schema}
```

注意：
- dialogue 无台词时填空字符串 ""，不要填 "无"
- connection 仅多段模式的非末段提供，单段或末段省略
- promptSections 的 6 个字段不可增删
- JSON 必须合法（双引号、无尾逗号）
- 全程使用中文输出
"""


def _generate_prompts(
    client: OpenAI,
    model: str,
    params: dict,
    storyboard: str,
) -> str:
    platform = _load_ref("references/platform-capabilities.md")

    system = _PROMPT_SYSTEM.format(
        platform=platform,
        json_schema=json.dumps(_JSON_SCHEMA_EXAMPLE, ensure_ascii=False, indent=2),
    )

    user_msg = (
        f"请将以下分镜脚本转化为即梦平台提示词并生成 JSON 数据。\n\n"
        f"## 项目参数\n{_format_params(params)}\n\n"
        f"## 分镜脚本\n{storyboard}"
    )

    print(f"\n{'─' * 40}")
    print("⏳ 正在生成即梦提示词…\n")

    return _call_stream(
        client, model,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
    )


# ---------------------------------------------------------------------------
# HTML 输出
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict | None:
    """从响应文本中提取 JSON 数据。"""
    # 优先查找 ```json ... ``` 代码块
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 退而求其次：查找包含 "project" 键的 JSON 对象
    m = re.search(r'\{[\s\S]*?"project"[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _generate_html(data: dict) -> pathlib.Path | None:
    """将 JSON 数据注入 HTML 模板并写入 output.html。"""
    template_path = SKILL_DIR / "templates" / "output.html"
    if not template_path.exists():
        print("⚠️  HTML 模板文件未找到，跳过 HTML 生成")
        return None

    html = template_path.read_text(encoding="utf-8")
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    html = html.replace('{"_placeholder": true}', json_str)

    output_path = pathlib.Path.cwd() / "output.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> None:
    client = _get_client()
    model = _get_model()

    # ── Phase 1-2：收集参数 ──
    params = _collect_params()

    print(f"\n{_DIVIDER}")
    print("  参数确认")
    print(_DIVIDER)
    print(_format_params(params))

    # ── Phase 4：生成分镜 ──
    storyboard = _generate_storyboard(client, model, params)

    # 确认 / 修改循环
    while True:
        print(f"\n{'─' * 40}")
        print("  y = 满意，继续生成提示词")
        print("  n = 不满意，重新生成")
        print("  e = 给出修改意见")
        choice = input("\n对分镜是否满意？ (y/n/e): ").strip().lower()

        if choice == "y":
            break
        elif choice == "n":
            storyboard = _generate_storyboard(client, model, params)
        elif choice == "e":
            feedback = input("请输入修改意见: ").strip()
            if feedback:
                storyboard = _revise_storyboard(
                    client, model, params, storyboard, feedback
                )
        else:
            print("请输入 y、n 或 e")

    # ── Phase 5：生成即梦提示词 ──
    result = _generate_prompts(client, model, params, storyboard)

    # ── 提取 JSON 并生成 HTML ──
    data = _extract_json(result)
    if data:
        output_path = _generate_html(data)
        if output_path:
            print(f"\n✅ 可视化页面已生成：{output_path}")
            try:
                import webbrowser
                webbrowser.open(output_path.as_uri())
                print("   已在浏览器中打开")
            except Exception:
                print("   请手动在浏览器中打开该文件")
    else:
        print("\n⚠️  未能从响应中提取 JSON 数据，HTML 页面未生成")
        print("   你可以复制上方的提示词直接粘贴到即梦平台使用")

    print(f"\n{_DIVIDER}")
    print("  完成！祝拍摄顺利 🎬")
    print(_DIVIDER)


if __name__ == "__main__":
    main()
