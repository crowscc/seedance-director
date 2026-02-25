#!/usr/bin/env python3
"""
Doubao Bridge — 火山引擎豆包 API 桥接脚本。

从 stdin 读取 JSON 输入，调用豆包生成分镜脚本或即梦提示词，输出 JSON 到 stdout。

用法：
    echo '{"mode":"storyboard", "project":{...}}' | python3 doubao_bridge.py
    echo '{"mode":"prompt", "project":{...}, "storyboard":"..."}' | python3 doubao_bridge.py
    echo '{"mode":"storyboard", ...}' | python3 doubao_bridge.py --dry-run

环境变量：
    ARK_API_KEY  — 火山引擎 ARK API Key（必需）
    ARK_MODEL    — 模型 ID（默认 doubao-seed-2-0-pro-260215）
    ARK_BASE_URL — API 地址（默认 https://ark.cn-beijing.volces.com/api/v3）
"""

import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# 输出工具
# ---------------------------------------------------------------------------

def _output_json(obj: dict) -> None:
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _output_error(error_type: str, message: str) -> None:
    _output_json({"success": False, "error": message, "error_type": error_type})


def _output_success(data: dict) -> None:
    _output_json({"success": True, "data": data})


# ---------------------------------------------------------------------------
# JSON 响应解析（多策略）
# ---------------------------------------------------------------------------

def _parse_response(raw_text: str) -> dict:
    """尝试从豆包返回的文本中提取 JSON。

    策略优先级：
    1. 直接 JSON 解析
    2. 从 markdown 代码块中提取
    3. 从最外层花括号提取
    4. 返回原始文本（标记解析失败）
    """
    text = raw_text.strip()

    # 策略 1：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 策略 2：markdown 代码块
    m = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 策略 3：最外层花括号
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    # 策略 4：解析失败，返回原始文本
    return {"_raw": text, "_parseError": True}


# ---------------------------------------------------------------------------
# API 调用
# ---------------------------------------------------------------------------

def _call_doubao(system_prompt: str, user_message: str) -> str:
    """调用火山引擎 ARK API（OpenAI 兼容）。"""
    from openai import OpenAI

    api_key = os.environ.get("ARK_API_KEY", "")
    base_url = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.environ.get("ARK_MODEL", "doubao-seed-2-0-pro-260215")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# 模式处理
# ---------------------------------------------------------------------------

def _handle_storyboard(data: dict, dry_run: bool = False) -> None:
    """Phase 4：生成分镜脚本。"""
    from prompts.storyboard_system import build_system_prompt, build_user_message

    project = data.get("project", {})
    system_prompt = build_system_prompt(project)
    user_message = build_user_message(data)

    if dry_run:
        _output_json({
            "dry_run": True,
            "system_prompt": system_prompt,
            "user_message": user_message,
            "system_prompt_length": len(system_prompt),
            "user_message_length": len(user_message),
        })
        return

    raw_response = _call_doubao(system_prompt, user_message)
    parsed = _parse_response(raw_response)

    if parsed.get("_parseError"):
        # 解析失败但 API 调用成功，返回原始文本供 Claude 处理
        _output_json({
            "success": True,
            "data": {"rawText": parsed["_raw"], "parseWarning": "豆包返回内容非标准 JSON，已返回原始文本"},
        })
        return

    # 包装为标准输出格式
    if "segments" in parsed:
        _output_success(parsed)
    else:
        _output_success({"segments": [parsed] if parsed else []})


def _handle_prompt(data: dict, dry_run: bool = False) -> None:
    """Phase 5：生成即梦提示词。"""
    from prompts.seedance_system import build_system_prompt, build_user_message

    project = data.get("project", {})
    system_prompt = build_system_prompt(project)
    user_message = build_user_message(data)

    if dry_run:
        _output_json({
            "dry_run": True,
            "system_prompt": system_prompt,
            "user_message": user_message,
            "system_prompt_length": len(system_prompt),
            "user_message_length": len(user_message),
        })
        return

    raw_response = _call_doubao(system_prompt, user_message)
    parsed = _parse_response(raw_response)

    if parsed.get("_parseError"):
        _output_json({
            "success": True,
            "data": {"rawText": parsed["_raw"], "parseWarning": "豆包返回内容非标准 JSON，已返回原始文本"},
        })
        return

    if "segments" in parsed:
        _output_success(parsed)
    else:
        _output_success({"segments": [parsed] if parsed else [], "operationGuide": [], "tips": []})


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main() -> None:
    dry_run = "--dry-run" in sys.argv

    # 读取 stdin
    try:
        raw_input = sys.stdin.read()
    except KeyboardInterrupt:
        _output_error("input_error", "输入被中断")
        return

    if not raw_input.strip():
        _output_error("input_error", "未收到输入。请通过 stdin 传入 JSON 数据。")
        return

    # 解析 JSON
    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        _output_error("input_error", f"输入 JSON 解析失败：{e}")
        return

    # 校验 mode
    mode = data.get("mode")
    if mode not in ("storyboard", "prompt"):
        _output_error("input_error", f"无效的 mode：'{mode}'。必须为 'storyboard' 或 'prompt'。")
        return

    # 校验 API Key（非 dry-run 时）
    if not dry_run:
        api_key = os.environ.get("ARK_API_KEY", "")
        if not api_key:
            _output_error(
                "auth_error",
                "ARK_API_KEY 环境变量未设置。请执行：export ARK_API_KEY='your-api-key'",
            )
            return

    # 执行
    try:
        if mode == "storyboard":
            _handle_storyboard(data, dry_run=dry_run)
        else:
            _handle_prompt(data, dry_run=dry_run)
    except ImportError as e:
        if "openai" in str(e):
            _output_error(
                "input_error",
                "openai 包未安装。请执行：pip3 install openai",
            )
        else:
            _output_error("input_error", f"导入错误：{e}")
    except Exception as e:
        # 区分常见的 API 错误类型
        error_name = type(e).__name__
        if "AuthenticationError" in error_name:
            _output_error("auth_error", "API Key 无效或已过期。请检查 ARK_API_KEY。")
        elif "RateLimitError" in error_name:
            _output_error("api_error", "API 请求频率超限，请稍后重试。")
        elif "Timeout" in error_name:
            _output_error("timeout_error", "API 请求超时，请重试。")
        else:
            _output_error("api_error", f"调用豆包 API 失败：{error_name}: {e}")


if __name__ == "__main__":
    main()
