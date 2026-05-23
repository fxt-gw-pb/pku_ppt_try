"""Mock LLM provider: returns a deterministic sample slide_json.

Used when LLM_PROVIDER=mock. Lets the rest of the pipeline (schema → render
→ export → API → frontend) be exercised end-to-end without a real key.
The manuscript text is read for the title-from-first-heading heuristic so
that different inputs produce visibly different mock decks.
"""
from __future__ import annotations

import re
from typing import Any


def _extract_title(manuscript: str) -> str:
    for line in manuscript.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip() or "示例演示稿"
        if line:
            return line[:40]
    return "示例演示稿"


def generate(manuscript: str, options: dict[str, Any]) -> dict[str, Any]:
    title = _extract_title(manuscript or "")
    return {
        "title": title,
        "subtitle": "GRADUATION DEFENSE / OPENING REPORT",
        "slides": [
            {"type": "cover", "title": title, "bullets": []},
            {
                "type": "contents",
                "title": "目录",
                "bullets": [
                    "背景与意义",
                    "国内外研究现状",
                    "研究思路与内容",
                    "研究方法",
                    "结论与展望",
                ],
            },
            {
                "type": "section",
                "title": "背景与意义",
                "bullets": ["宏观背景", "核心问题", "理论与实践意义"],
            },
            {
                "type": "content",
                "title": "选题背景",
                "section": "背景与意义",
                "bullets": [
                    "外部环境的驱动：行业趋势、政策导向或社会需求持续上升",
                    "现有方案的局限：在关键指标上仍存在明显瓶颈",
                    "新方向的可能性：新工具与新数据为突破提供契机",
                ],
                "layout": "multi-card",
            },
            {
                "type": "content",
                "title": "研究意义",
                "section": "背景与意义",
                "bullets": [
                    "理论价值：完善已有理论框架",
                    "方法价值：提出可推广工作流",
                    "应用价值：支撑具体应用场景",
                ],
                "layout": "multi-card",
            },
            {
                "type": "section",
                "title": "国内外研究现状",
                "bullets": ["主要流派", "技术演进", "现有缺口"],
            },
            {
                "type": "content",
                "title": "主流路径与共性短板",
                "section": "国内外研究现状",
                "bullets": [
                    "路径 A：原创理论领先，工程化偏弱",
                    "路径 B：工程化激进，原创度有限",
                    "路径 C：新兴方法，潜力可期",
                    "共性：跨场景泛化能力不足",
                ],
                "layout": "multi-card",
            },
            {
                "type": "section",
                "title": "研究思路与内容",
                "bullets": ["核心问题", "总体框架", "创新点定位"],
            },
            {
                "type": "content",
                "title": "总体框架",
                "section": "研究思路与内容",
                "bullets": [
                    "问题界定：明确研究对象与边界",
                    "理论建模：在已有理论上提出新假设",
                    "数据采集：梳理来源与采集方案",
                    "分析验证：实证检验并量化结论",
                ],
                "layout": "multi-card",
            },
            {
                "type": "section",
                "title": "研究方法",
                "bullets": ["方法体系", "技术路线", "实验设计"],
            },
            {
                "type": "content",
                "title": "四类互补方法",
                "section": "研究方法",
                "bullets": [
                    "文献调研：定位空白",
                    "消融实验：定位贡献",
                    "多中心评测：验证泛化",
                    "复杂度分析：支撑工程可行性",
                ],
                "layout": "multi-card",
            },
            {
                "type": "section",
                "title": "结论与展望",
                "bullets": ["主要结论", "创新点", "不足与展望"],
            },
            {
                "type": "content",
                "title": "主要结论",
                "section": "结论与展望",
                "bullets": [
                    "建立了关键变量与目标指标的定量关联",
                    "证实新机制 A 与 B 的协同效应",
                    "在真实场景下完成多轮验证",
                    "工程实现完成规模化扩展",
                ],
                "layout": "section-text",
            },
            {
                "type": "closing",
                "title": "感谢您的倾听！",
                "bullets": [],
                "notes": "感谢导师的悉心指导，感谢各位老师与同学的支持。敬请各位老师批评指正。",
            },
        ],
    }
