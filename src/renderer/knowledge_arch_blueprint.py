"""Render generic slide_json into the knowledge-arch-blueprint deck.

Visual language: cream paper background with light blueprint grid,
hard-edged black-bordered white cards, rust-red accent. Pipeline strip
with one hero step that pops in rust. Big serif numerals on dividers.
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
            out.append(f'<span class="rust">{part}</span>')
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


def _grid_bg() -> str:
    return '<div class="kb-grid-bg"></div>'


def _footer(left: str, slide_no: int, total: int) -> str:
    return f'<div class="kb-footer"><span>{_esc(left)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Generated deck · blueprint edition"
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">fxt ppt · auto-generated</div>
    <h1 class="kb-h1">{_rich(title)}</h1>
    <p class="kb-sub">{_rich(subtitle)}</p>
    <div style="margin-top:30px">
      <span class="kb-insight">
        <span class="kk">INSIGHT</span>
        把原文的结构、流程和重点搬到一张蓝图上。
      </span>
    </div>
    {_footer("cover · blueprint", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, t in enumerate(chapters[:6]):
        hero_cls = " hero" if i == 0 else ""
        cards.append(
            f"""
      <div class="kb-step{hero_cls}">
        <div class="kb-step-num">PART {i + 1:02d}</div>
        <div class="kb-step-title">{_rich(t)}</div>
        <div class="kb-step-body">本部分提炼原文关键观点与逻辑。</div>
      </div>
            """
        )
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">Contents</div>
    <h2 class="kb-h1" style="font-size:46px">蓝图 · {len(cards)} 个区段</h2>
    <div class="kb-section-label">structure overview</div>
    <div class="kb-pipeline">{''.join(cards)}</div>
    <div class="kb-legend">
      <div class="d"><span class="b rust"></span>核心区段</div>
      <div class="d"><span class="b"></span>支撑区段</div>
    </div>
    {_footer("contents · blueprint", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    chip_rows = "".join(
        f'<div class="kb-card" style="padding:14px 18px;margin-right:10px;display:inline-block"><h4 style="margin:0;font-size:16px">{_rich(p)}</h4></div>'
        for p in points[:3]
    )
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">part · {chapter_no:02d}</div>
    <div style="display:flex;align-items:baseline;gap:32px;margin-top:14px">
      <div class="kb-big-num">{chapter_no:02d}</div>
      <div>
        <h2 class="kb-h1" style="font-size:54px">{_rich(title)}</h2>
        <p class="kb-sub">先建立结构，再展开重点。</p>
      </div>
    </div>
    <div class="kb-section-label">key points</div>
    <div>{chip_rows}</div>
    {_footer(f"section · chapter_{chapter_no:02d}", slide_no, total)}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cells.append(
            f"""
      <div class="kb-card">
        <div class="kb-step-num">POINT {i + 1:02d}</div>
        <h4>{_rich(head or bullet)}</h4>
        <p>{_rich(body if head else "来自原文的核心要点提炼。")}</p>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="kb-card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">{_esc(slide.get("section") or "content")}</div>
    <h2 class="kb-h1" style="font-size:48px">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="kb-section-label">key cards</div>
    <div class="kb-grid-2">{''.join(cells)}</div>
    {_footer("content · cards", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    steps = []
    hero_idx = 0
    for i, bullet in enumerate(bullets[:5]):
        head, body = _split_kv(bullet)
        hero_cls = " hero" if i == hero_idx else ""
        steps.append(
            f"""
      <div class="kb-step{hero_cls}">
        <div class="kb-step-num">STEP {i + 1:02d}</div>
        <div class="kb-step-title">{_rich(head or f"步骤 {i + 1}")}</div>
        <div class="kb-step-body">{_rich(body if head else bullet)}</div>
      </div>
            """
        )
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">{_esc(slide.get("section") or "pipeline")}</div>
    <h2 class="kb-h1" style="font-size:48px">{_rich(slide.get("title") or "过程拆解")}</h2>
    <div class="kb-section-label">pipeline</div>
    <div class="kb-pipeline">{''.join(steps)}</div>
    {_footer("content · pipeline", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thank you"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。"
    inner = f"""
    {_grid_bg()}
    <div class="kb-kicker">end · blueprint</div>
    <h1 class="kb-h1"><span class="rust">{_rich(title)}</span></h1>
    <p class="kb-sub">{_rich(message)}</p>
    <div style="margin-top:28px">
      <span class="kb-insight">
        <span class="kk">CREDIT</span>
        fxt ppt · knowledge-arch-blueprint · auto-generated
      </span>
    </div>
    {_footer("end · eof", slide_no, total)}
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


def render_knowledge_arch_blueprint(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "奶油蓝图架构")
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
<body class="tpl-knowledge-arch-blueprint">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_knowledge_arch_blueprint"]
