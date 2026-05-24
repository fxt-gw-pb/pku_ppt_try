"""Render generic slide_json into the obsidian-claude-gradient deck.

Visual language: GitHub-dark backdrop with purple→blue→green gradient
washes, center-aligned typography, soft surface cards with color badges,
purple-glow tags.
"""
from __future__ import annotations

import html
from typing import Any

from . import layouts as L

BADGE_COLORS = ["oc-bp", "oc-bb", "oc-bg", "oc-bo"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="oc-g">{part}</span>')
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


def _backdrop() -> str:
    return '<div class="oc-cbg"></div><div class="oc-cgrid"></div>'


def _snum(slide_no: int, total: int) -> str:
    return f'<div class="oc-snum">{slide_no:02d} · {total:02d}</div>'


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or ""
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <h1 class="oc-h1"><span class="oc-g">{_rich(title)}</span></h1>
    <p class="oc-sub">{_rich(subtitle)}</p>
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cells = []
    for i, t in enumerate(chapters[:6]):
        badge = BADGE_COLORS[i % len(BADGE_COLORS)]
        cells.append(
            f"""
      <div class="oc-card">
        <span class="oc-badge {badge}">PART {i + 1:02d}</span>
        <div style="font-size:18px;font-weight:700;margin:6px 0 4px">{_rich(t)}</div>
      </div>
            """
        )
    grid_cls = "oc-grid-3" if len(cells) >= 3 else "oc-grid-2"
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <div class="oc-tag">contents</div>
    <h2 class="oc-h2">这份内容分为 <span class="oc-g">{len(cells)} 个部分</span></h2>
    <div class="{grid_cls}">{''.join(cells)}</div>
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(f'<span class="oc-pill">{_esc(p)}</span>' for p in points[:4])
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <div class="oc-tag">part · {chapter_no:02d}</div>
    <div class="oc-big oc-g">{chapter_no:02d}</div>
    <h2 class="oc-h2" style="margin-top:14px">{_rich(title)}</h2>
    <p class="oc-sub">先建立结构，再展开重点。</p>
    <div style="margin-top:18px">{pills}</div>
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        badge = BADGE_COLORS[i % len(BADGE_COLORS)]
        cells.append(
            f"""
      <div class="oc-card">
        <span class="oc-badge {badge}">{_rich(head or f"POINT {i + 1:02d}")}</span>
        <div style="font-size:18px;font-weight:700;margin:8px 0 6px">{_rich(body or bullet)}</div>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="oc-card"><div style="font-size:18px">{_rich(slide.get("title", ""))}</div></div>')
    n = len(cells)
    grid_cls = "oc-grid-3" if n in {3, 6} else "oc-grid-2"
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <div class="oc-tag">{_esc(slide.get("section") or "content")}</div>
    <h2 class="oc-h2">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="{grid_cls}">{''.join(cells)}</div>
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    items = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        items.append(
            f"""
      <div class="oc-step">
        <div class="oc-sn">{i + 1}</div>
        <div class="oc-sc">
          <h4>{_rich(head or f"步骤 {i + 1}")}</h4>
          <p>{_rich(body if head else bullet)}</p>
        </div>
      </div>
            """
        )
    quote_text = slide.get("notes") or slide.get("speaker_notes") or "逐步执行；每一步都能观察、回滚。"
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <div class="oc-tag">{_esc(slide.get("section") or "pipeline")}</div>
    <h2 class="oc-h2">{_rich(slide.get("title") or "过程拆解")}</h2>
    <div class="oc-steps">{''.join(items)}</div>
    <div class="oc-hl" style="margin-top:22px">{_rich(quote_text)}</div>
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。"
    inner = f"""
    {_backdrop()}
    {_snum(slide_no, total)}
    <div class="oc-tag">end</div>
    <h1 class="oc-h1"><span class="oc-g">{_rich(title)}</span></h1>
    <p class="oc-sub">{_rich(message)}</p>
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


def render_obsidian_claude_gradient(generic: dict[str, Any]) -> str:
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
            layout = L.normalize_layout(slide.get("layout"), len(bullets))
            if layout == "cards":
                sections.append(_cards(slide, idx, total))
            elif layout == "bullets":
                sections.append(_steps(slide, idx, total))
            else:
                body = L.render_inner(layout, slide)
                inner = f"""
    {_backdrop()}
    {_snum(idx, total)}
    <div class="oc-tag">{_esc(slide.get("section") or "content")}</div>
    <h2 class="oc-h2">{_rich(slide.get("title") or "")}</h2>
    {body}
    """
                sections.append(_section(inner, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "GitHub 暗紫渐变")
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
<body class="tpl-obsidian-claude-gradient">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_obsidian_claude_gradient"]
