"""Render generic slide_json into the xhs-pastel-card deck.

Visual language: cream background, macaron color blobs, Playfair Display
serif headlines with italic accents, six pastel card colors cycling through
peach / mint / sky / lilac / lemon / rose.
"""
from __future__ import annotations

import html
from typing import Any

PASTELS = ["peach", "mint", "sky", "lilac", "lemon", "rose"]
CHIP_COLORS = ["", "mint", "sky", "lilac", "rose"]  # empty == default peach dot


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


def _blobs(*which: str) -> str:
    return "".join(f'<div class="xp-blob {b}"></div>' for b in which)


def _top(chip_text: str, chip_color: str, slide_no: int, total: int) -> str:
    cls = f"xp-chip {chip_color}".strip()
    return f"""
    <div class="xp-topbar">
      <div class="{cls}">{_esc(chip_text)}</div>
      <div class="xp-page">{slide_no:02d} · {total:02d}</div>
    </div>
    """


def _footer(left: str, slide_no: int, total: int) -> str:
    return f"""
    <div class="xp-footer"><span>{_esc(left)}</span><span>{slide_no:02d} · {total:02d}</span></div>
    """


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "把文稿整理成一份柔和的内容 deck"
    inner = f"""
    {_blobs("b1", "b2", "b3")}
    {_top("A soft manifesto", "", slide_no, total)}
    <div class="xp-kicker">基于文稿生成</div>
    <h1 class="xp-h1">{_rich(title)}</h1>
    <div class="xp-divider"></div>
    <p class="xp-sub">{_rich(subtitle)}</p>
    {_footer("by fxt ppt · pastel edition", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, title in enumerate(chapters[:6]):
        color = PASTELS[i % len(PASTELS)]
        cards.append(
            f"""
      <div class="xp-card {color}">
        <div class="xp-num">{i + 1:02d}</div>
        <h4>{_rich(title)}</h4>
        <p>本部分提炼原文的关键观点。</p>
      </div>
            """
        )
    grid_cls = "xp-grid-3" if len(cards) >= 3 else "xp-grid-2"
    inner = f"""
    {_blobs("b2", "b3")}
    {_top("Contents", "mint", slide_no, total)}
    <h2 class="xp-h2">这份内容分为 <em>{len(cards)} 个</em>部分</h2>
    <div class="xp-divider"></div>
    <div class="{grid_cls}">{''.join(cards)}</div>
    {_footer("contents", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    chip_color = CHIP_COLORS[chapter_no % len(CHIP_COLORS)]
    chip_items: list[str] = []
    for j, p in enumerate(points[:3]):
        color = PASTELS[(chapter_no + j) % len(PASTELS)]
        chip_items.append(
            f'<div class="xp-card {color}" style="padding:14px 20px;display:inline-block;margin:6px 8px 0 0"><h4 style="margin:0;font-size:15px">{_rich(p)}</h4></div>'
        )
    chips = "".join(chip_items)
    inner = f"""
    {_blobs("b1", "b3")}
    {_top(f"Chapter · {chapter_no:02d}", chip_color, slide_no, total)}
    <div style="margin-top:80px">
      <div class="xp-kicker">第 {chapter_no} 部分</div>
      <h1 class="xp-h1" style="font-size:120px">{_rich(title)}</h1>
      <div class="xp-divider"></div>
      <p class="xp-sub">先建立结构，再展开重点。</p>
      <div style="margin-top:24px">{chips}</div>
    </div>
    {_footer(f"section · chapter {chapter_no}", slide_no, total)}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cards = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        color = PASTELS[i % len(PASTELS)]
        cards.append(
            f"""
      <div class="xp-card {color}">
        <div class="xp-num">{i + 1:02d}</div>
        <h4>{_rich(head or bullet)}</h4>
        <p>{_rich(body if head else "来自原文的核心要点提炼。")}</p>
      </div>
            """
        )
    if not cards:
        cards.append(
            f'<div class="xp-card peach"><h4>{_rich(slide.get("title", ""))}</h4></div>'
        )
    n = len(cards)
    if n >= 4:
        grid_cls = "xp-grid-2"
    elif n == 3:
        grid_cls = "xp-grid-3"
    else:
        grid_cls = "xp-grid-2"
    chip_text = _esc(slide.get("section") or slide.get("title") or "Highlights")
    inner = f"""
    {_blobs("b1")}
    {_top(chip_text, "rose", slide_no, total)}
    <h2 class="xp-h2">{_rich(slide.get("title") or "核心要点")}</h2>
    <div class="xp-divider"></div>
    <div class="{grid_cls}">{''.join(cards)}</div>
    {_footer(f"content · {grid_cls.split('-')[-1]}-up", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        color = PASTELS[i % len(PASTELS)]
        text = body if (head and body) else bullet
        title_text = head or f"步骤 {i + 1}"
        rows.append(
            f"""
      <div class="xp-card {color}" style="padding:18px 24px;display:flex;align-items:center;gap:18px;margin-bottom:10px">
        <div class="xp-num" style="font-size:42px">{i + 1:02d}</div>
        <div>
          <h4 style="margin:0">{_rich(title_text)}</h4>
          <p style="margin-top:4px">{_rich(text if head else "")}</p>
        </div>
      </div>
            """
        )
    quote = slide.get("notes") or slide.get("speaker_notes") or "把每一步讲清楚，读者就能跟上你的判断过程。"
    inner = f"""
    {_blobs("b2", "b3")}
    {_top(slide.get("section") or "Process", "lilac", slide_no, total)}
    <h2 class="xp-h2">{_rich(slide.get("title") or "过程拆解")}</h2>
    <div class="xp-divider"></div>
    <div style="margin-top:18px">{''.join(rows)}</div>
    <div class="xp-hero-card" style="margin-top:22px;padding:22px 28px">
      <p class="xp-quote" style="font-size:28px">{_rich(quote)}</p>
    </div>
    {_footer("content · steps", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "谢谢"
    message = slide.get("notes") or slide.get("speaker_notes") or "欢迎继续讨论，也欢迎把这份内容改造成你自己的表达。"
    inner = f"""
    {_blobs("b1", "b2", "b3")}
    {_top("Thank you", "rose", slide_no, total)}
    <div style="margin-top:100px">
      <h1 class="xp-h1" style="font-size:140px">{_rich(title)}</h1>
      <div class="xp-divider"></div>
      <p class="xp-sub" style="font-size:26px">{_rich(message)}</p>
      <div style="margin-top:30px">
        <span class="xp-chip">fxt ppt</span>
        <span class="xp-chip mint">xhs-pastel-card</span>
        <span class="xp-chip rose">generated</span>
      </div>
    </div>
    {_footer("end", slide_no, total)}
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


def render_xhs_pastel_card(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "小红书柔和马卡龙")
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
<body class="tpl-xhs-pastel-card">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_xhs_pastel_card"]
