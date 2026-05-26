"""Central registry for deck templates exposed by the generator."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE_ID = "pku-red"


@dataclass(frozen=True)
class DeckTemplate:
    template_id: str
    name: str
    engine: str
    description: str
    preview_url: str
    path: str
    body_class: str = ""
    renderer: str = "generic"

    def public_dict(self) -> dict[str, str]:
        data = asdict(self)
        data["engine"] = "classic" if self.engine == "pku-json" else "template"
        # Keep absolute filesystem details out of the public API.
        data.pop("path", None)
        data.pop("body_class", None)
        data.pop("renderer", None)
        data.pop("preview_url", None)
        return data


def _html_ppt(
    template_id: str,
    name: str,
    description: str,
    *,
    renderer: str = "generic",
) -> DeckTemplate:
    return DeckTemplate(
        template_id=template_id,
        name=name,
        engine="html-ppt",
        description=description,
        preview_url="",
        path=str(REPO_ROOT / "templates" / "html-ppt" / template_id),
        body_class=f"tpl-{template_id}",
        renderer=renderer,
    )


_TEMPLATES: dict[str, DeckTemplate] = {
    "pku-red": DeckTemplate(
        template_id="pku-red",
        name="北大红答辩模板",
        engine="pku-json",
        description="北大红学术答辩风格，适合论文答辩、开题报告和正式学术汇报。作者自制，最不推荐(bushi)。",
        preview_url="",
        path=str(REPO_ROOT / "pku-red-defense-ppt" / "assets" / "template"),
    ),
    "xhs-white-editorial": _html_ppt(
        "xhs-white-editorial",
        "小红书白底杂志风",
        "白底杂志风、强重点块、马卡龙软色卡，适合中文内容帖和知识分享。",
        renderer="xhs-white-editorial",
    ),
    "graphify-dark-graph": _html_ppt(
        "graphify-dark-graph",
        "暗底知识图谱",
        "深夜渐变、知识图谱和玻璃卡片，适合 AI、数据产品和图谱类分享。",
        renderer="graphify-dark-graph",
    ),
    "knowledge-arch-blueprint": _html_ppt(
        "knowledge-arch-blueprint",
        "奶油蓝图架构",
        "奶油纸面、蓝图网格和硬边框，适合系统架构、工程白皮书和技术路线。",
        renderer="knowledge-arch-blueprint",
    ),
    "hermes-cyber-terminal": _html_ppt(
        "hermes-cyber-terminal",
        "暗终端 Cyber",
        "终端窗口、扫描线和代码感，适合 CLI、Agent、工具评测和技术复盘。",
        renderer="hermes-cyber-terminal",
    ),
    "obsidian-claude-gradient": _html_ppt(
        "obsidian-claude-gradient",
        "GitHub 暗紫渐变",
        "GitHub dark 加紫蓝渐变，适合开发者工作流、LLM 产品和工具教程。",
        renderer="obsidian-claude-gradient",
    ),
    "testing-safety-alert": _html_ppt(
        "testing-safety-alert",
        "红琥珀警示",
        "风险警示、事故复盘和安全审查风格，适合 AI 安全、风控和红队汇报。",
        renderer="testing-safety-alert",
    ),
    "xhs-pastel-card": _html_ppt(
        "xhs-pastel-card",
        "小红书柔和马卡龙",
        "柔和卡片、手作杂志感，适合生活方式、成长类和轻内容分享。",
        renderer="xhs-pastel-card",
    ),
    "dir-key-nav-minimal": _html_ppt(
        "dir-key-nav-minimal",
        "方向键 8 色极简",
        "大留白、一页一观点、强色块切换，适合 keynote 式演讲。",
        renderer="dir-key-nav-minimal",
    ),
    "pitch-deck": _html_ppt(
        "pitch-deck",
        "Pitch Deck 路演",
        "白底蓝紫渐变、指标和融资叙事，适合创业路演和投资人汇报。",
        renderer="pitch-deck",
    ),
    "product-launch": _html_ppt(
        "product-launch",
        "Product Launch 发布会",
        "深色封面、功能卡片和 CTA，适合产品发布和方案展示。",
        renderer="product-launch",
    ),
    "tech-sharing": _html_ppt(
        "tech-sharing",
        "Tech Sharing 技术分享",
        "GitHub dark、代码块和终端感，适合内部技术分享和会议演讲。",
        renderer="tech-sharing",
    ),
    "weekly-report": _html_ppt(
        "weekly-report",
        "Weekly Report 周报",
        "清晰商务报表风，适合周报、项目进展和业务复盘。",
        renderer="weekly-report",
    ),
    "xhs-post": _html_ppt(
        "xhs-post",
        "小红书 3:4 图文",
        "3:4 竖版卡片，适合小红书/社媒图文轮播。",
        renderer="xhs-post",
    ),
    "course-module": _html_ppt(
        "course-module",
        "Course Module 教学模块",
        "课程侧栏和学习目标结构，适合课程、workshop 和培训材料。",
        renderer="course-module",
    ),
    "presenter-mode-reveal": _html_ppt(
        "presenter-mode-reveal",
        "演讲者模式 Reveal",
        "带逐字稿和演讲者视图的模板，适合技术分享、课程和正式演讲。",
        renderer="presenter-mode-reveal",
    ),
    "swiss-grid": _html_ppt(
        "swiss-grid",
        "瑞士国际网格",
        "克莱因蓝单一锚点、极轻 200 字重和 12 列网格，适合研究笔记、白皮书与品牌字段笔记。",
        renderer="swiss-grid",
    ),
    "editorial-monocle": _html_ppt(
        "editorial-monocle",
        "墨刻杂志风",
        "暗墨纸面、衬线大标题与杂志感小标签，适合长文阅读、专题策划与编辑型分享。",
        renderer="editorial-monocle",
    ),
}


def get_template(template_id: str | None) -> DeckTemplate:
    tid = (template_id or DEFAULT_TEMPLATE_ID).strip() or DEFAULT_TEMPLATE_ID
    if tid not in _TEMPLATES:
        known = ", ".join(sorted(_TEMPLATES))
        raise KeyError(f"unknown template_id {tid!r}; expected one of: {known}")
    return _TEMPLATES[tid]


def list_templates() -> list[dict[str, str]]:
    return [tpl.public_dict() for tpl in _TEMPLATES.values()]
