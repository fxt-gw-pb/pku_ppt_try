"""Render generic slide_json into the swiss-grid deck.

Visual language: off-white paper, IKB blue as single anchor, ultra-thin
200-weight headlines, JetBrains Mono small-caps labels, rule lines and
dot-matrix backdrops. Adapted from guizang-ppt-skill/template-swiss.html.
"""
from __future__ import annotations

import html
from typing import Any

from . import layouts as L


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    """Minimal rich-text: ``**phrase**`` becomes an italic IKB-blue emphasis."""
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


def _dot_bg() -> str:
    return '<div class="sw-dot-bg"></div>'


def _chrome(left: str, right: str) -> str:
    return f"""
    <div class="sw-chrome">
      <div class="l"><span class="dot"></span>{_esc(left)}</div>
      <div class="r">{_esc(right)}</div>
    </div>
    """


def _foot(left: str, slide_no: int, total: int) -> str:
    return f"""
    <div class="sw-foot">
      <span>{_esc(left)}</span>
      <span>{slide_no:02d} &middot; {total:02d}</span>
    </div>
    """


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or ""
    deck_id = f"SS · {slide_no:02d} / {total:02d}"
    inner = f"""
    {_dot_bg()}
    <div class="sw-cover">
      {_chrome(generic.get('subtitle') or 'FIELD NOTE · ISSUE 01', deck_id)}
      <div class="lead-block">
        <div class="sw-kicker">[ index ] cover · 主题宣告</div>
        <h1 class="sw-hero">{_rich(title)}</h1>
        <p class="sw-lead">{_rich(subtitle) if subtitle else '把原文的结构和判断整理为一份字段笔记，逐章交付。'}</p>
        <div class="sw-meta-row">
          <span>{_esc('Editor · field notes')}</span>
          <span class="dot"></span>
          <span>{_esc('Swiss Grid · IKB')}</span>
          <span class="dot"></span>
          <span>YY.MM.DD</span>
        </div>
      </div>
      <div class="sw-cover-meta">
        <span>→ swipe / arrow keys</span>
        <span>{slide_no:02d} / {total:02d}</span>
      </div>
    </div>
    """
    return _section(inner, active=active, title=str(title), extra_class="is-accent")


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:6]):
        accent_cls = " is-accent" if i == 0 else ""
        rows.append(
            f"""
      <div class="sw-toc-row{accent_cls}">
        <div class="sw-toc-num">{i + 1:02d}</div>
        <div class="sw-toc-title">{_rich(t)}</div>
        <div class="sw-toc-meta">Part · {i + 1:02d}</div>
      </div>
            """
        )
    inner = f"""
    {_chrome('contents · 目录索引', f'{slide_no:02d} / {total:02d}')}
    <div class="sw-kicker">contents</div>
    <h2 class="sw-h1">这份内容分为 <em>{len(rows)}</em> 个区段</h2>
    <p class="sw-lead">沿着下面的轴线展开。第一条用 IKB 蓝标注为本场重点。</p>
    <div class="sw-toc">{''.join(rows)}</div>
    {_foot('contents · ledger', slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    chips = "".join(
        f'<span class="sw-tag">{_rich(p)}</span>' for p in points[:3]
    )
    chip_row = (
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px">{chips}</div>'
        if chips else ""
    )
    inner = f"""
    {_dot_bg()}
    {_chrome(f'section · part {chapter_no:02d}', f'{slide_no:02d} / {total:02d}')}
    <div class="sw-divider-stage">
      <div class="sw-divider-num">{chapter_no:02d}</div>
      <div class="sw-divider-body">
        <div class="sw-kicker is-accent no-line">part · {chapter_no:02d}</div>
        <h2 class="sw-hero">{_rich(title)}</h2>
        <p class="sw-lead">先建立结构，再展开重点。本段焦点见下方。</p>
        {chip_row}
      </div>
    </div>
    {_foot(f'section · chapter_{chapter_no:02d}', slide_no, total)}
    """
    return _section(inner, title=title)


def _content_header(slide: dict[str, Any], label: str) -> str:
    title = slide.get("title") or "核心要点"
    return f"""
    <div class="sw-content-header">
      <h2 class="sw-h2">{_rich(title)}</h2>
      <div class="sw-section-label">{_esc(label)}</div>
    </div>
    """


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cards = []
    accent_idx = 0
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        accent_cls = " is-accent" if i == accent_idx else ""
        body_html = f"<p>{_rich(body)}</p>" if (head and body) else ""
        cards.append(
            f"""
      <div class="sw-card{accent_cls}">
        <div class="nb">Point {i + 1:02d}</div>
        <h4>{_rich(head or bullet)}</h4>
        {body_html}
      </div>
            """
        )
    if not cards:
        cards.append(f'<div class="sw-card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = max(2, min(4, len(cards)))
    inner = f"""
    {_chrome(slide.get('section') or 'content', f'{slide_no:02d} / {total:02d}')}
    {_content_header(slide, 'key cards')}
    <div class="sw-cards" style="--n:{n}">{''.join(cards)}</div>
    {_foot('content · cards', slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    steps = []
    accent_idx = 0
    for i, bullet in enumerate(bullets[:5]):
        head, body = _split_kv(bullet)
        accent_cls = " is-accent" if i == accent_idx else ""
        body_html = f"<p>{_rich(body if head else bullet)}</p>" if (head or body) else ""
        steps.append(
            f"""
      <div class="sw-step{accent_cls}">
        <div class="nb">Step {i + 1:02d}</div>
        <h4>{_rich(head or f"阶段 {i + 1}")}</h4>
        {body_html}
      </div>
            """
        )
    n = max(2, min(5, len(steps)))
    inner = f"""
    {_chrome(slide.get('section') or 'pipeline', f'{slide_no:02d} / {total:02d}')}
    {_content_header(slide, 'pipeline · steps')}
    <div class="sw-steps" style="--n:{n}">{''.join(steps)}</div>
    {_foot('content · pipeline', slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Build a model. Run forever."
    message = slide.get("notes") or slide.get("speaker_notes") or "用单一色彩、单一字体和精准的网格完成本场闭环。"
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:3]
    rows = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        body_html = f'<div class="sw-take-body">{_rich(body if head else b)}</div>' if (head or body) else ""
        rows.append(
            f"""
      <div class="sw-take-row">
        <div class="sw-take-num">{i + 1:02d}</div>
        <div>
          <div class="sw-take-title">{_rich(head or f"Takeaway {i + 1:02d}")}</div>
          {body_html}
        </div>
      </div>
            """
        )
    take_block = f'<div class="sw-takeaways">{"".join(rows)}</div>' if rows else ""
    inner = f"""
    {_dot_bg()}
    {_chrome('closing · manifesto', f'{slide_no:02d} / {total:02d}')}
    <div class="sw-kicker">manifesto</div>
    <h2 class="sw-hero">{_rich(title)}</h2>
    <p class="sw-lead" style="margin-top:18px">{_rich(message)}</p>
    {take_block}
    {_foot('end · field note', slide_no, total)}
    """
    return _section(inner, title=str(title))


def render_swiss_grid(generic: dict[str, Any]) -> str:
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
    {_chrome(slide.get('section') or 'content', f'{idx:02d} / {total:02d}')}
    {_content_header(slide, layout.replace('-', ' '))}
    {body}
    {_foot(f'content · {layout}', idx, total)}
    """
                sections.append(_section(inner, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "Swiss Grid · Field Notes")
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
<body class="tpl-swiss-grid">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_swiss_grid"]
