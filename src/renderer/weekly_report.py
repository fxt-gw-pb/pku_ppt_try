"""Render generic slide_json into the weekly-report deck.

Visual language: clean business report — blue/teal/amber accents on light
surface cards, KPI tiles with left status stripes, ship-item rows with
feat/fix/exp/infra tags, next-row task list.
"""
from __future__ import annotations

import html
from typing import Any

KPI_STATUS = ["good", "warn", "bad", ""]
SHIP_TAGS = ["feat", "fix", "exp", "infra"]


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


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _notes_aside(slide: dict[str, Any]) -> str:
    text = (slide.get("notes") or slide.get("speaker_notes") or "").strip()
    if not text:
        return ""
    return (
        '<div class="blocker" style="border-left-color:var(--accent);margin-top:18px">'
        '<h4 style="color:var(--accent)">讲者备注</h4>'
        f'<p>{_rich(text)}</p></div>'
    )


def _footer(left: str, slide_no: int, total: int) -> str:
    return f'<div class="deck-footer"><span>{_esc(left)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover_head() -> str:
    return (
        '<div class="cover-head">'
        '<div class="logo">fxt ppt</div>'
        '<div class="week-chip">auto · weekly</div>'
        '</div>'
    )


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "本周内容自动整理"
    inner = f"""
    {_cover_head()}
    <p class="kicker">WEEKLY · auto report</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m" style="max-width:880px">{_rich(subtitle)}</p>
    <div class="grid g3 mt-l">
      <div class="kpi"><div class="label">sections</div><div class="value">{max(1, len(generic.get("slides", [])) - 2)}</div><div class="delta flat">automated</div></div>
      <div class="kpi good"><div class="label">build</div><div class="value">OK</div><div class="delta up">↑ deck ready</div></div>
      <div class="kpi warn"><div class="label">review</div><div class="value">pending</div><div class="delta flat">→ human-in-loop</div></div>
    </div>
    {_footer("cover · weekly", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:8]):
        tag = SHIP_TAGS[i % len(SHIP_TAGS)]
        rows.append(
            f"""
      <div class="ship-item">
        <span class="tag {tag}">PART {i + 1:02d}</span>
        <div><b>{_rich(t)}</b></div>
        <span class="owner">@fxt-ppt</span>
      </div>
            """
        )
    inner = f"""
    {_cover_head()}
    <p class="kicker">agenda</p>
    <h2 class="h2">本期议程 · {len(rows)} sections</h2>
    <div class="mt-l">{''.join(rows)}</div>
    {_footer("agenda", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    kpis = []
    for i, p in enumerate(points[:3]):
        status = KPI_STATUS[i % len(KPI_STATUS)]
        cls = f"kpi {status}".strip()
        kpis.append(
            f"""
      <div class="{cls}">
        <div class="label">point {i + 1:02d}</div>
        <div class="value" style="font-size:22px;line-height:1.25">{_rich(p)}</div>
      </div>
            """
        )
    inner = f"""
    {_cover_head()}
    <p class="kicker">part · {chapter_no:02d}</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m">先建立结构，再展开重点。</p>
    <div class="grid g3 mt-l">{''.join(kpis)}</div>
    {_footer(f"section · chapter_{chapter_no:02d}", slide_no, total)}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        tag = SHIP_TAGS[i % len(SHIP_TAGS)]
        rows.append(
            f"""
      <div class="ship-item">
        <span class="tag {tag}">{_rich(head or f"item {i + 1:02d}")}</span>
        <div><b>{_rich(body or bullet)}</b></div>
        <span class="owner">{i + 1:02d}/{len(bullets):02d}</span>
      </div>
            """
        )
    if not rows:
        rows.append(f'<div class="ship-item"><span class="tag feat">item</span><div><b>{_rich(slide.get("title", ""))}</b></div></div>')
    n_items = max(len(bullets), 1)
    kpi_strip = f"""
    <div class="grid g3 mt-m" style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
      <div class="kpi good"><div class="label">items shipped</div><div class="value">{n_items:02d}</div><span class="delta up">▲ this week</span></div>
      <div class="kpi"><div class="label">slide</div><div class="value">{slide_no:02d}<span style="font-size:24px;color:var(--text-3)"> / {total:02d}</span></div><span class="delta flat">on track</span></div>
      <div class="kpi warn"><div class="label">section</div><div class="value" style="font-size:24px;line-height:1.2">{_esc((slide.get("section") or "core")[:14])}</div><span class="delta up">in scope</span></div>
    </div>
    """
    inner = f"""
    {_cover_head()}
    <p class="kicker">{_esc(slide.get("section") or "content")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "本周内容")}</h2>
    {kpi_strip}
    <div class="mt-l">{''.join(rows)}</div>
    {_notes_aside(slide)}
    {_footer("content · cards", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:8]):
        head, body = _split_kv(bullet)
        rows.append(
            f"""
      <div class="next-row">
        <div class="owner">step {i + 1:02d}</div>
        <div class="task"><b>{_rich(head or f"步骤 {i + 1}")}</b><span>{_rich(body if head else bullet)}</span></div>
      </div>
            """
        )
    inner = f"""
    {_cover_head()}
    <p class="kicker">{_esc(slide.get("section") or "next week")}</p>
    <h2 class="h2">{_rich(slide.get("title") or "下一步计划")}</h2>
    <div class="mt-l">{''.join(rows)}</div>
    {_notes_aside(slide)}
    {_footer("content · pipeline", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。"
    inner = f"""
    {_cover_head()}
    <p class="kicker">end · report</p>
    <h1 class="h1 mt-s">{_rich(title)}</h1>
    <p class="lede mt-m">{_rich(message)}</p>
    <div class="grid g3 mt-l">
      <div class="kpi good"><div class="label">deck</div><div class="value">READY</div><div class="delta up">automation OK</div></div>
      <div class="kpi"><div class="label">brand</div><div class="value">fxt ppt</div><div class="delta flat">weekly-report</div></div>
      <div class="kpi warn"><div class="label">credit</div><div class="value">AUTO</div><div class="delta flat">human-in-loop</div></div>
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


def render_weekly_report(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "Weekly Report 周报")
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
<body class="tpl-weekly-report">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_weekly_report"]
