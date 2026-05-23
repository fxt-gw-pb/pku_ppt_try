"""Render generic slide_json into the pitch-deck deck.

Visual language: classic YC/VC pitch — white background with soft blue-purple
gradient washes, mega numbers, metric strips, traction bar charts, ask box
with bold gradient backdrop, large section-num backdrops on dividers.
"""
from __future__ import annotations

import html
from typing import Any


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="gradient-text">{part}</span>')
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


def _brand() -> str:
    return '<div><span class="brand-dot"></span><span class="brand">fxt ppt</span></div>'


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _footer(slide_no: int, total: int, tag: str) -> str:
    return f'<div class="deck-footer"><span>{_esc(tag)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Auto-generated pitch · 路演版本"
    inner = f"""
    <div class="cover-bg"></div><div class="cover-blob"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:38px">
      {_brand()}
      <span class="num-tag">PITCH · 2026</span>
    </div>
    <p class="kicker">FXT PPT · AUTO PITCH</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m" style="max-width:900px">{_rich(subtitle)}</p>
    <div class="grid g3 mt-l" style="max-width:1080px">
      <div class="metric"><div class="n">1</div><div class="l">deck idea</div></div>
      <div class="metric"><div class="n">{max(1, len(generic.get("slides", [])) - 2)}</div><div class="l">sections</div></div>
      <div class="metric"><div class="n">∞</div><div class="l">iterations</div></div>
    </div>
    {_footer(slide_no, total, "cover · pitch")}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, t in enumerate(chapters[:6]):
        cards.append(
            f"""
      <div class="card" style="padding:26px 28px">
        <span class="num-tag">PART {i + 1:02d}</span>
        <h4 style="margin:10px 0 6px;font-size:22px;font-weight:800">{_rich(t)}</h4>
      </div>
            """
        )
    grid_cls = "grid g3" if len(cards) >= 3 else "grid g2"
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">CONTENTS</p>
    <h2 class="h2">这份 pitch 分为 <span class="gradient-text">{len(cards)} 段</span></h2>
    <div class="{grid_cls} mt-l">{''.join(cards)}</div>
    {_footer(slide_no, total, "contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(f'<span class="pill pill-accent" style="margin-right:8px">{_esc(p)}</span>' for p in points[:4])
    inner = f"""
    <div class="section-num">{chapter_no:02d}</div>
    {_brand()}
    <p class="kicker mt-l">PART · {chapter_no:02d}</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m" style="max-width:900px">先建立结构，再展开重点。</p>
    <div class="mt-l">{pills}</div>
    {_footer(slide_no, total, f"section · {chapter_no:02d}")}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        body_html = (
            f'<p class="dim" style="font-size:15px;line-height:1.55">{_rich(body)}</p>'
            if (head and body)
            else ""
        )
        cells.append(
            f"""
      <div class="card" style="padding:28px 32px">
        <span class="num-tag">{i + 1:02d}</span>
        <h4 style="margin:10px 0 8px;font-size:22px;font-weight:800">{_rich(head or bullet)}</h4>
        {body_html}
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "grid g3" if n in {3, 6} else "grid g2"
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">{_esc(slide.get("section") or "content")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="{grid_cls} mt-l">{''.join(cells)}</div>
    {_footer(slide_no, total, "content · cards")}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:6]
    n = max(len(bullets), 1)
    bars: list[str] = []
    for i, bullet in enumerate(bullets):
        head, _body = _split_kv(bullet)
        pct = 25 + int(70 * (i / max(n - 1, 1)))
        label = _esc(head or f"step {i + 1}")
        bars.append(
            f'<div class="bar" style="height:{pct}%"><em>{label}</em><span>{i + 1:02d}</span></div>'
        )
    rows = []
    for i, bullet in enumerate(bullets):
        head, body = _split_kv(bullet)
        rows.append(
            f"""
      <div class="card" style="padding:18px 22px;margin-top:10px">
        <span class="num-tag">{i + 1:02d}</span>
        <h4 style="margin:6px 0 4px;font-size:18px">{_rich(head or f"步骤 {i + 1}")}</h4>
        <p class="dim" style="font-size:13px;line-height:1.55">{_rich(body if head else bullet)}</p>
      </div>
            """
        )
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">{_esc(slide.get("section") or "traction")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "增长路径")}</h2>
    <div class="card mt-l" style="padding:36px 40px">
      <div class="traction-bar">{''.join(bars)}</div>
    </div>
    <div class="grid g3 mt-l">{''.join(rows)}</div>
    {_footer(slide_no, total, "content · traction")}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。期待和你的下一次对话。"
    inner = f"""
    {_brand()}
    <div class="ask-box mt-l">
      <p class="kicker" style="color:#fff">THE ASK</p>
      <h2 class="h2 mt-s">{_rich(title)}</h2>
      <p class="dim mt-m" style="font-size:18px">{_rich(message)}</p>
      <div class="mt-l">
        <span class="pill" style="background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.4)">fxt ppt</span>
        <span class="pill" style="background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.4)">pitch-deck</span>
        <span class="pill" style="background:rgba(255,255,255,.15);color:#fff;border-color:rgba(255,255,255,.4)">auto-generated</span>
      </div>
    </div>
    {_footer(slide_no, total, "end · ask")}
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


def render_pitch_deck(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "Pitch Deck 路演")
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
<body class="tpl-pitch-deck">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_pitch_deck"]
