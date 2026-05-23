"""Render generic slide_json into the graphify-dark-graph deck.

Visual language: deep navy backdrop with drifting color orbs, decorative
force-graph SVG on cover/chapter pages, rainbow + warm-grad headlines,
glass cards with subtle tints.
"""
from __future__ import annotations

import html
from typing import Any

GLASS_TINTS = ["", "gd-glass-warm", "gd-glass-blue", "gd-glass-green", ""]
ACCENT_SPANS = ["gd-accent", "gd-green", "gd-blue", "gd-accent"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="gd-grad">{part}</span>')
        else:
            out.append(part)
    return "".join(out)


def _split_kv(bullet: str) -> tuple[str, str]:
    for sep in ("：", ":"):
        if sep in bullet:
            head, _, tail = bullet.partition(sep)
            head, tail = head.strip(), tail.strip()
            if head and tail:
                return head, tail
    return "", bullet.strip()


def _ambient(*orbs: str) -> str:
    return '<div class="gd-ambient">' + "".join(f'<div class="gd-orb {o}"></div>' for o in (orbs or ("gd-orb-1", "gd-orb-2"))) + "</div>"


def _snum(slide_no: int, total: int) -> str:
    return f'<div class="gd-snum">{slide_no:02d} / {total:02d}</div>'


def _graph_svg() -> str:
    # Small decorative force-graph for cover/chapter pages.
    return """
    <svg viewBox="0 0 1600 900" style="position:absolute;inset:0;width:100%;height:100%;opacity:.28;z-index:1" xmlns="http://www.w3.org/2000/svg">
      <g stroke="#7eb8da" stroke-width="1" stroke-opacity=".5" fill="none">
        <line x1="280" y1="200" x2="520" y2="340"/>
        <line x1="520" y1="340" x2="780" y2="260"/>
        <line x1="780" y1="260" x2="1040" y2="420"/>
        <line x1="520" y1="340" x2="640" y2="560"/>
        <line x1="640" y1="560" x2="900" y2="620"/>
        <line x1="900" y1="620" x2="1040" y2="420"/>
        <line x1="1040" y1="420" x2="1260" y2="300"/>
        <line x1="1260" y1="300" x2="1380" y2="500"/>
        <line x1="900" y1="620" x2="1120" y2="720"/>
        <line x1="280" y1="200" x2="200" y2="420"/>
        <line x1="200" y1="420" x2="360" y2="640"/>
        <line x1="360" y1="640" x2="640" y2="560"/>
      </g>
      <g>
        <circle cx="280" cy="200" r="9" fill="#e8a87c"/>
        <circle cx="520" cy="340" r="13" fill="#7eb8da"/>
        <circle cx="780" cy="260" r="8" fill="#7ed3a4"/>
        <circle cx="1040" cy="420" r="16" fill="#b8a4d6"/>
        <circle cx="640" cy="560" r="10" fill="#d4a0b9"/>
        <circle cx="900" cy="620" r="11" fill="#e8a87c"/>
        <circle cx="1260" cy="300" r="8" fill="#7ed3a4"/>
        <circle cx="1380" cy="500" r="9" fill="#7eb8da"/>
        <circle cx="1120" cy="720" r="9" fill="#d4a0b9"/>
        <circle cx="200" cy="420" r="7" fill="#b8a4d6"/>
        <circle cx="360" cy="640" r="10" fill="#7eb8da"/>
      </g>
    </svg>
    """


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Generated deck · knowledge graph edition"
    inner = f"""
    {_ambient("gd-orb-1", "gd-orb-2", "gd-orb-3")}
    {_graph_svg()}
    {_snum(slide_no, total)}
    <div style="margin-top:auto">
      <p class="gd-eyebrow">fxt ppt · auto-generated deck</p>
      <h1 class="gd-h1" style="font-size:84px"><span class="gd-rainbow">{_rich(title)}</span></h1>
      <p class="gd-lede" style="margin-top:18px">{_rich(subtitle)}</p>
      <p class="gd-eyebrow" style="margin-top:24px">↑ 背景是装饰性的知识图谱节点</p>
    </div>
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cells = []
    for i, t in enumerate(chapters[:6]):
        tint = GLASS_TINTS[i % len(GLASS_TINTS)]
        cells.append(
            f"""
      <div class="gd-glass {tint}">
        <p class="gd-eyebrow">Part {i + 1:02d}</p>
        <h4 style="margin:8px 0 4px;font-size:18px">{_rich(t)}</h4>
      </div>
            """
        )
    grid_cls = "gd-grid-3" if len(cells) >= 3 else "gd-grid-2"
    inner = f"""
    {_ambient("gd-orb-2", "gd-orb-3")}
    {_snum(slide_no, total)}
    <p class="gd-eyebrow">Contents</p>
    <h2 class="gd-h2">这份内容分为 <span class="gd-grad">{len(cells)} 个部分</span></h2>
    <div class="{grid_cls}">{''.join(cells)}</div>
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    tags = "".join(f'<span class="gd-tag">{_esc(p)}</span>' for p in points[:4])
    inner = f"""
    {_ambient("gd-orb-1", "gd-orb-2")}
    {_graph_svg()}
    {_snum(slide_no, total)}
    <div style="margin:auto 0">
      <div class="gd-eyebrow">Part {chapter_no:02d}</div>
      <h1 class="gd-h1" style="font-size:108px"><span class="gd-grad">{_rich(title)}</span></h1>
      <p class="gd-lede">先建立结构，再展开重点。</p>
      <div style="margin-top:18px">{tags}</div>
    </div>
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        tint = GLASS_TINTS[i % len(GLASS_TINTS)]
        body_html = (
            f'<p class="gd-dim" style="font-size:13px;line-height:1.55">{_rich(body)}</p>'
            if (head and body)
            else ""
        )
        cells.append(
            f"""
      <div class="gd-glass {tint}">
        <div style="font-size:24px">{["◆", "●", "▲", "◇", "■", "★"][i % 6]}</div>
        <h4 style="margin:10px 0 6px;font-size:18px">{_rich(head or bullet)}</h4>
        {body_html}
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="gd-glass"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "gd-grid-4" if n >= 4 else "gd-grid-3" if n >= 3 else "gd-grid-2"
    eyebrow = slide.get("section") or "Feature map"
    inner = f"""
    {_ambient("gd-orb-2", "gd-orb-3")}
    {_snum(slide_no, total)}
    <p class="gd-eyebrow">{_esc(eyebrow)}</p>
    <h2 class="gd-h2">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="{grid_cls}">{''.join(cells)}</div>
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows: list[str] = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        accent = ACCENT_SPANS[i % len(ACCENT_SPANS)]
        rows.append(
            f"""
      <div class="gd-glass" style="display:flex;gap:18px;align-items:flex-start;margin-bottom:10px">
        <div style="font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:700;line-height:1" class="{accent}">{i + 1:02d}</div>
        <div>
          <h4 style="margin:0 0 6px;font-size:18px">{_rich(head or f"步骤 {i + 1}")}</h4>
          <p class="gd-dim" style="font-size:13px;line-height:1.6">{_rich(body if head else bullet)}</p>
        </div>
      </div>
            """
        )
    eyebrow = slide.get("section") or "Pipeline"
    inner = f"""
    {_ambient("gd-orb-1", "gd-orb-3")}
    {_snum(slide_no, total)}
    <p class="gd-eyebrow">{_esc(eyebrow)}</p>
    <h2 class="gd-h2">{_rich(slide.get("title") or "过程拆解")}</h2>
    <div style="margin-top:18px">{''.join(rows)}</div>
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。"
    inner = f"""
    {_ambient("gd-orb-1", "gd-orb-2", "gd-orb-3")}
    {_snum(slide_no, total)}
    <div style="margin:auto 0">
      <p class="gd-eyebrow">End of deck</p>
      <h1 class="gd-h1" style="font-size:120px"><span class="gd-rainbow">{_rich(title)}</span></h1>
      <p class="gd-lede" style="margin-top:18px">{_rich(message)}</p>
      <div style="margin-top:22px">
        <span class="gd-tag">fxt ppt</span>
        <span class="gd-tag">graphify-dark-graph</span>
        <span class="gd-tag">auto-generated</span>
      </div>
    </div>
    """
    return _section(inner, title=str(title))


def _planned_slides(generic: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    slides = [s for s in (generic.get("slides") or []) if isinstance(s, dict)]
    planned: list[tuple[str, dict[str, Any]]] = [("cover", {})]
    chapters = [
        (s.get("title") or s.get("section") or "").strip()
        for s in slides
        if s.get("type") == "section"
    ]
    if chapters:
        planned.append(("contents", {}))
    closing: dict[str, Any] | None = None
    for slide in slides:
        stype = slide.get("type")
        if stype in {"cover", "contents"}:
            continue
        if stype == "closing":
            closing = slide
            continue
        planned.append((stype, slide))
    planned.append(("closing", closing or {}))
    return planned


def render_graphify_dark_graph(generic: dict[str, Any]) -> str:
    planned = _planned_slides(generic)
    total = len(planned)
    sections: list[str] = []
    chapter_no = 0
    chapters = [
        (s.get("title") or s.get("section") or "").strip()
        for s in generic.get("slides", [])
        if isinstance(s, dict) and s.get("type") == "section"
    ]
    for idx, (kind, slide) in enumerate(planned, start=1):
        active = idx == 1
        if kind == "cover":
            sections.append(_cover(generic, idx, total, active))
        elif kind == "contents":
            sections.append(_contents(chapters, idx, total))
        elif kind == "section":
            chapter_no += 1
            title = slide.get("title") or f"Part {chapter_no}"
            points = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
            sections.append(_divider(title, points, chapter_no, idx, total))
        elif kind == "closing":
            sections.append(_closing(slide, idx, total))
        else:
            bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
            if slide.get("layout") == "timeline" or len(bullets) >= 5:
                sections.append(_steps(slide, idx, total))
            else:
                sections.append(_cards(slide, idx, total))

    title = _esc(generic.get("title") or "暗底知识图谱")
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
<body class="tpl-graphify-dark-graph">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_graphify_dark_graph"]
