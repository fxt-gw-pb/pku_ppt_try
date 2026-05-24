"""Render generic slide_json into the pitch-deck deck.

Visual language: classic YC/VC pitch — white background with soft blue-purple
gradient washes, mega numbers, KPI cards with colored stripes, VS panels,
serif pull quotes, gradient-dot timelines, numbered step cards.

Content-page layouts honored:
- cards / bullets (default fallbacks)
- two-column / three-column
- kpi-grid
- stat-highlight
- comparison / pros-cons (rendered through VS panel with different accents)
- big-quote
- timeline
- process-steps
"""
from __future__ import annotations

from typing import Any

from . import layouts as L


# ---------- shared chrome ----------

def _brand(label: str = "") -> str:
    text = f'<span class="brand">{L.esc(label)}</span>' if label else ""
    return f'<div><span class="brand-dot"></span>{text}</div>'


def _section(inner: str, *, active: bool = False, title: str = "") -> str:
    cls = "slide is-active" if active else "slide"
    data_title = f' data-title="{L.esc(title)}"' if title else ""
    return f'<section class="{cls}"{data_title}>{inner}</section>'


def _footer(slide_no: int, total: int, tag: str) -> str:
    return f'<div class="deck-footer"><span>{L.esc(tag)}</span><span>{slide_no:02d} / {total:02d}</span></div>'


# ---------- cover / contents / divider / closing ----------

def _cover(generic: dict[str, Any], slide_no: int, total: int, active: bool) -> str:
    title = generic.get("title") or "未命名内容"
    subtitle = generic.get("subtitle") or ""
    section_count = max(1, len(generic.get("slides", [])) - 2)
    inner = f"""
    <div class="cover-bg"></div><div class="cover-blob"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:38px">
      {_brand()}
      <span class="num-tag">{section_count:02d} SECTIONS</span>
    </div>
    <h1 class="h1 mt-s">{L.rich_grad(title)}</h1>
    <p class="lede mt-m" style="max-width:900px">{L.rich_grad(subtitle)}</p>
    {_footer(slide_no, total, "cover")}
    """
    return _section(inner, active=active, title=str(title))


def _contents(chapters: list[str], slide_no: int, total: int) -> str:
    cards = []
    for i, t in enumerate(chapters[:6]):
        cards.append(f"""
      <div class="card" style="padding:26px 28px">
        <span class="num-tag">PART {i + 1:02d}</span>
        <h4 style="margin:10px 0 6px;font-size:22px;font-weight:800">{L.rich_grad(t)}</h4>
      </div>""")
    grid_cls = "grid g3" if len(cards) >= 3 else "grid g2"
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">CONTENTS</p>
    <h2 class="h2">这份 pitch 分为 <span class="gradient-text">{len(cards)} 段</span></h2>
    <div class="{grid_cls} mt-l">{''.join(cards)}</div>
    {_footer(slide_no, total, "contents")}
    """
    return _section(inner, title="目录")


def _divider(title: str, points: list[str], chapter_no: int, slide_no: int, total: int) -> str:
    pills = "".join(
        f'<span class="pill pill-accent" style="margin-right:8px">{L.esc(p)}</span>'
        for p in points[:4]
    )
    inner = f"""
    <div class="section-num">{chapter_no:02d}</div>
    {_brand()}
    <p class="kicker mt-l">PART · {chapter_no:02d}</p>
    <h1 class="h1 mt-s">{L.rich_grad(title)}</h1>
    <p class="lede mt-m" style="max-width:900px">先建立结构，再展开重点。</p>
    <div class="mt-l">{pills}</div>
    {_footer(slide_no, total, f"section · {chapter_no:02d}")}
    """
    return _section(inner, title=title)


def _closing(slide: dict[str, Any], slide_no: int, total: int) -> str:
    title = slide.get("title") or "Thanks"
    message = slide.get("notes") or slide.get("speaker_notes") or "感谢你看到这里。期待和你的下一次对话。"
    inner = f"""
    {_brand()}
    <div class="ask-box mt-l">
      <p class="kicker" style="color:#fff">THE ASK</p>
      <h2 class="h2 mt-s">{L.rich(title)}</h2>
      <p class="dim mt-m" style="font-size:18px">{L.rich(message)}</p>
    </div>
    {_footer(slide_no, total, "end · ask")}
    """
    return _section(inner, title=str(title))


# ---------- shared content-page header ----------

def _content_header(slide: dict[str, Any], slide_no: int) -> str:
    return f"""
    {_brand()}
    <div class="section-num">{slide_no:02d}</div>
    <p class="kicker mt-l">{L.esc(slide.get("section") or "content")}</p>
    <h2 class="h2">{L.rich_grad(slide.get("title") or "")}</h2>
    """


# ---------- content layouts ----------

def _layout_cards(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = L.get_bullets(slide)
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = L.split_kv(bullet)
        body_html = (
            f'<p class="dim" style="font-size:15px;line-height:1.55">{L.rich(body)}</p>'
            if (head and body) else ""
        )
        cells.append(f"""
      <div class="card" style="padding:28px 32px">
        <span class="num-tag">{i + 1:02d}</span>
        <h4 style="margin:10px 0 8px;font-size:22px;font-weight:800">{L.rich_grad(head or bullet)}</h4>
        {body_html}
      </div>""")
    if not cells:
        cells.append(f'<div class="card"><h4>{L.rich(slide.get("title", ""))}</h4></div>')
    grid_cls = "grid g3" if len(cells) in {3, 6} else "grid g2"
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="{grid_cls} mt-l">{''.join(cells)}</div>
    {_footer(slide_no, total, "content · cards")}
    """
    return _section(inner, title=str(slide.get("title") or "内容"))


