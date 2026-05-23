"""Render generic slide_json into the tech-sharing deck.

Visual language: GitHub dark + green/blue/red accents, monospace kickers,
terminal-window code blocks, agenda rows with mono numbers. Reuses the
template's overridden card / pill / h1-h2 styles plus bespoke .terminal /
.agenda-row / .tag / .speaker.
"""
from __future__ import annotations

import html
from typing import Any


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


def _footer(left: str, slide_no: int, total: int) -> str:
    return f'<div class="deck-footer mono"><span>{_esc(left)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _terminal(bar: str, body: str) -> str:
    return f"""
    <div class="terminal">
      <div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span><span style="margin-left:8px">{_esc(bar)}</span></div>
      <pre>{body}</pre>
    </div>
    """


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "Generated deck · tech sharing edition"
    code_body = (
        '<span class="cmt"># run the auto-deck</span>\n'
        '<span class="kw">$</span> fxt-ppt run \\\n'
        '    --template <span class="str">"tech-sharing"</span> \\\n'
        '    --input <span class="str">"manuscript.md"</span>\n'
        '<span class="cmt"># deck materialized in &lt;1s</span>'
    )
    inner = f"""
      <p class="kicker">fxt-ppt :: auto-generated</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(subtitle)}</p>
      <div class="mt-l" style="max-width:760px">{_terminal('~/fxt-ppt $ ./run', code_body)}</div>
      <div class="speaker"><div class="av"></div><div><b>fxt ppt</b><span>template :: tech-sharing</span></div></div>
      {_footer("boot · cover", slide_no, total)}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:6]):
        rows.append(
            f"""
      <div class="agenda-row">
        <div class="num">{i + 1:02d}</div>
        <div class="t">{_rich(t)}</div>
        <div class="d">// 本部分提炼原文关键观点</div>
      </div>
            """
        )
    inner = f"""
      <p class="kicker">cat agenda.md</p>
      <h2 class="h2"># 目录 · {len(rows)} sections</h2>
      <div class="mt-l">{''.join(rows)}</div>
      {_footer("agenda", slide_no, total)}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    tags = "".join(f'<span class="tag">#{_esc(p)}</span>' for p in points[:4])
    inner = f"""
      <p class="kicker">chapter · {chapter_no:02d}</p>
      <h1 class="h1 mono" style="font-size:140px;background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">{chapter_no:02d}</h1>
      <h2 class="h2" style="margin-top:8px">{_rich(title)}</h2>
      <p class="lede mt-m">先建立结构，再展开重点。</p>
      <div class="mt-m" style="display:flex;flex-wrap:wrap;gap:8px">{tags}</div>
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
      <div class="card card-accent" style="padding:22px 26px">
        <span class="tag">{i + 1:02d}</span>
        <h4 style="margin:10px 0 6px;font-size:20px">{_rich(head or bullet)}</h4>
        <p class="lede" style="font-size:14px;line-height:1.6">{_rich(body if head else "来自原文的核心要点提炼。")}</p>
      </div>
            """
        )
    if not cells:
        cells.append(f'<div class="card"><h4>{_rich(slide.get("title", ""))}</h4></div>')
    n = len(cells)
    grid_cls = "grid g3" if n in {3, 6} else "grid g2"
    inner = f"""
      <p class="kicker">{_esc(slide.get("section") or "content")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "核心要点")}</h2>
      <div class="{grid_cls} mt-l">{''.join(cells)}</div>
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
            f'<span class="cmt"># step {i + 1:02d}</span>\n'
            f'<span class="kw">{title_part}</span>'
            f' <span class="num">→</span> {body_part}'
        )
    code_inner = "\n\n".join(lines) or '<span class="cmt"># no steps</span>'
    inner = f"""
      <p class="kicker">./pipeline</p>
      <h2 class="h2">{_rich(slide.get("title") or "过程拆解")}</h2>
      <div class="mt-l" style="max-width:980px">{_terminal('~/fxt-ppt $ ./pipeline.sh', code_inner)}</div>
      {_footer("content · pipeline", slide_no, total)}
    """
    return _section(inner, title=str(slide.get("title") or "过程"))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。session closed."
    inner = f"""
      <p class="kicker">exit 0</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-m">{_rich(message)}</p>
      <div class="mt-l">
        <span class="tag">fxt ppt</span>
        <span class="tag">tech-sharing</span>
        <span class="tag">auto-generated</span>
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


def render_tech_sharing(generic: dict[str, Any]) -> str:
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

    title = _esc(generic.get("title") or "Tech Sharing 技术分享")
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
<body class="tpl-tech-sharing">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_tech_sharing"]
