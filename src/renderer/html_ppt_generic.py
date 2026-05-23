"""Generic renderer for imported html-ppt full-deck templates."""
from __future__ import annotations

import html
from typing import Any


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        out.append(f'<span class="gradient-text">{part}</span>' if i % 2 else part)
    return "".join(out).replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")


def _split_kv(bullet: str) -> tuple[str, str]:
    for sep in ("：", ":"):
        if sep in bullet:
            head, _, tail = bullet.partition(sep)
            head, tail = head.strip(), tail.strip()
            if head and tail:
                return head, tail
    return "", bullet.strip()


def _section(inner: str, *, title: str, active: bool = False, extra_class: str = "") -> str:
    classes = " ".join(x for x in ["slide", "is-active" if active else "", extra_class] if x)
    return f'<section class="{classes}" data-title="{_esc(title)}">{inner}</section>'


def _footer(current: int, total: int) -> str:
    return f'<div class="deck-footer"><span>Generated deck</span><span>{current:02d} / {total:02d}</span></div>'


def _cover(generic: dict[str, Any], current: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Generated with html-ppt"
    inner = f"""
      <p class="kicker">Generated deck</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(subtitle)}</p>
      <div class="row wrap mt-l">
        <span class="pill pill-accent">HTML PPT</span>
        <span class="pill">模板生成</span>
        <span class="pill">文稿整理</span>
      </div>
      {_footer(current, total)}
    """
    return _section(inner, title=str(title), active=active)


def _contents(chapters: list[str], current: int, total: int) -> str:
    items = []
    for i, title in enumerate(chapters[:6]):
        items.append(
            f"""
        <div class="card card-hover">
          <p class="kicker">Part {i + 1:02d}</p>
          <h4>{_rich(title)}</h4>
          <p class="dim">本部分提炼原文中的关键论点。</p>
        </div>
            """
        )
    inner = f"""
      <p class="kicker">Contents</p>
      <h2 class="h2">内容结构</h2>
      <div class="grid g3 mt-l">{''.join(items)}</div>
      {_footer(current, total)}
    """
    return _section(inner, title="目录")


def _divider(slide: dict[str, Any], chapter_no: int, current: int, total: int) -> str:
    title = slide.get("title") or f"第 {chapter_no} 部分"
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:4]
    pills = "".join(f'<span class="pill pill-accent">{_rich(b)}</span>' for b in bullets)
    inner = f"""
      <p class="kicker">Chapter {chapter_no:02d}</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-m">先建立结构，再展开重点。</p>
      <div class="row wrap mt-l">{pills}</div>
      {_footer(current, total)}
    """
    return _section(inner, title=str(title), extra_class="full")


def _cards(slide: dict[str, Any], current: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cards = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cards.append(
            f"""
        <div class="card card-hover">
          <p class="kicker">{_rich(head or f"Point {i + 1:02d}")}</p>
          <h4>{_rich(body or bullet)}</h4>
          <p class="dim">来自原文的内容提炼。</p>
        </div>
            """
        )
    if not cards:
        cards.append(f'<div class="card"><h4>{_rich(slide.get("title") or "内容")}</h4></div>')
    grid_class = "g3" if len(cards) >= 3 else "g2"
    inner = f"""
      <p class="kicker">{_rich(slide.get("section") or "Content")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "核心要点")}</h2>
      <div class="grid {grid_class} mt-l">{''.join(cards)}</div>
      {_footer(current, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], current: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        rows.append(
            f"""
        <div class="row mt-m">
          <span class="pill pill-accent">{i + 1:02d}</span>
          <div>
            <h4>{_rich(head or bullet)}</h4>
            <p class="dim">{_rich(body if head else "")}</p>
          </div>
        </div>
            """
        )
    inner = f"""
      <p class="kicker">Process</p>
      <h2 class="h2">{_rich(slide.get("title") or "过程拆解")}</h2>
      <div class="mt-l">{''.join(rows)}</div>
      {_footer(current, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], current: int, total: int) -> str:
    title = slide.get("title") or "谢谢"
    message = slide.get("notes") or slide.get("speaker_notes") or "欢迎继续交流。"
    inner = f"""
      <p class="kicker">Thanks</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(message)}</p>
      <div class="row wrap mt-l">
        <span class="pill pill-accent">Q&A</span>
        <span class="pill">Generated by pku_ppt</span>
      </div>
      {_footer(current, total)}
    """
    return _section(inner, title=str(title), extra_class="full")


def _planned(generic: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    source = [s for s in (generic.get("slides") or []) if isinstance(s, dict)]
    planned: list[tuple[str, dict[str, Any]]] = [("cover", {})]
    if any(s.get("type") == "section" for s in source):
        planned.append(("contents", {}))
    closing: dict[str, Any] | None = None
    for slide in source:
        stype = slide.get("type")
        if stype in {"cover", "contents"}:
            continue
        if stype == "closing":
            closing = slide
        else:
            planned.append((stype or "content", slide))
    planned.append(("closing", closing or {}))
    return planned


def render_html_ppt_generic(
    generic: dict[str, Any],
    *,
    template_id: str,
    body_class: str,
    include_animations: bool = True,
) -> str:
    planned = _planned(generic)
    total = len(planned)
    chapters = [
        (s.get("title") or s.get("section") or "").strip()
        for s in generic.get("slides", [])
        if isinstance(s, dict) and s.get("type") == "section"
    ]
    sections: list[str] = []
    chapter_no = 0
    for i, (kind, slide) in enumerate(planned, start=1):
        if kind == "cover":
            sections.append(_cover(generic, i, total, active=i == 1))
        elif kind == "contents":
            sections.append(_contents(chapters, i, total))
        elif kind == "section":
            chapter_no += 1
            sections.append(_divider(slide, chapter_no, i, total))
        elif kind == "closing":
            sections.append(_closing(slide, i, total))
        elif slide.get("layout") == "timeline" or len(slide.get("bullets") or []) >= 5:
            sections.append(_steps(slide, i, total))
        else:
            sections.append(_cards(slide, i, total))

    title = _esc(generic.get("title") or template_id)
    anim_link = (
        '<link rel="stylesheet" href="assets/animations/animations.css">\n'
        if include_animations
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="assets/fonts.css">
<link rel="stylesheet" href="assets/base.css">
{anim_link}<link rel="stylesheet" href="style.css">
</head>
<body class="{_esc(body_class)}">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_html_ppt_generic"]
