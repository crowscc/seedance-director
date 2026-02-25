#!/usr/bin/env python3
"""
Seedance Director — 豆包 Seed 2.0 Pro 分镜 & 提示词生成器

通过火山引擎 OpenAI 兼容接口调用 doubao-seed-2-0-pro-260215，
由 Skill（SKILL.md）在 Phase 4/5 通过 Bash 工具调用。

调用方式（由 Skill 自动执行）：
  python doubao_generator.py storyboard --brief "创意简报内容"
  python doubao_generator.py prompt --brief "创意简报" --storyboard-file storyboard.md
  python doubao_generator.py full --brief "创意简报" -d output/
"""

import argparse
import os
import sys
from pathlib import Path

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
# 模型配置
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"
BASE_URL = "https://ark.cn-beijing.volces.com/api/compatible/v1"


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
# 豆包客户端（OpenAI 兼容接口）
# ---------------------------------------------------------------------------
class DoubaoClient:
    """通过 OpenAI 兼容接口调用豆包 Seed 2.0 Pro。"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit(
                "错误：缺少依赖 openai\n"
                "请执行: pip install openai"
            )

        self.api_key = api_key or os.getenv("ARK_API_KEY", "")
        self.model = model or os.getenv("ARK_MODEL", DEFAULT_MODEL)

        if not self.api_key:
            sys.exit(
                "错误：未设置 ARK_API_KEY\n"
                "请在环境变量中设置，或在 scripts/.env 文件中配置"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=BASE_URL,
        )

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
            model=self.model,
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
        """流式调用，实时输出到 stderr（stdout 保留给结构化输出）。"""
        stream = self.client.chat.completions.create(
            model=self.model,
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
                sys.stderr.write(delta)
                sys.stderr.flush()
                parts.append(delta)
        sys.stderr.write("\n")
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
    """两步串联：先生成分镜，再转化为提示词。"""
    sys.stderr.write(">>> 第一步：调用豆包生成分镜脚本...\n")
    storyboard = generate_storyboard(client, brief, stream=stream)

    sys.stderr.write("\n>>> 第二步：调用豆包生成即梦提示词 + 操作指引...\n")
    prompt = generate_prompt(client, brief, storyboard, stream=stream)

    return storyboard, prompt


# ---------------------------------------------------------------------------
# CLI — 供 Skill 通过 Bash 工具调用
# ---------------------------------------------------------------------------
def main():
    # 支持从 scripts/.env 加载环境变量
    env_file = SCRIPT_DIR / ".env"
    if env_file.is_file():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            pass  # dotenv 可选，环境变量也可以直接设置

    parser = argparse.ArgumentParser(
        description="豆包 Seed 2.0 Pro — 分镜 & 提示词生成器（供 Skill 调用）",
    )
    subparsers = parser.add_subparsers(dest="command", help="生成模式")

    # --- storyboard: 生成分镜脚本 ---
    sp_sb = subparsers.add_parser("storyboard", help="生成分镜脚本（Phase 4）")
    sp_sb.add_argument("--brief", required=True, help="创意简报")
    sp_sb.add_argument("--output", "-o", help="保存到文件")
    sp_sb.add_argument("--stream", action="store_true", help="流式输出到 stderr")

    # --- prompt: 根据分镜生成即梦提示词 ---
    sp_pr = subparsers.add_parser("prompt", help="生成即梦提示词（Phase 5）")
    sp_pr.add_argument("--brief", required=True, help="创意简报")
    sp_pr.add_argument("--storyboard-file", required=True, help="分镜脚本文件路径")
    sp_pr.add_argument("--output", "-o", help="保存到文件")
    sp_pr.add_argument("--stream", action="store_true", help="流式输出到 stderr")

    # --- full: 一次性生成分镜 + 提示词 ---
    sp_full = subparsers.add_parser("full", help="分镜 + 提示词（Phase 4+5）")
    sp_full.add_argument("--brief", required=True, help="创意简报")
    sp_full.add_argument("--output-dir", "-d", help="输出目录")
    sp_full.add_argument("--stream", action="store_true", help="流式输出到 stderr")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = DoubaoClient()

    if args.command == "storyboard":
        result = generate_storyboard(client, args.brief, stream=args.stream)
        print(result)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            sys.stderr.write(f"已保存到: {args.output}\n")

    elif args.command == "prompt":
        sb_text = Path(args.storyboard_file).read_text(encoding="utf-8")
        result = generate_prompt(client, args.brief, sb_text, stream=args.stream)
        print(result)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            sys.stderr.write(f"已保存到: {args.output}\n")

    elif args.command == "full":
        storyboard, prompt = generate_full(client, args.brief, stream=args.stream)
        # stdout 输出用分隔符分开，方便 Skill 解析
        print("===STORYBOARD===")
        print(storyboard)
        print("===PROMPT===")
        print(prompt)
        if args.output_dir:
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "storyboard.md").write_text(storyboard, encoding="utf-8")
            (out / "seedance-prompt.md").write_text(prompt, encoding="utf-8")
            sys.stderr.write(f"已保存到: {out}/\n")


if __name__ == "__main__":
    main()
