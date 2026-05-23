"""Render generic slide_json into the hermes-cyber-terminal deck.

Visual language: dark terminal chrome + neon green/cyan/amber, scanline
overlay, monospace headlines, code-block cards.
"""
from __future__ import annotations

import html
from typing import Any

TAG_COLORS = ["", "amber", "red", "", "amber"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="hl" style="color:var(--hc-green)">{part}</span>')
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


def _chrome_overlay() -> str:
    return (
        '<div class="hc-grid"></div>'
        '<div class="hc-vignette"></div>'
        '<div class="hc-scanlines"></div>'
    )


def _chrome_bar(left: str, right: str) -> str:
    return f"""
    <div class="hc-chrome">
      <div class="dots"><span></span><span></span><span></span></div>
      <div class="hc-prompt">{_esc(left)}</div>
      <div>{_esc(right)}</div>
    </div>
    """


def _footer(left: str, slide_no: int, total: int) -> str:
    return f"""
    <div class="hc-footer"><span>{_esc(left)}</span><span>{slide_no:03d} / {total:03d}</span></div>
    """


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Generated deck · cyber terminal edition"
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar("fxt-ppt run --template hermes-cyber-terminal", "session 01")}
    <div style="margin-top:60px">
      <div class="hc-tag">build · auto</div>
      <h1 class="hc-h1">{_rich(title)}<span class="hc-cursor"></span></h1>
      <p class="hc-lede">{_rich(subtitle)}</p>
      <div style="margin-top:22px">
        <span class="hc-tag">fxt ppt</span>
        <span class="hc-tag amber">template</span>
        <span class="hc-tag">classic mode</span>
      </div>
    </div>
    {_footer("boot · cover", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cells = []
    for i, t in enumerate(chapters[:6]):
        cells.append(
            f"""
      <div class="hc-card">
        <div class="lbl">PART {i + 1:02d}</div>
        <div class="val">{_rich(t)}</div>
      </div>
            """
        )
    grid_cls = "hc-grid-3" if len(cells) >= 3 else "hc-grid-2"
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar("cat contents.md", "module · index")}
    <div style="margin-top:30px">
      <h2 class="hc-h2"># 目录 · {len(cells)} sections</h2>
      <p class="hc-lede">scrolling through the table of contents.</p>
      <div class="{grid_cls}">{''.join(cells)}</div>
    </div>
    {_footer("contents", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    tags = "".join(
        f'<span class="hc-tag {TAG_COLORS[(chapter_no + j) % len(TAG_COLORS)]}">{_esc(p)}</span>'
        for j, p in enumerate(points[:4])
    )
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar(f"cd chapter_{chapter_no:02d}", f"chapter · {chapter_no:02d}")}
    <div style="margin-top:120px">
      <div class="hc-tag">chapter · {chapter_no:02d}</div>
      <div class="hc-big">{chapter_no:02d}</div>
      <h2 class="hc-h2" style="margin-top:8px">{_rich(title)}</h2>
      <p class="hc-lede">先建立结构，再展开重点。</p>
      <div style="margin-top:20px">{tags}</div>
    </div>
    {_footer(f"section · chapter_{chapter_no:02d}", slide_no, total)}
    """
    return _section(inner, title=title)


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        cells.append(
            f"""
      <div class="hc-card">
        <div class="lbl">{_rich(head or f"POINT {i + 1:02d}")}</div>
        <div class="val">{_rich(body or bullet)}</div>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="hc-card"><div class="val">{_rich(slide.get("title", ""))}</div></div>')
    n = len(cells)
    grid_cls = "hc-grid-3" if n in {3, 6} else "hc-grid-2"
    bar_left = f"cat {(slide.get('section') or 'content').lower().replace(' ', '_')}.md"
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar(bar_left, slide.get("section") or "content")}
    <div style="margin-top:20px">
      <h3 class="hc-h3">> {_rich(slide.get("title") or "核心要点")}</h3>
      <h2 class="hc-h2">{_rich(slide.get("title") or "核心要点")}</h2>
      <div class="{grid_cls}">{''.join(cells)}</div>
    </div>
    {_footer("content · cards", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    lines: list[str] = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        title_part = _rich(head or f"step {i + 1:02d}")
        body_part = _rich(body if head else bullet)
        lines.append(
            f'<div style="margin-top:6px"><span class="cm"># step {i + 1:02d}</span> '
            f'<span class="kw">{title_part}</span> '
            f'<span class="st">→</span> {body_part}</div>'
        )
    code_inner = "\n".join(lines) or '<span class="cm"># no steps</span>'
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar("./run_pipeline.sh", slide.get("section") or "pipeline")}
    <div style="margin-top:20px">
      <h2 class="hc-h2">{_rich(slide.get("title") or "过程拆解")}</h2>
      <p class="hc-lede">逐步执行；每一步可观察、可回滚。</p>
      <div class="hc-codebox" style="margin-top:18px">{code_inner}</div>
    </div>
    {_footer("content · pipeline", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "EXIT 0"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。session closed."
    inner = f"""
    {_chrome_overlay()}
    {_chrome_bar("./shutdown", "session · end")}
    <div style="margin-top:100px">
      <div class="hc-tag">return · 0</div>
      <div class="hc-big">{_rich(title)}</div>
      <p class="hc-lede" style="margin-top:18px">{_rich(message)}</p>
      <div style="margin-top:24px">
        <span class="hc-tag">fxt ppt</span>
        <span class="hc-tag amber">hermes-cyber-terminal</span>
        <span class="hc-tag">eof<span class="hc-cursor"></span></span>
      </div>
    </div>
    {_footer("end · eof", slide_no, total)}
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


def render_hermes_cyber_terminal(generic: dict[str, Any]) -> str:
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
            title = slide.get("title") or f"chapter {chapter_no}"
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

    title = _esc(generic.get("title") or "暗终端 Cyber")
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
<body class="tpl-hermes-cyber-terminal">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_hermes_cyber_terminal"]
