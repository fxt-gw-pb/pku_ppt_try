"""Mock LLM provider: returns a deterministic sample slide_json.

Used when LLM_PROVIDER=mock. Lets the rest of the pipeline (schema → render
→ export → API → frontend) be exercised end-to-end without a real key.

The sample deck deliberately exercises **every supported layout** so that
preview decks under `previews/<id>/` showcase each template's full visual
range, not just the cards grid. The manuscript text is only used to extract a
title from its first non-empty line.
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
                    "研究现状与问题",
                    "研究思路与方法",
                    "实验与结果",
                    "结论与展望",
                ],
            },

            # ===== 第一章：背景与意义 =====
            {
                "type": "section",
                "title": "背景与意义",
                "bullets": ["宏观背景", "核心问题", "理论与实践意义"],
            },
            {
                "type": "content",
                "title": "选题的三个驱动力",
                "section": "背景与意义",
                "layout": "three-column",
                "columns": [
                    {"title": "外部环境", "body": "行业趋势、政策导向与社会需求持续上升，为研究提供时代背景。"},
                    {"title": "现有方案", "body": "在关键指标上仍存在明显瓶颈，无法支撑下一阶段任务。"},
                    {"title": "新的可能", "body": "新工具与新数据为方法论突破提供契机，窗口期短暂但清晰。"},
                ],
                "bullets": [
                    "外部环境：行业趋势、政策与社会需求持续上升",
                    "现有方案：关键指标存在明显瓶颈",
                    "新的可能：新工具与新数据带来突破窗口",
                ],
                "notes": "这一页用三列结构把宏观、现状、机会拉开，让评审一眼看到选题不是凭空而起。",
            },
            {
                "type": "content",
                "title": "用一句话说清研究意义",
                "section": "背景与意义",
                "layout": "big-quote",
                "quote": {
                    "text": "如果一项研究只能压缩成一句话，那它一定是把复杂问题拆成了可以独立验证的最小单元。",
                    "author": "—— 研究方法学 笔记",
                },
                "bullets": [],
                "notes": "用一句口号式概括锚定全篇思想，后续每一页都会回扣到「可独立验证的最小单元」这条主线。",
            },

            # ===== 第二章：研究现状与问题 =====
            {
                "type": "section",
                "title": "研究现状与问题",
                "bullets": ["主流路径", "代表工作", "共性缺口"],
            },
            {
                "type": "content",
                "title": "现状 vs 我们的切入点",
                "section": "研究现状与问题",
                "layout": "comparison",
                "compare": {
                    "left": {
                        "title": "现有主流方法",
                        "points": [
                            "依赖大规模标注数据，单任务训练成本高",
                            "对长尾分布缺乏稳健性，跨域时显著退化",
                            "可解释性弱，难以为决策环节提供依据",
                        ],
                    },
                    "right": {
                        "title": "本研究切入点",
                        "points": [
                            "利用结构先验降低标注需求，单样本可学",
                            "通过多视图对齐显式建模长尾，跨域稳定",
                            "对每一步推理给出可追溯的中间表征",
                        ],
                    },
                },
                "bullets": [
                    "现有主流：高标注成本、长尾退化、可解释性弱",
                    "本研究：结构先验、对齐机制、可追溯表征",
                ],
                "notes": "并排比较让评审快速看到本研究的差异化定位，而不是堆砌方法名。",
            },
            {
                "type": "content",
                "title": "诚实的取舍",
                "section": "研究现状与问题",
                "layout": "pros-cons",
                "compare": {
                    "left": {
                        "title": "我们方法的优势",
                        "points": [
                            "训练样本需求降低 60% 以上",
                            "在 5 个跨域数据集上保持精度衰减 < 5%",
                            "中间表征可被领域专家直接审阅",
                        ],
                    },
                    "right": {
                        "title": "我们方法的局限",
                        "points": [
                            "对结构先验的质量比较敏感",
                            "在极小样本（<10）时仍不稳定",
                            "推理速度尚未做端侧优化",
                        ],
                    },
                },
                "bullets": [],
                "notes": "把短板讲透反而能赢得评审信任。后续章节会针对每条局限给出对应缓解策略。",
            },

            # ===== 第三章：研究思路与方法 =====
            {
                "type": "section",
                "title": "研究思路与方法",
                "bullets": ["总体框架", "关键创新", "实现路径"],
            },
            {
                "type": "content",
                "title": "四步研究流程",
                "section": "研究思路与方法",
                "layout": "process-steps",
                "steps": [
                    {"title": "问题界定", "body": "锁定研究对象、边界条件与可测量的目标指标。"},
                    {"title": "理论建模", "body": "在已有理论上提出结构假设，引入新约束。"},
                    {"title": "数据采集", "body": "梳理多源数据，建立标注与质控流程。"},
                    {"title": "实证验证", "body": "通过消融与跨域测试逐项检验，量化贡献。"},
                ],
                "bullets": [
                    "问题界定：锁定对象、边界与目标指标",
                    "理论建模：在已有理论上引入新约束",
                    "数据采集：多源数据 + 质控",
                    "实证验证：消融与跨域测试",
                ],
                "notes": "四步法的关键是每一步都有「上一步给的输入」与「下一步要的输出」，避免环节脱节。",
            },
            {
                "type": "content",
                "title": "研究演进时间线",
                "section": "研究思路与方法",
                "layout": "timeline",
                "steps": [
                    {"when": "2024 Q3", "title": "立项调研", "body": "完成 80+ 文献综述与 5 次专家访谈。"},
                    {"when": "2024 Q4", "title": "原型实现", "body": "搭建首版端到端 pipeline，跑通 baseline。"},
                    {"when": "2025 Q1", "title": "数据扩充", "body": "新增 12k 标注样本，建立质控规范。"},
                    {"when": "2025 Q2", "title": "方法迭代", "body": "引入结构先验与对齐损失，关键指标突破。"},
                    {"when": "2025 Q3", "title": "外部评测", "body": "在 3 个公开榜单与 2 个真实场景验证。"},
                ],
                "bullets": [],
                "notes": "时间线让评审看到研究节奏，也突出了方法不是一蹴而就，而是迭代收敛。",
            },

            # ===== 第四章：实验与结果 =====
            {
                "type": "section",
                "title": "实验与结果",
                "bullets": ["核心指标", "对比实验", "案例分析"],
            },
            {
                "type": "content",
                "title": "关键指标全面提升",
                "section": "实验与结果",
                "layout": "kpi-grid",
                "kpis": [
                    {"label": "Top-1 准确率", "value": "92.4%", "delta": "↑ 6.1pt vs SOTA", "status": "good"},
                    {"label": "跨域均值", "value": "88.7%", "delta": "↑ 9.3pt", "status": "good"},
                    {"label": "训练耗时", "value": "−38%", "delta": "8×A100 集群", "status": "good"},
                    {"label": "推理延迟", "value": "12ms", "delta": "→ 持平 baseline", "status": "warn"},
                ],
                "bullets": [
                    "Top-1 准确率 92.4%（+6.1pt）",
                    "跨域均值 88.7%（+9.3pt）",
                    "训练耗时 −38%",
                    "推理延迟 12ms 持平",
                ],
                "notes": "KPI 卡用绿/黄区分突破和持平，让评审在 3 秒内抓到亮点与诚实点。",
            },
            {
                "type": "content",
                "title": "一个数字说明问题",
                "section": "实验与结果",
                "layout": "stat-highlight",
                "stat": {
                    "value": "38%",
                    "label": "训练耗时下降",
                    "sub": "在 8×A100 集群上，全样本训练时间从 41h 缩短到 25h。",
                    "delta": "↓ vs strongest baseline",
                },
                "bullets": [],
                "notes": "把训练效率这件最容易被忽视的工程价值单独拎一页，正向呼应「工程可行」的论点。",
            },
            {
                "type": "content",
                "title": "概念 vs 实现",
                "section": "实验与结果",
                "layout": "two-column",
                "columns": [
                    {"title": "概念层", "kicker": "Why", "body": "结构先验把领域知识显式注入到训练目标，让模型在小样本下也能稳定收敛。"},
                    {"title": "实现层", "kicker": "How", "body": "通过一组可微图算子构造对齐损失，并以课程学习方式逐步加权。"},
                ],
                "bullets": [
                    "概念层：把领域知识注入训练目标",
                    "实现层：可微图算子 + 课程学习",
                ],
                "notes": "把「想法」和「代码」放在两列里讲，对工程评审最友好。",
            },
            {
                "type": "content",
                "title": "贡献清单（卡片回顾）",
                "section": "实验与结果",
                "layout": "cards",
                "bullets": [
                    "结构先验：把领域知识转成可微约束，降低标注需求",
                    "对齐损失：在多视图特征上建模长尾，提升稳定性",
                    "可追溯表征：中间层支持专家直接审阅与干预",
                    "工程优化：训练耗时 −38%，端到端 pipeline 已开源",
                ],
                "notes": "最后用 cards 收束四条贡献，呼应封面的「四个独立可验证的单元」。",
            },

            # ===== 第五章：结论与展望 =====
            {
                "type": "section",
                "title": "结论与展望",
                "bullets": ["主要结论", "不足", "下一步"],
            },
            {
                "type": "content",
                "title": "结论与下一步",
                "section": "结论与展望",
                "layout": "bullets",
                "bullets": [
                    "建立了关键变量与目标指标的定量关联，效果在 5 个数据集上验证",
                    "证实结构先验与对齐损失的协同效应，跨域稳定性显著提升",
                    "工程实现完成规模化扩展，已在两个真实业务场景落地",
                    "下一步：极小样本场景的稳定性、端侧推理优化、跨语言迁移",
                ],
                "notes": "结尾用清单形式让记忆点更扎实；下一步条目同时回应前面承认的局限。",
            },

            {
                "type": "closing",
                "title": "感谢您的倾听！",
                "bullets": [],
                "notes": "感谢导师的悉心指导，感谢各位老师与同学的支持。敬请各位老师批评指正。",
            },
        ],
    }
