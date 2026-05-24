"""Render generic slide_json into the course-module deck.

Visual language: academic friendly — cream paper, teal/amber accents,
Playfair Display headings. Content slides use a 260px sidebar with course
objectives list (highlighting current chapter) + main panel with
concept-box / exercise / callout. Cover, dividers, closing use .slide.full.
"""
from __future__ import annotations

import html
from typing import Any

from . import layouts as L


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f"<b>{part}</b>")
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


def _section(inner: str, *, active: bool = False, title: str = "", full: bool = False) -> str:
    classes = " ".join(c for c in ["slide", "is-active" if active else "", "full" if full else ""] if c)
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{classes}"{data_title}>{inner}</section>'


def _footer(slide_no: int, total: int, label: str) -> str:
    return f'<div class="deck-footer mono"><span>{_esc(label)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _sidebar(chapters: list[str], current_idx: int, done_until: int) -> str:
    items = []
    for i, t in enumerate(chapters):
        if i < done_until:
            cls = "done"
        elif i == current_idx:
            cls = "current"
        else:
            cls = ""
        items.append(f'<li class="{cls}">{_rich(t)}</li>')
    return f"""
    <aside class="sidebar">
      <h5>Course outline</h5>
      <ul class="obj-list">{''.join(items)}</ul>
    </aside>
    """


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or ""
    inner = f"""
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <p class="lede mt-m" style="max-width:900px">{_rich(subtitle)}</p>
      {_footer(slide_no, total, "cover")}
    """
    return _section(inner, active=active, title=str(title), full=True)


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cells = []
    for i, t in enumerate(chapters[:6]):
        cells.append(
            f"""
      <div class="concept-box">
        <p class="kicker">PART {i + 1:02d}</p>
        <h4>{_rich(t)}</h4>
      </div>
            """
        )
    grid_cls = "grid g3" if len(cells) >= 3 else "grid g2"
    sidebar = _sidebar(chapters, current_idx=-1, done_until=0)
    inner = f"""
    {sidebar}
    <div class="main">
      <p class="kicker">COURSE OUTLINE</p>
      <h2 class="h2">本模块共 {len(cells)} 个章节</h2>
      <div class="{grid_cls} mt-l">{''.join(cells)}</div>
      {_footer(slide_no, total, "contents")}
    </div>
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(f'<span class="pill-academic" style="margin-right:8px">{_esc(p)}</span>' for p in points[:4])
    inner = f"""
      <p class="kicker">CHAPTER · {chapter_no:02d}</p>
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <p class="lede mt-m" style="max-width:880px">先建立结构，再展开重点。</p>
      <div class="mt-l">{pills}</div>
      <div class="callout mt-l"><b>Section objective</b><br>在这一节里我们将拆解 {_esc(title)}。</div>
      {_footer(slide_no, total, f"section · chapter_{chapter_no:02d}")}
    """
    return _section(inner, title=title, full=True)


def _cards(slide: dict[str, Any], chapters: list[str], current_idx: int, slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        body_html = (
            f'<p style="font-size:14px;color:var(--text-2);line-height:1.55;margin-top:6px">{_rich(body)}</p>'
            if (head and body)
            else ""
        )
        cells.append(
            f"""
      <div class="concept-box">
        <p class="kicker">POINT {i + 1:02d}</p>
        <h4>{_rich(head or bullet)}</h4>
        {body_html}
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="concept-box"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "grid g2" if n in {2, 4} else "grid g3"
    sidebar = _sidebar(chapters, current_idx=current_idx, done_until=max(current_idx, 0))
    inner = f"""
    {sidebar}
    <div class="main">
      <p class="kicker">{_esc(slide.get("section") or "concepts")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "核心概念")}</h2>
      <div class="{grid_cls} mt-l">{''.join(cells)}</div>
      {_footer(slide_no, total, "content · concepts")}
    </div>
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], chapters: list[str], current_idx: int, slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        rows.append(
            f"""
      <div class="mcq">
        <div class="letter">{chr(65 + i)}</div>
        <div>
          <b style="font-size:17px">{_rich(head or f"步骤 {i + 1}")}</b>
          <p style="font-size:14px;color:var(--text-2);line-height:1.55;margin-top:4px">{_rich(body if head else bullet)}</p>
        </div>
      </div>
            """
        )
    sidebar = _sidebar(chapters, current_idx=current_idx, done_until=max(current_idx, 0))
    inner = f"""
    {sidebar}
    <div class="main">
      <p class="kicker">{_esc(slide.get("section") or "exercise")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "练习与拆解")}</h2>
      <div class="mt-l">{''.join(rows)}</div>
      <div class="exercise mt-l">{_rich(slide.get("notes") or slide.get("speaker_notes") or "尝试用一句话总结这一节的要点。")}</div>
      {_footer(slide_no, total, "content · exercise")}
    </div>
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Module complete"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你完成本模块。下一步：练习上面的概念，把它讲给同伴听。"
    inner = f"""
      <p class="kicker">END · MODULE</p>
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <p class="lede mt-m" style="max-width:920px">{_rich(message)}</p>
      <div class="callout mt-l"><b>Next module</b><br>把本节的概念整理成一份学习笔记，或者尝试解释给同伴听。</div>
      {_footer(slide_no, total, "module · end")}
    """
    return _section(inner, title=str(title), full=True)


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


def render_course_module(generic: dict[str, Any]) -> str:
    planned = _planned_slides(generic)
    total = len(planned)
    sections: list[str] = []
    chapter_no = 0  # 1-indexed when assigned to a divider
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
            title = slide.get("title") or f"Chapter {chapter_no}"
            points = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
            sections.append(_divider(title, points, chapter_no, idx, total))
        elif kind == "closing":
            sections.append(_closing(slide, idx, total))
        else:
            current_idx = max(chapter_no - 1, 0)
            bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
            layout = L.normalize_layout(slide.get("layout"), len(bullets))
            if layout == "cards":
                sections.append(_cards(slide, chapters, current_idx, idx, total))
            elif layout == "bullets":
                sections.append(_steps(slide, chapters, current_idx, idx, total))
            else:
                body = L.render_inner(layout, slide)
                sidebar = _sidebar(chapters, current_idx=current_idx, done_until=max(current_idx, 0))
                inner = f"""
    {sidebar}
    <div class="main">
      <p class="kicker">{_esc(slide.get("section") or "concepts")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "")}</h2>
      {body}
      {_footer(idx, total, f"content · {layout}")}
    </div>
    """
                sections.append(_section(inner, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "Course Module 教学模块")
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
<body class="tpl-course-module">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_course_module"]
