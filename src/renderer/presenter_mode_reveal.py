"""Render generic slide_json into the presenter-mode-reveal deck.

Visual language: light-themed presenter deck with structured rows —
agenda-row for contents, rule-row for chapters, feature-row for content
points, card-accent for highlights, code-block for steps, speaker chip.
Inherits base.css tokens; minimal overrides.
"""
from __future__ import annotations

import html
from typing import Any

ACCENT_COLORS = ["blue", "green", "orange", "purple", "red"]


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _rich(value: Any) -> str:
    text = _esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="accent">{part}</span>')
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


def _section(inner: str, *, active: bool = False, title: str = "", notes: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{_esc(title)}"' if title else ""
    data_notes = f' data-notes="{_esc(notes)}"' if notes else ""
    return f'<section class="{cls}"{data_title}{data_notes}>{inner}</section>'


def _footer(slide_no: int, total: int, label: str) -> str:
    return f'<div class="deck-footer mono"><span>{_esc(label)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or "auto-generated presenter deck"
    inner = f"""
      <p class="kicker">fxt-ppt :: presenter mode</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede">{_rich(subtitle)}</p>
      <div class="speaker"><div class="av"></div><div><b>fxt ppt</b><span>auto-generated · presenter mode</span></div></div>
      {_footer(slide_no, total, "cover")}
    """
    return _section(inner, active=active, title=str(title), notes="按 P 进入演讲者视图。")


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    rows = []
    for i, t in enumerate(chapters[:8]):
        rows.append(
            f"""
      <div class="agenda-row">
        <div class="num">{i + 1:02d}</div>
        <div class="t">{_rich(t)}</div>
        <div class="d">// auto-grouped</div>
      </div>
            """
        )
    inner = f"""
      <p class="kicker">agenda · {len(rows):02d}</p>
      <h2 class="h2">本次分享分为 {len(rows)} 个主题</h2>
      <div class="stack mt-l">{''.join(rows)}</div>
      {_footer(slide_no, total, "contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    rules = []
    for i, p in enumerate(points[:3]):
        color = ACCENT_COLORS[(chapter_no + i) % len(ACCENT_COLORS)]
        rules.append(
            f"""
      <div class="rule-row">
        <div class="num {color}">{i + 1:02d}</div>
        <div><b>{_rich(p)}</b><p class="dim">本节将围绕这一点展开。</p></div>
      </div>
            """
        )
    inner = f"""
      <p class="kicker">chapter · {chapter_no:02d}</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede mt-s">先建立结构，再展开重点。</p>
      <div class="mt-l">{''.join(rules)}</div>
      {_footer(slide_no, total, f"section · {chapter_no:02d}")}
    """
    return _section(inner, title=title, notes=f"Chapter {chapter_no}: {title}")


def _cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    rows = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        color = ACCENT_COLORS[i % len(ACCENT_COLORS)]
        rows.append(
            f"""
      <div class="feature-row">
        <div class="num {color}">{i + 1:02d}</div>
        <div><b>{_rich(head or bullet)}</b><p class="dim">{_rich(body if head else "")}</p></div>
      </div>
            """
        )
    if not rows:
        rows.append(f'<div class="feature-row"><b>{_rich(slide.get("title", ""))}</b></div>')
    inner = f"""
      <p class="kicker">{_esc(slide.get("section") or "content")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "核心要点")}</h2>
      <div class="card card-accent mt-l">{''.join(rows)}</div>
      {_footer(slide_no, total, "content · rows")}
    """
    notes = slide.get("notes") or slide.get("speaker_notes") or ""
    return _section(inner, title=str(slide.get("title") or "内容"), notes=str(notes))


def _steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    lines: list[str] = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = _split_kv(bullet)
        title_part = _rich(head or f"step {i + 1:02d}")
        body_part = _rich(body if head else bullet)
        lines.append(
            f'<span class="comment"># step {i + 1:02d}</span>\n'
            f'<span class="cmd">{title_part}</span> '
            f'<span class="flag">→</span> {body_part}'
        )
    code_inner = "\n\n".join(lines) or '<span class="comment"># no steps</span>'
    inner = f"""
      <p class="kicker">{_esc(slide.get("section") or "process")}</p>
      <h2 class="h2">{_rich(slide.get("title") or "过程")}</h2>
      <div class="code-block mt-l">{code_inner}</div>
      {_footer(slide_no, total, "content · code")}
    """
    notes = slide.get("notes") or slide.get("speaker_notes") or ""
    return _section(inner, title=str(slide.get("title") or "过程"), notes=str(notes))


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。按 P 切换演讲者视图。"
    inner = f"""
      <p class="kicker">end · presenter</p>
      <h1 class="h1">{_rich(title)}</h1>
      <p class="lede">{_rich(message)}</p>
      <div class="speaker mt-l"><div class="av"></div><div><b>fxt ppt</b><span>presenter-mode-reveal · auto-generated</span></div></div>
      {_footer(slide_no, total, "end")}
    """
    return _section(inner, title=str(title), notes=str(message))


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


def render_presenter_mode_reveal(generic: dict[str, Any]) -> str:
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
            title = slide.get("title") or f"Chapter {chapter_no}"
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

    title = _esc(generic.get("title") or "演讲者模式 Reveal")
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
<body class="tpl-presenter-mode-reveal">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_presenter_mode_reveal"]
