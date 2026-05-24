"""Render generic slide_json into the xhs-post 3:4 portrait deck.

Visual language: peach cream background, hand-drawn boxes with offset shadows,
sticky-note stickers, large numbered circles, hashtag pills. One idea per
slide; lower density than 16:9 decks.
"""
from __future__ import annotations

import html
from typing import Any

from . import layouts as L

STICKER_COLORS = ["pink", "yellow", "blue", "green"]
ACCENTS = ["var(--accent)", "var(--accent-2)", "var(--accent-3)"]
ACCENT_TEXT = ["#fff", "#fff", "var(--text-1)"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="cover-title">{part}</span>')
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


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _page_dot(slide_no: int, total: int) -> str:
    return f'<div class="page-dot">{slide_no} / {total}</div>'


def _bottom(left: str, right: str) -> str:
    return (
        '<div class="bottom-bar">'
        f'<div><span class="avatar">f</span> <b style="color:var(--text-1);margin-left:8px">{_esc(left)}</b></div>'
        f'<div>{_esc(right)}</div>'
        '</div>'
    )


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "把文稿整理成 3:4 图文轮播"
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="sticker pink" style="top:130px;left:48px;transform:rotate(-6deg)">📝 fxt ppt</div>
    <div class="sticker yellow" style="top:150px;right:50px;transform:rotate(5deg)">自动生成</div>
    <div style="margin-top:220px">
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede" style="margin-top:24px">{_rich(subtitle)}</p>
    </div>
    {_bottom("@fxt-ppt", "← 左滑 查看")}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    items = []
    for i, t in enumerate(chapters[:6]):
        items.append(
            f"""
      <div class="hand-box" style="margin-bottom:18px">
        <b style="font-size:22px">PART {i + 1:02d} · {_rich(t)}</b>
      </div>
            """
        )
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="sticker blue" style="top:120px;right:50px;transform:rotate(4deg)">目录</div>
    <div style="margin-top:160px">
      <h2 class="h2">这份内容分为 <span class="cover-title">{len(items)} 段</span></h2>
      <div style="margin-top:30px">{''.join(items)}</div>
    </div>
    {_bottom("@fxt-ppt", "contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    sticker = STICKER_COLORS[chapter_no % len(STICKER_COLORS)]
    chips = "".join(f'<span class="ht">#{_esc(p)}</span>' for p in points[:3])
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="sticker {sticker}" style="top:120px;right:48px;transform:rotate(-3deg)">Part {chapter_no:02d}</div>
    <div style="margin-top:280px">
      <p class="lede" style="font-weight:700;color:var(--accent)">第 {chapter_no} 段</p>
      <h1 class="h1 mt-s">{_rich(title)}</h1>
      <div class="tag-row">{chips}</div>
    </div>
    {_bottom("@fxt-ppt", f"chapter {chapter_no:02d}")}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    items = []
    for i, bullet in enumerate(bullets[:4]):
        head, body = _split_kv(bullet)
        items.append(
            f"""
      <div class="hand-box" style="margin-bottom:18px">
        <b style="font-size:22px">{_rich(head or f"要点 {i + 1:02d}")}</b>
        <p class="lede" style="font-size:16px;margin-top:4px">{_rich(body if head else bullet)}</p>
      </div>
            """
        )
    if not items:
        items.append(f'<div class="hand-box"><b style="font-size:22px">{_rich(slide.get("title", ""))}</b></div>')
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="sticker yellow" style="top:120px;right:48px;transform:rotate(4deg)">{_esc(slide.get("section") or "干货")}</div>
    <div style="margin-top:180px">
      <h2 class="h2">{_rich(slide.get("title") or "核心要点")}</h2>
      <div style="margin-top:24px">{''.join(items)}</div>
    </div>
    {_bottom("@fxt-ppt", "content")}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:4]):
        head, body = _split_kv(bullet)
        bg = ACCENTS[i % len(ACCENTS)]
        color = ACCENT_TEXT[i % len(ACCENT_TEXT)]
        rows.append(
            f"""
      <div class="step-card">
        <div style="display:flex;align-items:center;gap:16px">
          <div class="num-circle" style="background:{bg};color:{color};width:54px;height:54px;font-size:26px">{i + 1}</div>
          <div>
            <h4>{_rich(head or f"步骤 {i + 1}")}</h4>
            <p>{_rich(body if head else bullet)}</p>
          </div>
        </div>
      </div>
            """
        )
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="sticker green" style="top:120px;right:48px;transform:rotate(-3deg)">step by step</div>
    <div style="margin-top:170px">
      <h2 class="h2">{_rich(slide.get("title") or "过程拆解")}</h2>
      <div style="margin-top:26px">{''.join(rows)}</div>
    </div>
    {_bottom("@fxt-ppt", "steps")}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "谢谢你看到这里"
    message = slide.get("notes") or slide.get("speaker_notes") or "如果觉得有用，欢迎点赞、收藏、转发给朋友 💌"
    inner = f"""
    {_page_dot(slide_no, total)}
    <div class="big-emoji" style="margin-top:120px">💌</div>
    <div style="margin-top:30px;text-align:center">
      <h2 class="h2">{_rich(title)}</h2>
      <p class="lede" style="margin-top:20px">{_rich(message)}</p>
      <div class="tag-row" style="justify-content:center;margin-top:30px">
        <span class="ht">#fxtppt</span>
        <span class="ht">#自动生成</span>
        <span class="ht">#xhs-post</span>
      </div>
    </div>
    {_bottom("@fxt-ppt", "end ♡")}
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


def render_xhs_post(generic: dict[str, Any]) -> str:
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
            layout = L.normalize_layout(slide.get("layout"), len(L.get_bullets(slide)))
            if layout == "cards":
                sections.append(_cards(slide, idx, total))
            elif layout == "bullets":
                sections.append(_steps(slide, idx, total))
            else:
                body = L.render_inner(layout, slide)
                inner = f"""
    {_page_dot(idx, total)}
    <div class="sticker pink" style="top:130px;left:46px;transform:rotate(-4deg)">{_esc(slide.get("section") or "")}</div>
    <div style="margin-top:160px">
      <h2 class="h2">{_rich(slide.get("title") or "")}</h2>
      {body}
    </div>
    {_bottom("@fxt-ppt", f"content · {layout}")}
    """
                sections.append(_section(inner, title=str(slide.get("title") or "")))

    title = _esc(generic.get("title") or "小红书 3:4 图文")
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
<body class="tpl-xhs-post">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_xhs_post"]
