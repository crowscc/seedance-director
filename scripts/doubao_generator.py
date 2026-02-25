#!/usr/bin/env python3
"""
豆包（Doubao）AI 视频分镜 & 即梦提示词生成器

通过火山引擎 Ark API 调用豆包大模型，基于 seedance-director 的参考资料，
自动完成：创意理解 → 分镜脚本生成 → 即梦平台提示词生成 的完整工作流。

使用方法:
    1. 设置环境变量（或创建 .env 文件）:
       - ARK_API_KEY: 火山引擎 Ark API 密钥
       - ARK_MODEL: 豆包模型的 endpoint ID (如 ep-xxxx)
    2. 安装依赖: pip install -r requirements.txt
    3. 运行: python doubao_generator.py
"""

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 参考资料目录（相对于本脚本）
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent / "skills" / "seedance-director"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"
EXAMPLES_DIR = SKILL_DIR / "examples"


def load_env() -> None:
    """从 .env 文件加载环境变量（简易实现，不依赖 python-dotenv）。"""
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                os.environ.setdefault(key, value)


def get_client() -> OpenAI:
    """创建火山引擎 Ark API 客户端。"""
    api_key = os.environ.get("ARK_API_KEY", "")
    if not api_key:
        print("错误：请设置环境变量 ARK_API_KEY（火山引擎 Ark API 密钥）")
        print("  export ARK_API_KEY='your-api-key-here'")
        print("  或者在 scripts/.env 文件中设置")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=ARK_BASE_URL)


def get_model() -> str:
    """获取豆包模型 endpoint ID。"""
    model = os.environ.get("ARK_MODEL", "")
    if not model:
        print("错误：请设置环境变量 ARK_MODEL（豆包模型 endpoint ID，如 ep-xxxx）")
        print("  export ARK_MODEL='ep-xxxx'")
        print("  或者在 scripts/.env 文件中设置")
        sys.exit(1)
    return model


# ---------------------------------------------------------------------------
# 参考资料加载
# ---------------------------------------------------------------------------

def load_reference(filename: str) -> str:
    """加载指定的参考资料文件。"""
    path = REFERENCES_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_template(filename: str) -> str:
    """加载指定的模板文件。"""
    path = TEMPLATES_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_examples(filename: str) -> str:
    """加载指定的示例文件。"""
    path = EXAMPLES_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 系统提示词构建
# ---------------------------------------------------------------------------

DIRECTOR_SYSTEM_PROMPT = """你是一位专业的 AI 视频导演，精通传统影视制作方法论（剧本结构、分镜设计、镜头语言、声音设计）和即梦 Seedance 2.0 平台全部能力。

你的工作方式：像有经验的导演和用户聊天 — 快速抓住创意核心，给出专业方案，输出可直接使用的即梦提示词。

**核心能力**：
- 即梦 Seedance 2.0 完全支持中文对白与口型同步
- 每次生成的视频统一为 15 秒，每个提示词对应一个 15s 片段
- 多段视频通过即梦的视频延长功能衔接

**全程使用中文**思考和输出。"""


def build_storyboard_system_prompt(duration_seconds: int) -> str:
    """构建分镜生成的系统提示词，包含必要的参考资料。"""
    vocabulary = load_reference("vocabulary.md")
    narrative_structures = load_reference("narrative-structures.md")
    scene_strategies = load_reference("scene-strategies.md")

    if duration_seconds <= 15:
        templates = load_template("single-video.md")
    else:
        templates = load_template("multi-segment.md")

    examples = load_examples("single-examples.md")

    return f"""{DIRECTOR_SYSTEM_PROMPT}

---

## 你的任务：生成分镜脚本

根据用户的创意描述，输出专业的分镜表。分镜表格式如下：

| 镜号 | 时间 | 景别 | 运镜 | 画面描述 | 角色 / 台词 | 音效/音乐 |
|------|------|------|------|----------|-------------|----------|

**景别和运镜使用中英双语标注**（如"近景 Close-Up"、"缓推 Dolly In"）。

**质感取向判断**：
- 抖音/小红书种草、Vlog、日常记录 → 真实生活感（手持微晃、自然光、微动作）
- 品牌广告大片、电商产品、仙侠CG → 精致制作感（专业布光、稳定运镜）
- 短剧/情感向 → 混合（日常戏活人感，高潮戏制作感）

**时长策略**：
- ≤15s → 单段，一个提示词
- 16-30s → 2段（段2用视频延长）
- 31-45s → 3段
- >45s → 按场景拆段

---

## 参考资料

### 镜头语言与视觉风格词汇库
{vocabulary}

### 叙事结构库
{narrative_structures}

### 场景化策略
{scene_strategies}

### 分镜模板
{templates}

### 参考示例
{examples}
"""


