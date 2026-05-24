"""Render generic slide_json into the weekly-report deck.

Visual language: clean business report — blue/teal/amber accents on light
surface cards, KPI tiles with status stripes, ship-item rows. Dispatches new
generic layouts (kpi-grid / stat-highlight / comparison / pros-cons /
big-quote / timeline / process-steps / two/three-column / bullets) via
`src/renderer/layouts.py`.
"""
from __future__ import annotations

from typing import Any

from . import layouts as L

KPI_STATUS = ["good", "warn", "bad", ""]
SHIP_TAGS = ["feat", "fix", "exp", "infra"]


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{L.esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _footer(left: str, slide_no: int, total: int) -> str:
    return f'<div class="deck-footer"><span>{L.esc(left)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover_head() -> str:
    return (
        '<div class="cover-head">'
        '<div class="logo">fxt ppt</div>'
        '<div class="week-chip">auto · weekly</div>'
        '</div>'
    )


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "本周内容自动整理"
    inner = f"""
    {_cover_head()}
    <p class="kicker">WEEKLY · auto report</p>
    <h1 class="h1 mt-s">{L.rich(title)}</h1>
    <p class="lede mt-m" style="max-width:880px">{L.rich(subtitle)}</p>
    <div class="grid g3 mt-l">
      <div class="kpi"><div class="label">sections</div><div class="value">{max(1, len(generic.get("slides", [])) - 2)}</div><div class="delta flat">automated</div></div>
      <div class="kpi good"><div class="label">build</div><div class="value">OK</div><div class="delta up">↑ deck ready</div></div>
      <div class="kpi warn"><div class="label">review</div><div class="value">pending</div><div class="delta flat">→ human-in-loop</div></div>
    </div>
    {_footer("cover · weekly", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:8]):
        tag = SHIP_TAGS[i % len(SHIP_TAGS)]
        rows.append(
            f'<div class="ship-item"><span class="tag {tag}">PART {i + 1:02d}</span>'
            f'<div><b>{L.rich(t)}</b></div><span class="owner">@fxt-ppt</span></div>'
        )
    inner = f"""
    {_cover_head()}
    <p class="kicker">agenda</p>
    <h2 class="h2">本期议程 · {len(rows)} sections</h2>
    <div class="mt-l">{''.join(rows)}</div>
    {_footer("agenda", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    kpis = []
    for i, p in enumerate(points[:3]):
        status = KPI_STATUS[i % len(KPI_STATUS)]
        cls = f"kpi {status}".strip()
        kpis.append(
            f'<div class="{cls}"><div class="label">point {i + 1:02d}</div>'
            f'<div class="value" style="font-size:22px;line-height:1.25">{L.rich(p)}</div></div>'
        )
    inner = f"""
    {_cover_head()}
    <p class="kicker">part · {chapter_no:02d}</p>
    <h1 class="h1 mt-s">{L.rich(title)}</h1>
    <p class="lede mt-m">先建立结构，再展开重点。</p>
    <div class="grid g3 mt-l">{''.join(kpis)}</div>
    {_footer(f"section · chapter_{chapter_no:02d}", slide_no, total)}
    """
    return _section(inner, title=title)


def _content(slide: dict[str, Any], slide_no: int, total: int) -> str:
    layout = L.normalize_layout(slide.get("layout"), len(L.get_bullets(slide)))
    body = L.render_inner(layout, slide)
    inner = f"""
    {_cover_head()}
    <p class="kicker">{L.esc(slide.get("section") or "content")}</p>
    <h2 class="h2">{L.rich(slide.get("title") or "本周内容")}</h2>
    {body}
    {_footer(f"content · {layout}", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。"
    inner = f"""
    {_cover_head()}
    <p class="kicker">end · report</p>
    <h1 class="h1 mt-s">{L.rich(title)}</h1>
    <p class="lede mt-m">{L.rich(message)}</p>
    <div class="grid g3 mt-l">
      <div class="kpi good"><div class="label">deck</div><div class="value">READY</div><div class="delta up">automation OK</div></div>
      <div class="kpi"><div class="label">brand</div><div class="value">fxt ppt</div><div class="delta flat">weekly-report</div></div>
      <div class="kpi warn"><div class="label">credit</div><div class="value">AUTO</div><div class="delta flat">human-in-loop</div></div>
    </div>
    {_footer("end", slide_no, total)}
    """
    return _section(inner, title=str(title))


def render_weekly_report(generic: dict[str, Any]) -> str:
    planned = L.planned_slides(generic)
    total = len(planned)
    chapters = L.chapter_titles(generic)
    sections: list[str] = []
    chapter_no = 0
    for idx, (kind, slide) in enumerate(planned, start=1):
        active = idx == 1
        if kind == "cover":
            sections.append(_cover(generic, idx, total, active))
        elif kind == "contents":
            sections.append(_contents(chapters, idx, total))
        elif kind == "section":
            chapter_no += 1
            title = slide.get("title") or f"Part {chapter_no}"
            points = L.get_bullets(slide)
            sections.append(_divider(title, points, chapter_no, idx, total))
        elif kind == "closing":
            sections.append(_closing(slide, idx, total))
        else:
            sections.append(_content(slide, idx, total))

    title = L.esc(generic.get("title") or "Weekly Report 周报")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="assets/fonts.css">
<link rel="stylesheet" href="assets/base.css">
<link rel="stylesheet" href="style.css">
</head>
<body class="tpl-weekly-report">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_weekly_report"]