def _layout_bullets(slide: dict[str, Any], slide_no: int, total: int) -> str:
    bullets = L.get_bullets(slide)
    rows = []
    for i, b in enumerate(bullets[:7]):
        rows.append(
            f'<div class="row"><div class="ord">{i + 1:02d}</div>'
            f'<div class="txt">{L.rich_grad(b)}</div></div>'
        )
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="bullets-list">{''.join(rows)}</div>
    {_footer(slide_no, total, "content · bullets")}
    """
    return _section(inner, title=str(slide.get("title") or "要点"))


def _layout_columns(slide: dict[str, Any], slide_no: int, total: int, n: int) -> str:
    cols = L.get_columns(slide, n)
    blocks = []
    for c in cols:
        kicker = f'<p class="ckicker">{L.esc(c["kicker"])}</p>' if c.get("kicker") else ""
        blocks.append(f"""
      <div class="col">
        {kicker}
        <h4>{L.rich_grad(c["title"])}</h4>
        <p>{L.rich(c["body"])}</p>
      </div>""")
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="col-wrap" style="--n:{n}">{''.join(blocks)}</div>
    {_footer(slide_no, total, f"content · {n}-col")}
    """
    return _section(inner, title=str(slide.get("title") or ""))


def _layout_kpi_grid(slide: dict[str, Any], slide_no: int, total: int) -> str:
    kpis = L.get_kpis(slide, max_n=4)
    cells = []
    for k in kpis:
        cls = f"kpi-card {k['status']}".strip()
        delta = f'<div class="delta">{L.esc(k["delta"])}</div>' if k.get("delta") else ""
        cells.append(f"""
      <div class="{cls}">
        <div class="lbl">{L.esc(k["label"])}</div>
        <div class="val">{L.esc(k["value"])}</div>
        {delta}
      </div>""")
    grid_cls = "grid g4" if len(kpis) == 4 else "grid g3" if len(kpis) == 3 else "grid g2"
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="{grid_cls} mt-l">{''.join(cells)}</div>
    {_footer(slide_no, total, "content · KPI")}
    """
    return _section(inner, title=str(slide.get("title") or "指标"))


def _layout_stat(slide: dict[str, Any], slide_no: int, total: int) -> str:
    stat = L.get_stat(slide)
    delta = f'<div class="delta">{L.esc(stat["delta"])}</div>' if stat.get("delta") else ""
    sub = f'<div class="sub">{L.rich(stat["sub"])}</div>' if stat.get("sub") else ""
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">{L.esc(slide.get("section") or "impact")}</p>
    <div class="stat-stage">
      <div class="num">{L.esc(stat["value"])}</div>
      <div class="lbl">{L.rich(stat["label"] or slide.get("title") or "")}</div>
      {sub}
      {delta}
    </div>
    {_footer(slide_no, total, "content · stat")}
    """
    return _section(inner, title=str(slide.get("title") or "数字"))


