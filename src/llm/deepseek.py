"""DeepSeek LLM provider via the OpenAI-compatible SDK.

The real API key is read from the DEEPSEEK_API_KEY environment variable —
which is populated either by .env (local dev) or by the host's environment
variable settings (production). The key must never be embedded in source.
"""
from __future__ import annotations

import json
import os
from typing import Any

SYSTEM_PROMPT = """你是一个专业 PPT 策划助手。你的任务是把用户提供的文稿整理成结构化幻灯片 JSON。

请严格输出 JSON，不要输出 Markdown，不要输出解释，不要使用代码块。

JSON 顶层必须包含：
- title: 演示主标题（字符串）
- subtitle: 副标题（字符串，可使用英文，显示在副标题位置）
- slides: 数组

slides 是数组，每个元素代表一页幻灯片。每页至少包含：
- type: 取值之一: "cover" | "contents" | "section" | "content" | "closing"
- title: 页面标题（字符串）
- bullets: 字符串数组（封面、目录、致谢页可为空）

可选字段：
- notes: 演讲备注
- layout: PKU 模板布局 hint，可取: cover, contents, section-divider, image-analysis, chart-analysis, timeline, theory-cards, multi-card, framework, vs, swot, method, section-text, closing
- image_prompt: 用于配图生成的英文 prompt
- chart_suggestion: 文字描述应放置何种图表
- speaker_notes: 演讲稿备注（同 notes）
- section: 当前页所属章节名（用于把内容页归到 section 扉页之下）

页面规划建议：
- 通常为 封面 + 目录 + 3-6 章 × (扉页 + 2-3 内容页) + 致谢页，约 12-22 页。
- 每章用一个 type=section 的扉页开头，其 bullets 是 2-4 条章节要点。
- 每条 bullet 控制在 35 个汉字以内，可使用 "标题：正文" 的格式以便渲染为卡片。
- 不要重复封面 / 致谢页；contents 页可省略 bullets 时由前端目录自动生成。
- 不要在 JSON 之外输出任何字符，确保 response_format=json_object 严格合法。
"""


def generate(manuscript: str, options: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. Either:\n"
            "  - copy .env.example to .env and fill in DEEPSEEK_API_KEY, OR\n"
            "  - set LLM_PROVIDER=mock to run the pipeline without a real key."
        )

    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    # Lazy-import openai so `LLM_PROVIDER=mock` works without it installed.
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover - install-error path
        raise RuntimeError(
            "openai package is not installed. Run: pip install -r requirements.txt"
        ) from e

    client = OpenAI(api_key=api_key, base_url=base_url)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": manuscript},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )

    raw = (completion.choices[0].message.content or "").strip()
    if not raw:
        raise RuntimeError("DeepSeek returned empty content")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        snippet = raw[:2000]
        raise RuntimeError(
            f"DeepSeek returned non-JSON content ({e}). First 2000 chars:\n{snippet}"
        ) from e
