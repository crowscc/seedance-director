#!/usr/bin/env python3
"""
Seedance Director — 豆包 AI 分镜 & 提示词生成器

通过火山引擎调用豆包大模型，在特定阶段生成：
  1. 分镜脚本（Phase 4）
  2. 即梦平台提示词（Phase 5）

使用方式：
  python doubao_generator.py --help
  python doubao_generator.py storyboard --brief "15秒温情回家短片，电影写实风格"
  python doubao_generator.py prompt --brief "15秒温情回家短片" --storyboard storyboard.md
  python doubao_generator.py full --brief "15秒咖啡品牌广告，小红书，温馨风格"
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SKILL_DIR = PROJECT_ROOT / "skills" / "seedance-director"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"
EXAMPLES_DIR = SKILL_DIR / "examples"


# ---------------------------------------------------------------------------
# 参考文件加载
# ---------------------------------------------------------------------------
def _read(path: Path) -> str:
    """读取文件内容，文件不存在时返回空字符串。"""
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def load_vocabulary() -> str:
    return _read(REFERENCES_DIR / "vocabulary.md")


def load_platform_capabilities() -> str:
    return _read(REFERENCES_DIR / "platform-capabilities.md")


def load_scene_strategies() -> str:
    return _read(REFERENCES_DIR / "scene-strategies.md")


def load_single_templates() -> str:
    return _read(TEMPLATES_DIR / "single-video.md")


def load_multi_templates() -> str:
    return _read(TEMPLATES_DIR / "multi-segment.md")


def load_single_examples() -> str:
    return _read(EXAMPLES_DIR / "single-examples.md")


def load_multi_examples() -> str:
    return _read(EXAMPLES_DIR / "multi-examples.md")


# ---------------------------------------------------------------------------
# 豆包客户端
# ---------------------------------------------------------------------------
class DoubaoClient:
    """火山引擎方舟平台豆包大模型客户端。"""

    def __init__(self, api_key: str | None = None, endpoint: str | None = None):
        try:
            from volcenginesdkarkruntime import Ark
        except ImportError:
            sys.exit(
                "错误：缺少依赖 volcenginesdkarkruntime\n"
                "请执行: pip install volcenginesdkarkruntime"
            )

        self.api_key = api_key or os.getenv("ARK_API_KEY", "")
        self.endpoint = endpoint or os.getenv("ARK_MODEL_ENDPOINT", "")

        if not self.api_key:
            sys.exit(
                "错误：未设置 ARK_API_KEY\n"
                "请在 .env 文件或环境变量中设置"
            )
        if not self.endpoint:
            sys.exit(
                "错误：未设置 ARK_MODEL_ENDPOINT\n"
                "请在 .env 文件或环境变量中设置"
            )

        os.environ["ARK_API_KEY"] = self.api_key
        self.client = Ark(base_url="https://ark.cn-beijing.volces.com/api/v3")

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """调用豆包聊天补全接口，返回模型回复文本。"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if stream:
            return self._stream_chat(messages, temperature, max_tokens)

        completion = self.client.chat.completions.create(
            model=self.endpoint,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content

    def _stream_chat(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """流式调用，实时打印并返回完整回复。"""
        stream = self.client.chat.completions.create(
            model=self.endpoint,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        parts: list[str] = []
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                parts.append(delta)
        print()  # 换行
        return "".join(parts)


# ---------------------------------------------------------------------------
# System Prompt 构建
# ---------------------------------------------------------------------------
STORYBOARD_SYSTEM_PROMPT = """\
你是一位专业的 AI 视频导演，精通传统影视制作方法论（剧本结构、分镜设计、镜头语言、声音设计）和即梦 Seedance 2.0 平台全部能力。

你的任务是：根据用户提供的创意简报，生成一份**专业的分镜脚本**。

## 输出格式

输出一份完整的分镜表，使用 Markdown 表格格式：

```
## 分镜脚本：[标题]

**叙事结构**：[类型] | **总时长**：[X]秒 | **宽高比**：[比例] | **风格**：[风格]

| 镜号 | 时间 | 景别 | 运镜 | 画面描述 | 角色 / 台词 | 音效/音乐 |
|------|------|------|------|----------|-------------|----------|
| 001  | 0-3s | 近景 Close-Up | 缓推 Dolly In | [描述] | 角色A："[台词]" | [音效] |
```

## 设计原则

1. **景别和运镜中英双语标注**（如"近景 Close-Up"、"缓推 Dolly In"）
2. **台词标注说话人**（角色A："台词"），即梦支持中文对白与口型同步
3. **时间精确到秒**，每个镜头注明起止时间
4. **即梦生成时长固定为 15s**：每个提示词对应一个 15s 片段，多段视频通过视频延长功能衔接
5. **质感取向**：根据内容类型判断"真实生活感"或"精致制作感"
   - 抖音/小红书种草、Vlog → 真实生活感（手持微晃、自然光、微动作）
   - 品牌广告、仙侠CG → 精致制作感（专业布光、稳定运镜）
6. **多段视频**（>15s）需要拆段，标注衔接策略：
   - 连续场景 → 视频延长
   - 场景跳转同风格 → 独立生成 + 首帧衔接
   - 完全不同场景 → 完全独立生成

## 参考知识库

### 镜头语言词汇
{vocabulary}

### 分镜模板（单段 ≤15s）
{single_templates}

### 分镜模板（多段 >15s）
{multi_templates}

### 完整示例
{examples}
"""

PROMPT_SYSTEM_PROMPT = """\
你是一位专业的 AI 视频导演，精通即梦 Seedance 2.0 平台提示词编写。

你的任务是：将分镜脚本转化为**可直接粘贴到即梦平台的提示词**。

## 提示词固定六板块结构

每段提示词必须包含以下六个板块：

```
## 角色 + 参考图
- 角色A（主角）：@图片1 — [外貌、服装、年龄描述]
- 场景参考：@图片2 — [环境描述]

## 背景介绍
[前情、环境、情绪氛围]

## 镜头描述
镜头1（0-3s）：[景别]，[画面内容]，角色A [动作]，角色A："[台词]"，[运镜]
镜头2（3-6s）：[景别]，[画面内容]，[运镜]

## 声音设计
- BGM：[风格/乐器/节奏变化]
- 环境音：[按时间段标注]
- 对白/旁白：写在镜头描述中或此处标注完整文案 + 音色参考

## 风格指令
[统一视觉风格：质感、色调、光线、景深等]

## 禁止项
禁止出现文字、水印、LOGO
```

## 关键原则

1. **提示词只写画面内容和风格**，宽高比/分辨率/帧率/时长在平台 UI 设置，不写进提示词
2. **每个角色独立绑定一张参考图**（@图片N），多角色同框时靠参考图区分
3. **台词必须标注说话人**（角色A："台词"），避免即梦混淆角色对白
4. **@引用必须中文**（@图片1，不是 @image1），标注用途
5. **对白和旁白全部由即梦生成**，不走后期配音
6. **对白写完整台词**，不能只写"描述产品特点"等概括性指令

## 活人感判断

| 场景 | 质感取向 | 写法 |
|------|---------|------|
| 抖音/小红书种草 | 真实生活感 | 微动作、手持微晃、自然光、不完美 |
| 短剧/情感 | 混合 | 日常戏活人感，高潮戏制作感 |
| 品牌广告/仙侠CG | 精致制作感 | 专业布光、稳定运镜、完美构图 |

## 操作指引模板

提示词之后，附上操作指引：

```
## 操作指引

### 1. 素材准备
[列出需要上传的参考图及用途]

### 2. 逐段生成
- 模式：[纯文本生成 / 图生视频]
- 参数：15s / [宽高比] / 最高分辨率
[按段列出操作步骤]

### 3. 段间衔接
[视频延长 / 独立+首帧 / 完全独立]

### 4. 检查要点
- 主体清晰度、运镜流畅度
- 素材一致性（角色/场景跨段统一）
- 声音同步（对白口型、旁白节奏、BGM情绪）
```

## 参考知识库

### 平台能力
{platform_capabilities}

### 场景策略
{scene_strategies}

### 完整示例
{examples}
"""


def build_storyboard_system_prompt() -> str:
    """组装分镜生成的 system prompt，注入参考文件内容。"""
    return STORYBOARD_SYSTEM_PROMPT.format(
        vocabulary=load_vocabulary(),
        single_templates=load_single_templates(),
        multi_templates=load_multi_templates(),
        examples=load_single_examples(),
    )


def build_prompt_system_prompt() -> str:
    """组装提示词生成的 system prompt，注入参考文件内容。"""
    return PROMPT_SYSTEM_PROMPT.format(
        platform_capabilities=load_platform_capabilities(),
        scene_strategies=load_scene_strategies(),
        examples=load_single_examples(),
    )


# ---------------------------------------------------------------------------
# 生成函数
# ---------------------------------------------------------------------------
def generate_storyboard(
    client: DoubaoClient,
    brief: str,
    *,
    stream: bool = False,
) -> str:
    """根据创意简报生成分镜脚本。"""
    system = build_storyboard_system_prompt()
    user = (
        f"请根据以下创意简报生成完整的分镜脚本：\n\n{brief}\n\n"
        "要求：\n"
        "1. 输出专业分镜表（Markdown 表格），景别运镜中英双语\n"
        "2. 如果时长 >15s，需拆段并标注衔接策略\n"
        "3. 根据内容类型判断质感取向（真实生活感 / 精致制作感）\n"
        "4. 时间精确到秒，台词标注说话人"
    )
    return client.chat(system, user, stream=stream)


def generate_prompt(
    client: DoubaoClient,
    brief: str,
    storyboard: str,
    *,
    stream: bool = False,
) -> str:
    """将分镜脚本转化为即梦平台提示词。"""
    system = build_prompt_system_prompt()
    user = (
        f"## 创意简报\n{brief}\n\n"
        f"## 分镜脚本\n{storyboard}\n\n"
        "请将上述分镜转化为可直接粘贴到即梦平台的提示词，"
        "严格遵循六板块结构，并附上操作指引。"
    )
    return client.chat(system, user, stream=stream, max_tokens=8192)


def generate_full(
    client: DoubaoClient,
    brief: str,
    *,
    stream: bool = False,
) -> tuple[str, str]:
    """一次性生成分镜 + 提示词（两步调用）。"""
    print("=" * 60)
    print("📋 第一步：生成分镜脚本")
    print("=" * 60)
    storyboard = generate_storyboard(client, brief, stream=stream)
    if not stream:
        print(storyboard)

    print()
    print("=" * 60)
    print("🎬 第二步：生成即梦提示词 + 操作指引")
    print("=" * 60)
    prompt = generate_prompt(client, brief, storyboard, stream=stream)
    if not stream:
        print(prompt)

    return storyboard, prompt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    load_dotenv(SCRIPT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Seedance Director — 豆包 AI 分镜 & 提示词生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  python doubao_generator.py storyboard --brief "15秒温情回家短片，电影写实风格"\n'
            '  python doubao_generator.py prompt --brief "15秒温情回家短片" --storyboard storyboard.md\n'
            '  python doubao_generator.py full --brief "15秒咖啡品牌广告，小红书，温馨风格"\n'
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="生成模式")

    # --- storyboard ---
    sp_sb = subparsers.add_parser("storyboard", help="仅生成分镜脚本")
    sp_sb.add_argument("--brief", required=True, help="创意简报（描述你想要的视频）")
    sp_sb.add_argument("--output", "-o", help="输出文件路径（默认打印到终端）")
    sp_sb.add_argument("--stream", action="store_true", help="流式输出")

    # --- prompt ---
    sp_pr = subparsers.add_parser("prompt", help="根据分镜生成即梦提示词")
    sp_pr.add_argument("--brief", required=True, help="创意简报")
    sp_pr.add_argument(
        "--storyboard", required=True, help="分镜脚本文件路径（.md）"
    )
    sp_pr.add_argument("--output", "-o", help="输出文件路径")
    sp_pr.add_argument("--stream", action="store_true", help="流式输出")

    # --- full ---
    sp_full = subparsers.add_parser("full", help="一次性生成分镜 + 提示词")
    sp_full.add_argument("--brief", required=True, help="创意简报")
    sp_full.add_argument("--output-dir", "-d", help="输出目录（保存分镜和提示词文件）")
    sp_full.add_argument("--stream", action="store_true", help="流式输出")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = DoubaoClient()

    if args.command == "storyboard":
        result = generate_storyboard(client, args.brief, stream=args.stream)
        if not args.stream:
            print(result)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"\n✅ 分镜脚本已保存到: {args.output}")

    elif args.command == "prompt":
        sb_text = Path(args.storyboard).read_text(encoding="utf-8")
        result = generate_prompt(client, args.brief, sb_text, stream=args.stream)
        if not args.stream:
            print(result)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"\n✅ 即梦提示词已保存到: {args.output}")

    elif args.command == "full":
        storyboard, prompt = generate_full(client, args.brief, stream=args.stream)
        if args.output_dir:
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "storyboard.md").write_text(storyboard, encoding="utf-8")
            (out / "seedance-prompt.md").write_text(prompt, encoding="utf-8")
            print(f"\n✅ 文件已保存到: {out}/")
            print(f"   - storyboard.md     (分镜脚本)")
            print(f"   - seedance-prompt.md (即梦提示词 + 操作指引)")


if __name__ == "__main__":
    main()
