"""Render generic slide_json into the editorial-monocle deck.

Visual language: dark ink #0a0a0b background with warm paper #f1efea text,
Playfair Display + Noto Serif SC headlines, IBM Plex Mono small-caps meta,
warm rust accent. Adapted from guizang-ppt-skill/template.html.
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
            out.append(f"<em>{part}</em>")
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


def _section(inner: str, *, active: bool = False, title: str = "", extra_class: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    if extra_class:
        cls += " " + extra_class
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _bg() -> str:
    return '<div class="em-bg"></div>'


def _chrome(left: str, right: str) -> str:
    return f"""
    <div class="em-chrome">
      <div class="l">{_esc(left)}<span class="sep"></span></div>
      <div class="r"><span class="sep"></span>{_esc(right)}</div>
    </div>
    """


def _foot(title_text: str, slide_no: int, total: int, tag: str = "Field Note") -> str:
    return f"""
    <div class="em-foot">
      <span>{_esc(tag)}</span>
      <span class="title">{_rich(title_text)}</span>
      <span>{slide_no:02d} / {total:02d}</span>
    </div>
    """


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "用编辑设计的眼光把一份文档变成一本可翻页的小杂志。"
    inner = f"""
    {_bg()}
    <div class="em-cover">
      {_chrome('Editorial · Issue 01', f'Vol · {slide_no:02d} / {total:02d}')}
      <div class="lead-block">
        <div class="em-kicker">cover &middot; manifesto</div>
        <h1 class="em-display">{_rich(title)}</h1>
        <p class="em-lead"><span class="em-hi">{_rich(subtitle)}</span></p>
        <div class="em-meta-row">
          <span>Editor &middot; Field Notes</span>
          <span class="dot"></span>
          <span>Editorial &middot; Monocle</span>
          <span class="dot"></span>
          <span>YY.MM.DD</span>
        </div>
      </div>
      <div class="em-cover-sig">
        <span>→ swipe / arrow keys</span>
        <span class="nb">{slide_no:02d} / {total:02d}</span>
      </div>
    </div>
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:6]):
        rows.append(
            f"""
      <div class="em-toc-row">
        <div class="em-toc-num">{i + 1:02d}</div>
        <div class="em-toc-title">{_rich(t)}</div>
        <div class="em-toc-meta">Chapter · {i + 1:02d}</div>
      </div>
            """
        )
    inner = f"""
    {_bg()}
    {_chrome('Contents · Inside this issue', f'{slide_no:02d} / {total:02d}')}
    <div class="em-kicker" style="margin-top:18px">contents</div>
    <h2 class="em-h1">本期共 <em>{len(rows)}</em> 个章节</h2>
    <p class="em-lead" style="margin-top:16px">沿着目录翻页。每一章先立结构，再展开重点。</p>
    <div class="em-toc">{''.join(rows)}</div>
    {_foot('Contents · Inside this issue', slide_no, total, tag='Contents')}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(
        f'<span class="em-pill">{_rich(p)}</span>' for p in points[:3]
    )
    strip = f'<div class="em-divider-strip">{pills}</div>' if pills else ""
    inner = f"""
    {_bg()}
    {_chrome(f'Chapter · {chapter_no:02d}', f'{slide_no:02d} / {total:02d}')}
    <div class="em-divider-stage">
      <div class="em-divider-num">{chapter_no:02d}</div>
      <h2 class="em-divider-title">{_rich(title)}</h2>
      <p class="em-lead" style="margin-top:6px">先建立这一章的结构，再展开关键点。</p>
      {strip}
    </div>
    {_foot(title, slide_no, total, tag=f'Chapter {chapter_no:02d}')}
    """
    return _section(inner, title=title)


def _content_header(slide: dict[str, Any], label: str) -> str:
    title = slide.get("title") or "核心要点"
    return f"""
    <div class="em-kicker">{_esc(label)}</div>
    <h2 class="em-h2">{_rich(title)}</h2>
    """


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cards = []
    hero_idx = 0
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        hero_cls = " hero" if i == hero_idx else ""
        body_html = f"<p>{_rich(body)}</p>" if (head and body) else ""
        cards.append(
            f"""
      <div class="em-card{hero_cls}" data-n="{i + 1:02d}">
        <div class="em-card-num">Point {i + 1:02d}</div>
        <h4>{_rich(head or bullet)}</h4>
        {body_html}
      </div>
            """
        )
    if not cards:
        cards.append(f'<div class="em-card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = max(2, min(4, len(cards)))
    inner = f"""
    {_bg()}
    {_chrome(slide.get('section') or 'Content', f'{slide_no:02d} / {total:02d}')}
    {_content_header(slide, 'editorial cards')}
    <div class="em-cards" style="--n:{n}">{''.join(cards)}</div>
    {_foot(slide.get('title') or '内容', slide_no, total, tag='Content')}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    steps = []
    hero_idx = 0
    for i, bullet in enumerate(bullets[:5]):
        head, body = _split_kv(bullet)
        hero_cls = " hero" if i == hero_idx else ""
        body_html = f'<p>{_rich(body if head else bullet)}</p>' if (head or body) else ""
        steps.append(
            f"""
      <div class="em-step{hero_cls}">
        <div class="nb">{i + 1:02d}</div>
        <div>
          <h4>{_rich(head or f"阶段 {i + 1}")}</h4>
          {body_html}
        </div>
        <div class="meta">Step · {i + 1:02d}</div>
      </div>
            """
        )
    inner = f"""
    {_bg()}
    {_chrome(slide.get('section') or 'Pipeline', f'{slide_no:02d} / {total:02d}')}
    {_content_header(slide, 'pipeline')}
    <div class="em-steps">{''.join(steps)}</div>
    {_foot(slide.get('title') or '过程', slide_no, total, tag='Pipeline')}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Build a model. Run forever."
    message = slide.get("notes") or slide.get("speaker_notes") or "把每个章节落到一句话上。一本可翻页的小杂志收束于此。"
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:3]
    rows = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        body_html = f"<p>{_rich(body if head else b)}</p>" if (head or body) else ""
        rows.append(
            f"""
      <div class="em-closing-row">
        <div class="nb">{i + 1:02d}</div>
        <div>
          <h4>{_rich(head or f"Takeaway {i + 1:02d}")}</h4>
          {body_html}
        </div>
      </div>
            """
        )
    rules = f'<div class="em-closing-rules">{"".join(rows)}</div>' if rows else ""
    inner = f"""
    {_bg()}
    {_chrome('Closing · Manifesto', f'{slide_no:02d} / {total:02d}')}
    <div class="em-closing">
      <div class="em-closing-left">
        <div>
          <div class="em-kicker">manifesto</div>
          <span class="em-closing-mark">&ldquo;</span>
          <h2 class="em-display" style="margin-top:14px">{_rich(title)}</h2>
          <p class="em-lead" style="margin-top:18px">{_rich(message)}</p>
        </div>
        <div class="em-meta-row">
          <span>End of issue</span>
          <span class="dot"></span>
          <span>{slide_no:02d} / {total:02d}</span>
        </div>
      </div>
      {rules}
    </div>
    {_foot(title, slide_no, total, tag='Closing')}
    """
    return _section(inner, title=str(title))


def render_editorial_monocle(generic: dict[str, Any]) -> str:
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
            title = slide.get("title") or f"Chapter {chapter_no}"
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
    {_bg()}
    {_chrome(slide.get('section') or 'Content', f'{idx:02d} / {total:02d}')}
    {_content_header(slide, layout.replace('-', ' '))}
    {body}
    {_foot(slide.get('title') or '内容', idx, total, tag='Content')}
    """
                sections.append(_section(inner, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "Editorial Monocle · Field Notes")
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
<body class="tpl-editorial-monocle">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_editorial_monocle"]
