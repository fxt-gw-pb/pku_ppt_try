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

    def public_dict(self) -> dict[str, str]:
        data = asdict(self)
        # Keep absolute filesystem details out of the public API.
        data.pop("path", None)
        return data


_TEMPLATES: dict[str, DeckTemplate] = {
    "pku-red": DeckTemplate(
        template_id="pku-red",
        name="北大红答辩模板",
        engine="pku-json",
        description="北大红学术答辩风格，适合论文答辩、开题报告和正式学术汇报。",
        preview_url="/demo.html",
        path=str(REPO_ROOT / "pku-red-defense-ppt" / "assets" / "template"),
    ),
    "xhs-white-editorial": DeckTemplate(
        template_id="xhs-white-editorial",
        name="小红书白底杂志风",
        engine="html-ppt",
        description="白底杂志风、强重点块、马卡龙软色卡，适合中文内容帖和知识分享。",
        preview_url="/html-ppt-templates/templates/full-decks/xhs-white-editorial/index.html",
        path=str(REPO_ROOT / "templates" / "html-ppt" / "xhs-white-editorial"),
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

