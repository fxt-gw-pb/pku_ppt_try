"""Render generic slide_json into the product-launch deck.

Visual language: bold launch deck — white surface for content, dark
.slide.dark for cover/closing hero, orange-amber gradient, feature cards
with icon badges, big CTA button.
"""
from __future__ import annotations

import html
from typing import Any

ICON_GLYPHS = ["◆", "●", "▲", "★", "■", "◇"]


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


def _section(inner: str, *, active: bool = False, title: str = "", extra_class: str = "") -> str:
    classes = " ".join(c for c in ["slide", "is-active" if active else "", extra_class] if c)
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{classes}"{data_title}>{inner}</section>'


def _footer(slide_no: int, total: int, label: str) -> str:
    return f'<div class="deck-footer"><span>{_esc(label)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Auto-generated launch deck"
    inner = f"""
    <div class="hero-shot"></div>
    <div style="position:relative;z-index:2;max-width:760px">
      <span class="brand">fxt ppt</span>
      <p class="kicker mt-l">LAUNCH · 2026</p>
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(subtitle)}</p>
      <div class="mt-l"><a class="cta-btn">立即查看</a></div>
    </div>
    {_footer(slide_no, total, "cover · launch")}
    """
    return _section(inner, active=active, title=str(title), extra_class="dark")


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, t in enumerate(chapters[:6]):
        cards.append(
            f"""
      <div class="feature-card">
        <div class="icon">{ICON_GLYPHS[i % len(ICON_GLYPHS)]}</div>
        <p class="kicker">PART {i + 1:02d}</p>
        <h4 style="margin:8px 0 6px;font-size:22px;font-weight:800">{_rich(t)}</h4>
        <p class="dim" style="font-size:14px;line-height:1.55">本部分提炼原文的关键观点。</p>
      </div>
            """
        )
    grid_cls = "grid g3" if len(cards) >= 3 else "grid g2"
    inner = f"""
    <span class="brand">fxt ppt</span>
    <p class="kicker mt-l">WHAT'S INSIDE</p>
    <h2 class="h2">分为 <span class="gradient-text">{len(cards)} 个功能</span></h2>
    <div class="{grid_cls} mt-l">{''.join(cards)}</div>
    {_footer(slide_no, total, "contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(f'<span class="pill pill-accent" style="margin-right:8px">{_esc(p)}</span>' for p in points[:4])
    inner = f"""
    <span class="brand" style="color:rgba(255,255,255,.85)">fxt ppt</span>
    <p class="kicker mt-l">CHAPTER · {chapter_no:02d}</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m">先建立结构，再展开重点。</p>
    <div class="mt-l">{pills}</div>
    {_footer(slide_no, total, f"section · {chapter_no:02d}")}
    """
    return _section(inner, title=title, extra_class="dark")


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cells.append(
            f"""
      <div class="feature-card">
        <div class="icon">{ICON_GLYPHS[i % len(ICON_GLYPHS)]}</div>
        <p class="kicker">POINT {i + 1:02d}</p>
        <h4 style="margin:8px 0 6px;font-size:22px;font-weight:800">{_rich(head or bullet)}</h4>
        <p class="dim" style="font-size:14px;line-height:1.55">{_rich(body if head else "来自原文的核心要点提炼。")}</p>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="feature-card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "grid g3" if n in {3, 6} else "grid g2"
    inner = f"""
    <span class="brand">fxt ppt</span>
    <p class="kicker mt-l">{_esc(slide.get("section") or "feature")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "核心特性")}</h2>
    <div class="{grid_cls} mt-l">{''.join(cells)}</div>
    {_footer(slide_no, total, "content · features")}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        rows.append(
            f"""
      <div class="step" style="margin-top:18px">
        <div class="n">{i + 1}</div>
        <div>
          <h4 style="margin:4px 0 6px;font-size:22px;font-weight:800">{_rich(head or f"步骤 {i + 1}")}</h4>
          <p class="dim" style="font-size:15px;line-height:1.55">{_rich(body if head else bullet)}</p>
        </div>
      </div>
            """
        )
    inner = f"""
    <span class="brand">fxt ppt</span>
    <p class="kicker mt-l">{_esc(slide.get("section") or "how it works")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "工作流程")}</h2>
    <div class="mt-l" style="max-width:980px">{''.join(rows)}</div>
    {_footer(slide_no, total, "content · steps")}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Ready when you are."
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。把这份内容带走，给团队看。"
    inner = f"""
    <div class="hero-shot"></div>
    <div style="position:relative;z-index:2;max-width:780px">
      <span class="brand" style="color:rgba(255,255,255,.85)">fxt ppt</span>
      <p class="kicker mt-l">END · LAUNCH</p>
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(message)}</p>
      <div class="mt-l"><a class="cta-btn">下载本期内容</a></div>
    </div>
    {_footer(slide_no, total, "end · launch")}
    """
    return _section(inner, title=str(title), extra_class="dark")


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


def render_product_launch(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "Product Launch 发布会")
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
<body class="tpl-product-launch">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_product_launch"]