def _layout_comparison(slide: dict[str, Any], slide_no: int, total: int, *, pros_cons: bool = False) -> str:
    cmp = L.get_compare(slide)
    left, right = cmp["left"], cmp["right"]
    left_lis = "".join(f"<li>{L.rich(p)}</li>" for p in left["points"][:6])
    right_lis = "".join(f"<li>{L.rich(p)}</li>" for p in right["points"][:6])
    if pros_cons:
        left_kicker = '<span class="kicker-tag">PROS</span>'
        right_kicker = '<span class="kicker-tag">CONS</span>'
        wrap_cls = "vs-wrap pc"
        mid = "✓ / ✗"
    else:
        left_kicker = '<span class="kicker-tag">BEFORE</span>'
        right_kicker = '<span class="kicker-tag">AFTER</span>'
        wrap_cls = "vs-wrap"
        mid = "→"
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="{wrap_cls}">
      <div class="card side left">
        <h3>{left_kicker}{L.rich(left["title"])}</h3>
        <ul>{left_lis}</ul>
      </div>
      <div class="mid">{mid}</div>
      <div class="card side right">
        <h3>{right_kicker}{L.rich(right["title"])}</h3>
        <ul>{right_lis}</ul>
      </div>
    </div>
    {_footer(slide_no, total, "content · " + ("pros-cons" if pros_cons else "compare"))}
    """
    return _section(inner, title=str(slide.get("title") or "对比"))


def _layout_quote(slide: dict[str, Any], slide_no: int, total: int) -> str:
    q = L.get_quote(slide)
    author = f'<div class="author">— {L.esc(q["author"])}</div>' if q.get("author") else ""
    inner = f"""
    {_brand()}
    <p class="kicker mt-l">{L.esc(slide.get("section") or "quote")}</p>
    <div class="quote-stage">
      <div class="qmark">"</div>
      <blockquote>{L.rich_grad(q["text"])}</blockquote>
      {author}
    </div>
    {_footer(slide_no, total, "content · quote")}
    """
    return _section(inner, title=str(slide.get("title") or "Quote"))


def _layout_timeline(slide: dict[str, Any], slide_no: int, total: int) -> str:
    steps = L.get_steps(slide, max_n=6)
    n = max(len(steps), 3)
    items = []
    for s in steps:
        items.append(f"""
      <div class="tl-item">
        <div class="when">{L.esc(s["when"] or s["title"][:14])}</div>
        <div class="dot"></div>
        <h4>{L.rich(s["title"])}</h4>
        <p>{L.rich(s["body"])}</p>
      </div>""")
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="tl-wrap"><div class="tl-row" style="--n:{n}">{''.join(items)}</div></div>
    {_footer(slide_no, total, "content · timeline")}
    """
    return _section(inner, title=str(slide.get("title") or "时间线"))


def _layout_process_steps(slide: dict[str, Any], slide_no: int, total: int) -> str:
    steps = L.get_steps(slide, max_n=4)
    n = max(len(steps), 2)
    items = []
    for i, s in enumerate(steps):
        items.append(f"""
      <div class="step" data-n="{i + 1:02d}">
        <div class="num">STEP {i + 1:02d}</div>
        <h4>{L.rich(s["title"])}</h4>
        <p>{L.rich(s["body"])}</p>
      </div>""")
    inner = f"""
    {_content_header(slide, slide_no)}
    <div class="steps-wrap" style="--n:{n}">{''.join(items)}</div>
    {_footer(slide_no, total, "content · process")}
    """
    return _section(inner, title=str(slide.get("title") or "流程"))


# ---------- main entry ----------

def render_pitch_deck(generic: dict[str, Any]) -> str:
    planned = L.planned_slides(generic)
    total = len(planned)
    chapters = L.chapter_titles(generic)
    sections: list[str] = []
    chapter_no = 0
    for idx, (kind, slide) in enumerate(planned, start=1):
        active = idx == 1
        if kind == "cover":
            sections.append(_cover(generic, idx, total, active))
            continue
        if kind == "contents":
            sections.append(_contents(chapters, idx, total))
            continue
        if kind == "section":
            chapter_no += 1
            title = slide.get("title") or f"Part {chapter_no}"
            points = L.get_bullets(slide)
            sections.append(_divider(title, points, chapter_no, idx, total))
            continue
        if kind == "closing":
            sections.append(_closing(slide, idx, total))
            continue
        # content
        layout = L.normalize_layout(slide.get("layout"), len(L.get_bullets(slide)))
        if layout == "kpi-grid":
            sections.append(_layout_kpi_grid(slide, idx, total))
        elif layout == "stat-highlight":
            sections.append(_layout_stat(slide, idx, total))
        elif layout == "comparison":
            sections.append(_layout_comparison(slide, idx, total, pros_cons=False))
        elif layout == "pros-cons":
            sections.append(_layout_comparison(slide, idx, total, pros_cons=True))
        elif layout == "big-quote":
            sections.append(_layout_quote(slide, idx, total))
        elif layout == "timeline":
            sections.append(_layout_timeline(slide, idx, total))
        elif layout == "process-steps":
            sections.append(_layout_process_steps(slide, idx, total))
        elif layout == "two-column":
            sections.append(_layout_columns(slide, idx, total, 2))
        elif layout == "three-column":
            sections.append(_layout_columns(slide, idx, total, 3))
        elif layout == "bullets":
            sections.append(_layout_bullets(slide, idx, total))
        else:
            sections.append(_layout_cards(slide, idx, total))

    title = L.esc(generic.get("title") or "Pitch Deck 路演")
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
<body class="tpl-pitch-deck">
<div class="deck">
{''.join(sections)}
</div>
<script src="assets/runtime.js"></script>
</body>
</html>
"""


__all__ = ["render_pitch_deck"]