def build_prompt_system_prompt() -> str:
    """构建即梦提示词生成的系统提示词。"""
    platform_capabilities = load_reference("platform-capabilities.md")
    vocabulary = load_reference("vocabulary.md")
    scene_strategies = load_reference("scene-strategies.md")
    examples = load_examples("single-examples.md")

    return f"""{DIRECTOR_SYSTEM_PROMPT}

---

## 你的任务：将分镜脚本转化为即梦平台提示词

将分镜脚本转化为可直接粘贴到即梦平台的提示词。每段提示词**必须包含以下六个板块**：

```
## 角色 + 参考图
- 角色A（主角）：@图片1 — [外貌、服装、年龄描述]
- 场景参考：@图片N — [环境描述]

## 背景介绍
[前情、环境、情绪氛围]

## 镜头描述
镜头1（0-3s）：[景别]，[画面内容]，角色A [动作]，角色A："[台词]"，[运镜]
镜头2（3-6s）：...

## 声音设计
- BGM：[风格/乐器/节奏变化]
- 环境音：[按时间段标注]
- 对白/旁白：完整文案 + 音色参考

## 风格指令
[统一视觉风格：质感、色调、光线、景深等]

## 禁止项
禁止出现文字、水印、LOGO
```

**关键原则**：
- 提示词只写画面内容和风格，不写宽高比等技术参数
- 每个角色独立绑定一张参考图（@图片N）
- 台词必须标注说话人
- @引用必须中文（@图片1 而非 @image1）
- 对白和旁白必须写出完整文案，不能只写"描述产品特点"等概括性指令
- 所有内容（画面、对白、BGM）全部在即梦提示词中生成，不走后期

---

## 参考资料

### 即梦平台能力
{platform_capabilities}

### 镜头语言词汇
{vocabulary}

### 场景化策略与示例
{scene_strategies}

### 完整示例
{examples}
"""


# ---------------------------------------------------------------------------
# 交互式创意收集
# ---------------------------------------------------------------------------

def collect_creative_input() -> dict:
    """通过交互式问答收集用户创意信息。"""
    print("\n" + "=" * 60)
    print("  🎬 AI 视频导演 — 创意收集")
    print("=" * 60)

    info = {}

    # 主题
    print("\n📌 请描述你的创意（拍什么、讲什么故事）：")
    info["topic"] = input("> ").strip()
    if not info["topic"]:
        print("创意描述不能为空！")
        sys.exit(1)

    # 时长
    print("\n⏱️  视频时长（秒）[默认 15]：")
    duration_input = input("> ").strip()
    info["duration"] = int(duration_input) if duration_input.isdigit() else 15

    # 风格
    print("\n🎨 视觉风格 [回车跳过，由 AI 推荐]：")
    print("   参考：电影写实 / 3D CG / 赛博朋克 / 中国风 / 商业广告 / 日系清新 / 复古胶片")
    style_input = input("> ").strip()
    info["style"] = style_input if style_input else None

    # 宽高比
    print("\n📐 画面比例 [默认 16:9]：")
    print("   可选：16:9 / 9:16 / 1:1")
    ratio_input = input("> ").strip()
    info["aspect_ratio"] = ratio_input if ratio_input else "16:9"

    # 素材
    print("\n📁 你有什么素材？[回车跳过 = 无素材，纯文本生成]：")
    print("   例如：3张角色参考图 / 一段参考视频 / 无")
    assets_input = input("> ").strip()
    info["assets"] = assets_input if assets_input else "无素材，纯文本生成"

    # 声音
    print("\n🔊 声音需求 [回车跳过 = BGM]：")
    print("   例如：需要角色对白 / 旁白 / 纯BGM / BGM+环境音")
    audio_input = input("> ").strip()
    info["audio"] = audio_input if audio_input else "BGM"

    # 额外要求
    print("\n💡 其他要求或补充说明 [回车跳过]：")
    extra_input = input("> ").strip()
    info["extra"] = extra_input if extra_input else None

    return info


