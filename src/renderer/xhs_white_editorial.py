"""Render generic slide_json into the xhs-white-editorial deck."""
from __future__ import annotations

import html
from typing import Any

SOFT_CLASSES = ["soft-pink", "soft-blue", "soft-green", "soft-orange", "soft-purple"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    # Tiny safe vocab matching this template's visual language.
    out: list[str] = []
    parts = text.split("**")
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="xw-focus">{part}</span>')
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


def _top(slide_no: int, total: int, tag: str) -> str:
    return f"""
    <div class="xw-topline"></div>
    <div class="xw-topbar">
      <div class="xw-tag"><span class="dot"></span>{_esc(tag)}</div>
      <div class="xw-page">{slide_no:02d} / {total:02d}</div>
    </div>
    """


def _footer(slide_no: int, total: int, label: str) -> str:
    return f"""
    <div class="xw-footer"><span>{_esc(label)}</span><span>{slide_no:02d} / {total:02d}</span></div>
    """


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f"<section class=\"{cls}\"{data_title}>{inner}</section>"


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "把文稿整理成一份白底杂志风内容 deck"
    inner = f"""
    {_top(slide_no, total, "内容生成 · 白底杂志风")}
    <div class="xw-kicker">基于文稿自动生成</div>
    <h1 class="xw-title">{_rich(title)}</h1>
    <p class="xw-sub">{_rich(subtitle)}</p>
    <div class="xw-hero">
      <div class="xw-quote">先把复杂内容讲清楚，<br>再用 <span class="xw-focus">重点块</span> 抓住读者注意力。</div>
    </div>
    {_footer(slide_no, total, "Cover · xhs-white-editorial")}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, title in enumerate(chapters[:6]):
        cards.append(
            f"""
      <div class="xw-card {SOFT_CLASSES[i % len(SOFT_CLASSES)]}">
        <div class="xw-label">Part {i + 1:02d}</div>
        <div class="main">{_rich(title)}</div>
        <div class="desc">本部分提炼文稿中的关键观点。</div>
      </div>
            """
        )
    grid_cls = "xw-grid-3" if len(cards) >= 3 else "xw-grid-2"
    inner = f"""
    {_top(slide_no, total, "内容目录")}
    <h2 class="xw-title-md">这份内容分为 <span class="xw-grad">{len(cards)} 个部分</span></h2>
    <div class="{grid_cls}">{''.join(cards)}</div>
    {_footer(slide_no, total, "Contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    shown = points[:3]
    chips = "".join(f'<span class="xw-pill">{_rich(p)}</span>' for p in shown)
    inner = f"""
    {_top(slide_no, total, f"Chapter · {chapter_no:02d}")}
    <div style="margin-top:110px">
      <div class="xw-kicker" style="font-size:20px;letter-spacing:.2em;text-transform:uppercase;color:#98a2b3">第 {chapter_no} 部分</div>
      <h1 class="xw-title" style="font-size:94px;margin-top:20px">{_rich(title)}</h1>
      <p class="xw-sub" style="font-size:26px">先建立结构，再展开重点。</p>
      <div style="margin-top:34px">{chips}</div>
    </div>
    {_footer(slide_no, total, "Section Divider")}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cards = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cards.append(
            f"""
      <div class="xw-card {SOFT_CLASSES[i % len(SOFT_CLASSES)]}">
        <div class="xw-label">{_rich(head or f"Point {i + 1:02d}")}</div>
        <div class="main">{_rich(body or bullet)}</div>
        <div class="desc">来自原文的核心要点提炼。</div>
      </div>
            """
        )
    if not cards:
        cards.append(
            f'<div class="xw-card soft-blue"><div class="main">{_rich(slide.get("title", ""))}</div></div>'
        )
    grid_cls = "xw-grid-3" if len(cards) in {3, 5, 6} else "xw-grid-2"
    inner = f"""
    {_top(slide_no, total, slide.get("section") or slide.get("title") or "核心要点")}
    <h2 class="xw-title-md">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="{grid_cls}">{''.join(cards)}</div>
    {_footer(slide_no, total, "Content · Cards")}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    steps = []
    for i, bullet in enumerate(bullets[:5]):
        head, body = _split_kv(bullet)
        text = f"{head}：{body}" if head and body else bullet
        steps.append(
            f"""
      <div class="xw-step">
        <div class="xw-num">{i + 1}</div>
        <div class="xw-txt">{_rich(text)}</div>
      </div>
            """
        )
    quote = slide.get("notes") or slide.get("speaker_notes") or "把每一步讲清楚，读者就能跟上你的判断过程。"
    inner = f"""
    {_top(slide_no, total, slide.get("section") or "过程拆解")}
    <h2 class="xw-title-md">{_rich(slide.get("title") or "过程拆解")}</h2>
    <div class="xw-steps">{''.join(steps)}</div>
    <div class="xw-hero"><div class="xw-quote" style="font-size:30px">{_rich(quote)}</div></div>
    {_footer(slide_no, total, "Content · Steps")}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "谢谢"
    message = slide.get("notes") or slide.get("speaker_notes") or "欢迎继续讨论，也欢迎把这份内容改造成你自己的表达。"
    inner = f"""
    {_top(slide_no, total, "Thanks for reading")}
    <div style="margin-top:100px">
      <div class="xw-big-stat xw-grad">{_rich(title)}<small> · thanks</small></div>
      <p class="xw-sub" style="font-size:28px;margin-top:36px">{_rich(message)}</p>
      <div style="margin-top:40px">
        <span class="xw-pill">fxt ppt</span>
        <span class="xw-pill">xhs-white-editorial</span>
        <span class="xw-pill">generated deck</span>
      </div>
    </div>
    {_footer(slide_no, total, "End")}
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


def render_xhs_white_editorial(generic: dict[str, Any]) -> str:
    """Return a complete static HTML deck for xhs-white-editorial."""
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
            title = slide.get("title") or f"第 {chapter_no} 部分"
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

    title = _esc(generic.get("title") or "小红书白底杂志风")
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
<body class="tpl-xhs-white-editorial">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_xhs_white_editorial"]
