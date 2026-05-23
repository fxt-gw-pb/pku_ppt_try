"""Render generic slide_json into the testing-safety-alert deck.

Visual language: incident-style red/amber/green alert deck. Top/bottom
hazard stripes, alert-tag pills, alert-box callouts with status colors,
checklist rows with ok/fail boxes.
"""
from __future__ import annotations

import html
from typing import Any

ALERT_TONES = ["", "amber", "green"]  # default red
BOX_TONES = ["", "amber", "green"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="red">{part}</span>')
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


def _stripes() -> str:
    return '<div class="ts-stripe"></div><div class="ts-stripe-b"></div>'


def _chrome(left_tag: str, tone: str, slide_no: int, total: int) -> str:
    return f"""
    <div class="ts-chrome">
      <div class="ts-alert-tag {tone}">{_esc(left_tag)}</div>
      <div class="ts-page">{slide_no:02d} / {total:02d}</div>
    </div>
    """


def _footer(left: str, slide_no: int, total: int) -> str:
    return f'<div class="ts-footer"><span>{_esc(left)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "incident report"
    subtitle = generic.get("subtitle") or "auto-generated alert deck"
    inner = f"""
    {_stripes()}
    {_chrome("safety · alert", "", slide_no, total)}
    <div class="ts-kicker">fxt ppt · auto-generated</div>
    <h1 class="ts-h1">{_rich(title)}</h1>
    <p class="ts-sub">{_rich(subtitle)}</p>
    <div class="ts-alert-box" style="margin-top:28px">
      <h3>这是一份警示风格的内容报告</h3>
      <p>红色 = 风险与必须关注，琥珀 = 注意事项，绿色 = 已确认结论。</p>
    </div>
    {_footer("alert · cover", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, t in enumerate(chapters[:6]):
        tone = BOX_TONES[i % len(BOX_TONES)]
        cards.append(
            f"""
      <div class="ts-card">
        <div class="lbl">PART {i + 1:02d}</div>
        <h4>{_rich(t)}</h4>
        <p>本部分提炼原文的关键观点。</p>
      </div>
            """
        )
    grid_cls = "ts-grid-3" if len(cards) >= 3 else "ts-grid-2"
    inner = f"""
    {_stripes()}
    {_chrome("agenda", "amber", slide_no, total)}
    <div class="ts-kicker">agenda</div>
    <h2 class="ts-h2">本报告共 <span class="ts-highlight-red">{len(cards)}</span> 个部分</h2>
    <div class="{grid_cls}">{''.join(cards)}</div>
    {_footer("contents", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    tone = ALERT_TONES[chapter_no % len(ALERT_TONES)]
    box_tone = BOX_TONES[chapter_no % len(BOX_TONES)]
    pills = "".join(f'<span class="ts-highlight-amber" style="margin-right:8px">{_esc(p)}</span>' for p in points[:3])
    inner = f"""
    {_stripes()}
    {_chrome(f"part · {chapter_no:02d}", tone, slide_no, total)}
    <div class="ts-kicker">chapter · {chapter_no:02d}</div>
    <h1 class="ts-h1">{_rich(title)}</h1>
    <p class="ts-sub">先建立结构，再展开重点。</p>
    <div style="margin-top:18px">{pills}</div>
    <div class="ts-alert-box {box_tone}" style="margin-top:24px">
      <h3>section objective</h3>
      <p>在这一节，我们将逐条复盘 {_esc(title)}。</p>
    </div>
    {_footer(f"section · {chapter_no:02d}", slide_no, total)}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cells.append(
            f"""
      <div class="ts-card">
        <div class="lbl">FINDING {i + 1:02d}</div>
        <h4>{_rich(head or bullet)}</h4>
        <p>{_rich(body if head else "来自原文的核心要点提炼。")}</p>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="ts-card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "ts-grid-3" if n in {3, 6} else "ts-grid-2"
    tone = ALERT_TONES[slide_no % len(ALERT_TONES)]
    inner = f"""
    {_stripes()}
    {_chrome(slide.get("section") or "finding", tone, slide_no, total)}
    <div class="ts-kicker">findings</div>
    <h2 class="ts-h2">{_rich(slide.get("title") or "核心发现")}</h2>
    <div class="{grid_cls}">{''.join(cells)}</div>
    {_footer("content · cards", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        ok = i % 3 == 2  # mark every third item as ok for visual variety
        rows.append(
            f"""
      <div class="ts-check {"ok" if ok else ""}">
        <div class="box">{"✓" if ok else "!"}</div>
        <div class="txt">{_rich(head or f"step {i + 1}")}<br><span style="font-weight:400;color:var(--ts-ink2);font-size:14px">{_rich(body if head else bullet)}</span></div>
      </div>
            """
        )
    inner = f"""
    {_stripes()}
    {_chrome(slide.get("section") or "checklist", "amber", slide_no, total)}
    <div class="ts-kicker">runbook</div>
    <h2 class="ts-h2">{_rich(slide.get("title") or "处置清单")}</h2>
    <div class="ts-checklist">{''.join(rows)}</div>
    {_footer("content · runbook", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "incident closed"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。所有事项已闭环。"
    inner = f"""
    {_stripes()}
    {_chrome("resolved", "green", slide_no, total)}
    <div class="ts-kicker">end · resolved</div>
    <h1 class="ts-h1">{_rich(title)}</h1>
    <p class="ts-sub">{_rich(message)}</p>
    <div class="ts-alert-box green" style="margin-top:24px">
      <h3>credits</h3>
      <p>fxt ppt · testing-safety-alert · auto-generated</p>
    </div>
    {_footer("end · resolved", slide_no, total)}
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


def render_testing_safety_alert(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "红琥珀警示")
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
<body class="tpl-testing-safety-alert">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_testing_safety_alert"]
