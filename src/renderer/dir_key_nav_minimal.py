"""Render generic slide_json into the dir-key-nav-minimal deck.

Visual language: one idea per slide, giant typography, 8 cycled background
themes (indigo/cream/crimson/emerald/slate/violet/white/charcoal). Slides
use bespoke .dk-* class vocabulary; the theme class goes on .slide itself.
"""
from __future__ import annotations

import html
from typing import Any

from . import layouts as L

THEMES = ["t-indigo", "t-cream", "t-crimson", "t-emerald", "t-slate", "t-violet", "t-white", "t-charcoal"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="dk-accent">{part}</span>')
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


def _section(inner: str, theme: str, *, active: bool = False, title: str = "") -> str:
    classes = " ".join(c for c in ["slide", "is-active" if active else "", theme] if c)
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{classes}"{data_title}>{inner}</section>'


def _meta(slide_no: int, total: int, eyebrow: str) -> str:
    return (
        f'<div class="dk-snum">{slide_no:02d} / {total:02d}</div>'
        f'<div class="dk-page">{eyebrow}</div>'
    )


def _keyhint() -> str:
    return '<div class="dk-keyhint">use <kbd>←</kbd><kbd>→</kbd> to navigate</div>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "untitled"
    subtitle = generic.get("subtitle") or "auto-generated minimal deck"
    inner = f"""
    {_meta(slide_no, total, "cover")}
    <div class="dk-eyebrow">fxt ppt · auto-generated</div>
    <h1 class="dk-h0">{_rich(title)}</h1>
    <span class="dk-line"></span>
    <p class="dk-lede">{_rich(subtitle)}</p>
    {_keyhint()}
    """
    return _section(inner, THEMES[0], active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    items = "".join(f"<li>{_rich(t)}</li>" for t in chapters[:8])
    theme = THEMES[1]
    inner = f"""
    {_meta(slide_no, total, "contents")}
    <div class="dk-eyebrow">outline</div>
    <h2 class="dk-h1">{len(chapters)} ideas, <span class="dk-accent">one slide each</span></h2>
    <ul class="dk-list">{items}</ul>
    {_keyhint()}
    """
    return _section(inner, theme, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    theme = THEMES[chapter_no % len(THEMES)]
    items = "".join(f"<li>{_rich(p)}</li>" for p in points[:3])
    inner = f"""
    {_meta(slide_no, total, f"part {chapter_no:02d}")}
    <div class="dk-eyebrow">part · {chapter_no:02d}</div>
    <div class="dk-big">{chapter_no:02d}</div>
    <h2 class="dk-h2">{_rich(title)}</h2>
    <ul class="dk-list">{items}</ul>
    {_keyhint()}
    """
    return _section(inner, theme, title=title)


def _cards(slide: dict[str, Any], theme: str, slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    if len(bullets) <= 4:
        # show as a clean ordered list under a giant title — one idea per slide spirit
        items = "".join(f"<li>{_rich(b)}</li>" for b in bullets)
        body = f'<ul class="dk-list">{items}</ul>'
    else:
        # 2-col grid for denser content
        cols = []
        for i, bullet in enumerate(bullets[:6]):
            head, txt = _split_kv(bullet)
            cols.append(
                f'<div class="dk-col"><h3>{_rich(head or f"point {i + 1:02d}")}</h3><p>{_rich(txt if head else bullet)}</p></div>'
            )
        body = f'<div class="dk-grid-2">{"".join(cols)}</div>'
    eyebrow = slide.get("section") or "idea"
    inner = f"""
    {_meta(slide_no, total, str(eyebrow).lower())}
    <div class="dk-eyebrow">{_esc(eyebrow)}</div>
    <h2 class="dk-h2">{_rich(slide.get("title") or "key idea")}</h2>
    <span class="dk-line"></span>
    {body}
    {_keyhint()}
    """
    return _section(inner, theme, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], theme: str, slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:6]
    items = "".join(f"<li>{_rich(b)}</li>" for b in bullets)
    eyebrow = slide.get("section") or "process"
    inner = f"""
    {_meta(slide_no, total, "process")}
    <div class="dk-eyebrow">{_esc(eyebrow)}</div>
    <h2 class="dk-h2">{_rich(slide.get("title") or "step by step")}</h2>
    <ul class="dk-list">{items}</ul>
    {_keyhint()}
    """
    return _section(inner, theme, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "thanks."
    message = slide.get("notes") or slide.get("speaker_notes") or "press → to start over."
    inner = f"""
    {_meta(slide_no, total, "end")}
    <div class="dk-eyebrow">end · deck</div>
    <h1 class="dk-h0">{_rich(title)}</h1>
    <span class="dk-line"></span>
    <p class="dk-lede">{_rich(message)}</p>
    {_keyhint()}
    """
    return _section(inner, THEMES[7], title=str(title))


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


def render_dir_key_nav_minimal(generic: dict[str, Any]) -> str:
    planned = _planned_slides(generic)
    total = len(planned)
    sections: list[str] = []
    chapter_no = 0
    content_no = 0
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
            content_no += 1
            theme = THEMES[(chapter_no + content_no) % len(THEMES)]
            bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
            layout = L.normalize_layout(slide.get("layout"), len(bullets))
            if layout == "cards":
                sections.append(_cards(slide, theme, idx, total))
            elif layout == "bullets":
                sections.append(_steps(slide, theme, idx, total))
            else:
                body = L.render_inner(layout, slide)
                eyebrow = slide.get("section") or "idea"
                inner = f"""
    {_meta(idx, total, str(eyebrow).lower())}
    <div class="dk-eyebrow">{_esc(eyebrow)}</div>
    <h2 class="dk-h2">{_rich(slide.get("title") or "")}</h2>
    <span class="dk-line"></span>
    {body}
    {_keyhint()}
    """
                sections.append(_section(inner, theme, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "方向键 8 色极简")
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
<body class="tpl-dir-key-nav-minimal">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_dir_key_nav_minimal"]