def format_creative_brief(info: dict) -> str:
    """将用户创意信息格式化为文本描述。"""
    parts = [f"**创意描述**：{info['topic']}"]
    parts.append(f"**视频时长**：{info['duration']}秒")
    if info.get("style"):
        parts.append(f"**视觉风格**：{info['style']}")
    parts.append(f"**画面比例**：{info.get('aspect_ratio', '16:9')}")
    parts.append(f"**素材情况**：{info.get('assets', '无')}")
    parts.append(f"**声音需求**：{info.get('audio', 'BGM')}")
    if info.get("extra"):
        parts.append(f"**补充说明**：{info['extra']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 豆包 API 调用
# ---------------------------------------------------------------------------

def call_doubao(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
) -> str:
    """调用豆包大模型并返回回复文本。"""
    print("\n⏳ 正在调用豆包生成中，请稍候...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"\n❌ 调用豆包 API 失败：{e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 主工作流
# ---------------------------------------------------------------------------

def phase1_understand(client: OpenAI, model: str, info: dict) -> str:
    """Phase 1: 理解创意 — 让豆包分析用户创意并补充信息。"""
    brief = format_creative_brief(info)

    system_prompt = f"""{DIRECTOR_SYSTEM_PROMPT}

你的任务是分析用户的创意描述，评估信息完整度（主题、时长、风格、素材、声音五个维度），
然后给出：
1. 创意核心总结（1-2句话）
2. 推荐的叙事结构（从16种中选最合适的1-2种，说明理由）
3. 推荐的视觉风格（如果用户没指定）
4. 分段策略（如果时长>15秒）
5. 补充建议

输出格式简洁专业，使用中文。"""

    result = call_doubao(
        client, model, system_prompt,
        f"请分析以下创意：\n\n{brief}",
    )
    return result


def phase4_storyboard(client: OpenAI, model: str, info: dict, analysis: str) -> str:
    """Phase 4: 生成分镜脚本。"""
    brief = format_creative_brief(info)
    system_prompt = build_storyboard_system_prompt(info["duration"])

    user_message = f"""请根据以下创意和分析结果，生成完整的分镜脚本。

## 用户创意
{brief}

## 创意分析
{analysis}

## 要求
1. 输出标准分镜表（markdown 表格）
2. 景别和运镜中英双语标注
3. 时间精确到秒
4. 台词写完整内容（不要概括）
5. 如果时长 >15s，按段拆分并标注衔接策略
"""

    result = call_doubao(client, model, system_prompt, user_message)
    return result


def phase5_prompts(client: OpenAI, model: str, info: dict, storyboard: str) -> str:
    """Phase 5: 生成即梦平台提示词 + 操作指引。"""
    brief = format_creative_brief(info)
    system_prompt = build_prompt_system_prompt()

    user_message = f"""请将以下分镜脚本转化为可直接粘贴到即梦平台的提示词。

## 用户创意
{brief}

## 分镜脚本
{storyboard}

## 要求
1. 每段提示词包含完整六板块（角色+参考图、背景介绍、镜头描述、声音设计、风格指令、禁止项）
2. 如果是多段视频，逐段输出提示词并标注衔接方式
3. 最后附上操作指引（素材准备、逐段生成、段间衔接、检查要点）
4. 所有内容在即梦中生成，不引导用户使用外部工具做后期
"""

    result = call_doubao(client, model, system_prompt, user_message)
    return result


def save_output(info: dict, analysis: str, storyboard: str, prompts: str) -> Path:
    """将结果保存到 markdown 文件。"""
    output_dir = SCRIPT_DIR / "output"
    output_dir.mkdir(exist_ok=True)

    # 使用创意主题的前20个字作为文件名
    safe_name = info["topic"][:20].replace(" ", "_").replace("/", "_")
    output_path = output_dir / f"{safe_name}.md"

    content = f"""# 🎬 AI 视频分镜 & 提示词

> 由豆包大模型（火山引擎）自动生成

---

## 创意信息

{format_creative_brief(info)}

---

## 创意分析

{analysis}

---

## 分镜脚本

{storyboard}

---

## 即梦平台提示词 & 操作指引

{prompts}
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> None:
    """主入口。"""
    # 加载环境变量
    load_env()

    # 初始化 API 客户端
    client = get_client()
    model = get_model()

    print("\n" + "=" * 60)
    print("  🎬 豆包 AI 视频导演 — 分镜 & 提示词生成器")
    print("  基于 seedance-director 参考资料")
    print("  调用火山引擎豆包大模型")
    print("=" * 60)

    # 收集创意
    info = collect_creative_input()

    # Phase 1: 创意分析
    print("\n" + "-" * 40)
    print("📋 Phase 1: 创意分析")
    print("-" * 40)
    analysis = phase1_understand(client, model, info)
    print("\n" + analysis)

    # 确认是否继续
    print("\n是否继续生成分镜？[回车继续 / q 退出]")
    if input("> ").strip().lower() == "q":
        print("已退出。")
        return

    # Phase 4: 分镜脚本
    print("\n" + "-" * 40)
    print("🎬 Phase 4: 生成分镜脚本")
    print("-" * 40)
    storyboard = phase4_storyboard(client, model, info, analysis)
    print("\n" + storyboard)

    # 确认是否继续
    print("\n是否继续生成即梦提示词？[回车继续 / q 退出 / e 修改分镜]")
    user_choice = input("> ").strip().lower()
    if user_choice == "q":
        print("已退出。")
        return
    elif user_choice == "e":
        print("\n请输入修改意见：")
        edit_feedback = input("> ").strip()
        if edit_feedback:
            storyboard = phase4_storyboard(
                client, model, info,
                f"{analysis}\n\n用户反馈：{edit_feedback}\n\n上一版分镜：\n{storyboard}",
            )
            print("\n" + storyboard)

    # Phase 5: 即梦提示词
    print("\n" + "-" * 40)
    print("✨ Phase 5: 生成即梦提示词 + 操作指引")
    print("-" * 40)
    prompts = phase5_prompts(client, model, info, storyboard)
    print("\n" + prompts)

    # 保存结果
    output_path = save_output(info, analysis, storyboard, prompts)
    print("\n" + "=" * 60)
    print(f"✅ 完成！结果已保存到：{output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
