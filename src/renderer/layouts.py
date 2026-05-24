"""Shared helpers for html-ppt template renderers.

Every renderer in `src/renderer/<template>.py` repeats the same boilerplate:
- HTML escaping + minimal rich-text (** → emphasis, <br> passthrough)
- Parsing bullets shaped like ``"标题：正文"``
- Walking the generic slide list to plan cover/contents/section/closing
- Extracting structured fields (stat / quote / compare / kpis / steps / columns)
  from a slide, falling back to bullets when the LLM didn't emit them.

This module owns that shared logic so the per-template renderers can focus on
their visual identity. Nothing in here decides *how* a layout looks — that's
each renderer's job.
"""
from __future__ import annotations

import html
from typing import Any, Iterable


# ---------- text helpers ----------

def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def rich(value: Any, accent_tag: str = "em") -> str:
    """Minimal rich-text: ``**word**`` becomes <accent_tag>word</accent_tag>;
    ``<br>`` / ``<br/>`` survive intact. Everything else is HTML-escaped.
    """
    text = esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f"<{accent_tag}>{part}</{accent_tag}>")
        else:
            out.append(part)
    return "".join(out)


def rich_grad(value: Any) -> str:
    """Variant of rich() that wraps emphasis in ``<span class="gradient-text">``
    for templates whose visual identity is gradient-driven (pitch-deck,
    obsidian-claude-gradient, etc.)."""
    text = esc(value)
    text = text.replace("&lt;br&gt;", "<br>").replace("&lt;br/&gt;", "<br>")
    parts = text.split("**")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(f'<span class="gradient-text">{part}</span>')
        else:
            out.append(part)
    return "".join(out)


def deck_subtitle(generic: Any, fallback: str = "") -> str:
    """Return a content-derived eyebrow/sub-label for in-deck chrome.

    Uses the manuscript's subtitle when meaningful; otherwise falls back to the
    caller-provided string. Renderers use this to avoid leaking brand or
    template-id strings ("fxt ppt", "weekly-report") into the slides.
    """
    sub = ""
    if isinstance(generic, dict):
        sub = (generic.get("subtitle") or "").strip()
    return sub or fallback


def split_kv(bullet: str) -> tuple[str, str]:
    """Split ``"标题：正文"`` / ``"title: body"`` on either : or ：
    Returns (head, body); head is empty when no separator is present.
    """
    for sep in ("：", ":"):
        if sep in bullet:
            head, _, tail = bullet.partition(sep)
            head, tail = head.strip(), tail.strip()
            if head and tail:
                return head, tail
    return "", bullet.strip()


# ---------- planning ----------

def planned_slides(generic: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Walk a generic slide_json and return the ordered list of (kind, slide)
    tuples to render. Always emits a cover at position 0 and a closing at the
    end, synthesizing them if absent.

    `kind` is one of: "cover" / "contents" / "section" / "content" / "closing".
    """
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
        planned.append((stype or "content", slide))
    planned.append(("closing", closing or {}))
    return planned


def chapter_titles(generic: dict[str, Any]) -> list[str]:
    return [
        (s.get("title") or s.get("section") or "").strip()
        for s in (generic.get("slides") or [])
        if isinstance(s, dict) and s.get("type") == "section"
    ]


# ---------- structured-field extractors ----------

# Each extractor returns the structured data when the LLM provided it on the
# slide; otherwise it builds a best-effort fallback from `bullets` so every
# layout still renders something sensible.

def get_columns(slide: dict[str, Any], expected: int) -> list[dict[str, str]]:
    raw = slide.get("columns")
    if isinstance(raw, list) and raw:
        cols = [c for c in raw if isinstance(c, dict)]
        if cols:
            return [
                {
                    "title": str(c.get("title") or ""),
                    "body": str(c.get("body") or ""),
                    "kicker": str(c.get("kicker") or ""),
                }
                for c in cols[:expected]
            ]
    # Fallback: bullets[:expected]
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    cols: list[dict[str, str]] = []
    for b in bullets[:expected]:
        head, body = split_kv(b)
        cols.append({"title": head or b[:14], "body": body or b, "kicker": ""})
    while len(cols) < expected:
        cols.append({"title": f"维度 {len(cols) + 1}", "body": "", "kicker": ""})
    return cols


def get_kpis(slide: dict[str, Any], max_n: int = 4) -> list[dict[str, str]]:
    raw = slide.get("kpis")
    if isinstance(raw, list) and raw:
        items = []
        for k in raw[:max_n]:
            if not isinstance(k, dict):
                continue
            items.append({
                "label": str(k.get("label") or ""),
                "value": str(k.get("value") or ""),
                "delta": str(k.get("delta") or ""),
                "status": str(k.get("status") or ""),
            })
        if items:
            return items
    # Fallback: parse bullets — look for digits as the "value"
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    items: list[dict[str, str]] = []
    import re
    for b in bullets[:max_n]:
        head, body = split_kv(b)
        m = re.search(r"([+\-↑↓]?\s*[0-9][0-9.,]*\s*(?:%|pt|ms|s|x|×|倍|K|M|B)?)", body or b)
        value = m.group(1).strip() if m else (body[:6] if body else "—")
        items.append({
            "label": head or (b[:10] if b else "指标"),
            "value": value,
            "delta": "",
            "status": "",
        })
    while len(items) < max(2, min(max_n, 3)):
        items.append({"label": "—", "value": "—", "delta": "", "status": ""})
    return items[:max_n]


def get_stat(slide: dict[str, Any]) -> dict[str, str]:
    raw = slide.get("stat")
    if isinstance(raw, dict) and raw.get("value") is not None:
        return {
            "value": str(raw.get("value") or ""),
            "label": str(raw.get("label") or slide.get("title") or ""),
            "sub": str(raw.get("sub") or ""),
            "delta": str(raw.get("delta") or ""),
        }
    # Fallback: pull a number out of the first bullet
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    import re
    value = "—"
    label = slide.get("title") or ""
    sub = ""
    if bullets:
        head, body = split_kv(bullets[0])
        m = re.search(r"([+\-↑↓]?\s*[0-9][0-9.,]*\s*(?:%|pt|ms|s|x|×|倍|K|M|B)?)", body or bullets[0])
        if m:
            value = m.group(1).strip()
        label = head or label
        sub = body if head else (bullets[1] if len(bullets) > 1 else "")
    return {"value": value, "label": str(label or ""), "sub": str(sub or ""), "delta": ""}


def get_quote(slide: dict[str, Any]) -> dict[str, str]:
    raw = slide.get("quote")
    if isinstance(raw, dict) and raw.get("text"):
        return {"text": str(raw.get("text") or ""), "author": str(raw.get("author") or "")}
    # Fallback: first non-empty bullet as the quote, slide.notes as author
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str) and b.strip()]
    text = bullets[0] if bullets else (slide.get("title") or "")
    author = slide.get("notes") if not bullets else (bullets[1] if len(bullets) > 1 else "")
    return {"text": str(text or ""), "author": str(author or "")}


def get_compare(slide: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return {left:{title,points[]}, right:{title,points[]}}. Always normalized."""
    raw = slide.get("compare")
    if isinstance(raw, dict):
        out: dict[str, dict[str, Any]] = {}
        for side in ("left", "right"):
            obj = raw.get(side)
            if not isinstance(obj, dict):
                out[side] = {"title": "", "points": []}
                continue
            points = obj.get("points") or obj.get("bullets") or []
            if not isinstance(points, list):
                points = []
            out[side] = {
                "title": str(obj.get("title") or ""),
                "points": [str(p) for p in points if isinstance(p, str)],
            }
        if out["left"]["points"] or out["right"]["points"]:
            return out
    # Fallback: split bullets in half
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)]
    mid = max(1, len(bullets) // 2) if bullets else 0
    return {
        "left": {"title": slide.get("title") or "现状", "points": bullets[:mid]},
        "right": {"title": "对照", "points": bullets[mid:]},
    }


def get_steps(slide: dict[str, Any], max_n: int = 6) -> list[dict[str, str]]:
    raw = slide.get("steps")
    if isinstance(raw, list) and raw:
        items = []
        for s in raw[:max_n]:
            if not isinstance(s, dict):
                continue
            items.append({
                "when": str(s.get("when") or ""),
                "title": str(s.get("title") or ""),
                "body": str(s.get("body") or ""),
            })
        if items:
            return items
    # Fallback: bullets as steps
    bullets = [b for b in (slide.get("bullets") or []) if isinstance(b, str)][:max_n]
    items = []
    for i, b in enumerate(bullets):
        head, body = split_kv(b)
        items.append({"when": f"STEP {i + 1:02d}", "title": head or f"阶段 {i + 1}", "body": body or b})
    return items


def get_bullets(slide: dict[str, Any]) -> list[str]:
    return [b for b in (slide.get("bullets") or []) if isinstance(b, str)]


# ---------- layout normalization ----------

# Map deprecated / cross-template aliases to their canonical generic name so
# every renderer can dispatch on a small known set.
_LAYOUT_ALIASES = {
    "multi-card": "cards",
    "theory-cards": "cards",
    "method": "process-steps",
    "section-text": "bullets",
    "vs": "comparison",
    "swot": "comparison",
    "framework": "process-steps",
    "image-analysis": "cards",
    "chart-analysis": "kpi-grid",
    "quote-card": "big-quote",
}


def normalize_layout(layout: str | None, bullets_count: int) -> str:
    """Resolve a slide's `layout` to a canonical generic-layout name.

    When `layout` is missing, picks a default:
    - 2-4 bullets → "cards"
    - 5+ bullets → "bullets"
    - 0-1 bullet → "cards"
    """
    if layout:
        layout = _LAYOUT_ALIASES.get(layout, layout)
        if layout in {
            "cards", "bullets",
            "two-column", "three-column",
            "kpi-grid", "stat-highlight",
            "comparison", "pros-cons",
            "big-quote", "timeline", "process-steps",
        }:
            return layout
    if 2 <= bullets_count <= 4:
        return "cards"
    if bullets_count >= 5:
        return "bullets"
    return "cards"


# ---------- default HTML fragments ----------
#
# Each `inner_*` function returns the *inner HTML* of one content slide using
# `base.css` primitives (.card, .grid g3, .h2, .pill, .gradient-text). Per-
# template style.css files override the tokens (--accent, --surface, --grad,
# --text-1) and any layout-specific classes (kpi/vs/tl/steps/col/qs/sg/bl/cards)
# so the same fragments render in each template's visual identity.
#
# Renderers compose: their own chrome (brand, kicker, headline, section-num)
# then the inner fragment then their own footer. The fragments here include
# only the *body* of the slide (post-title), not the title itself.


def _grid_class(n: int) -> str:
    if n >= 4:
        return "grid g4"
    if n == 3:
        return "grid g3"
    return "grid g2"


def inner_cards(slide: dict[str, Any], *, accent_grad: bool = False) -> str:
    """Classic content cards. 2-4 cells in a grid."""
    bullets = get_bullets(slide)
    rich_fn = rich_grad if accent_grad else rich
    cells = []
    for i, bullet in enumerate(bullets[:6]):
        head, body = split_kv(bullet)
        body_html = (
            f'<p class="dim" style="font-size:15px;line-height:1.55;margin-top:6px">{rich(body)}</p>'
            if (head and body) else ""
        )
        cells.append(
            f'<div class="card"><span class="pill pill-accent">{i + 1:02d}</span>'
            f'<h4 style="margin:10px 0 0;font-size:22px;font-weight:800">'
            f"{rich_fn(head or bullet)}</h4>{body_html}</div>"
        )
    if not cells:
        cells.append(f'<div class="card"><h4>{rich(slide.get("title", ""))}</h4></div>')
    return f'<div class="{_grid_class(len(cells))} mt-l content-cards">{"".join(cells)}</div>'


def inner_bullets(slide: dict[str, Any]) -> str:
    """Plain numbered bullets list (no card grid)."""
    bullets = get_bullets(slide)
    rows = []
    for i, b in enumerate(bullets[:7]):
        rows.append(
            f'<div class="bl-row"><div class="ord">{i + 1:02d}</div>'
            f'<div class="txt">{rich(b)}</div></div>'
        )
    return f'<div class="mt-l content-bullets">{"".join(rows)}</div>'


def inner_columns(slide: dict[str, Any], n: int = 2) -> str:
    cols = get_columns(slide, n)
    blocks = []
    for c in cols:
        kicker = f'<p class="ckicker">{esc(c["kicker"])}</p>' if c.get("kicker") else ""
        blocks.append(
            f'<div class="col">{kicker}'
            f'<h4>{rich(c["title"])}</h4><p>{rich(c["body"])}</p></div>'
        )
    return f'<div class="content-cols cols-{n}" style="--n:{n}">{"".join(blocks)}</div>'


def inner_kpi_grid(slide: dict[str, Any]) -> str:
    kpis = get_kpis(slide, max_n=4)
    cells = []
    for k in kpis:
        cls = f"kpi {k['status']}".strip()
        delta = f'<div class="delta">{esc(k["delta"])}</div>' if k.get("delta") else ""
        cells.append(
            f'<div class="{cls}"><div class="lbl">{esc(k["label"])}</div>'
            f'<div class="val">{esc(k["value"])}</div>{delta}</div>'
        )
    n = len(cells)
    grid = "g4" if n == 4 else "g3" if n == 3 else "g2"
    return f'<div class="grid {grid} mt-l content-kpis">{"".join(cells)}</div>'


def inner_stat(slide: dict[str, Any]) -> str:
    st = get_stat(slide)
    delta = f'<div class="sg-delta">{esc(st["delta"])}</div>' if st.get("delta") else ""
    sub = f'<div class="sg-sub">{rich(st["sub"])}</div>' if st.get("sub") else ""
    return (
        '<div class="content-stat">'
        f'<div class="sg-val">{esc(st["value"])}</div>'
        f'<div class="sg-lbl">{rich(st["label"] or slide.get("title") or "")}</div>'
        f"{sub}{delta}</div>"
    )


def inner_comparison(slide: dict[str, Any], *, pros_cons: bool = False) -> str:
    cmp = get_compare(slide)
    left, right = cmp["left"], cmp["right"]
    left_lis = "".join(f"<li>{rich(p)}</li>" for p in left["points"][:6])
    right_lis = "".join(f"<li>{rich(p)}</li>" for p in right["points"][:6])
    if pros_cons:
        cls, mid = "content-vs pc", "✓/✗"
        l_tag, r_tag = "PROS", "CONS"
    else:
        cls, mid = "content-vs", "→"
        l_tag, r_tag = "BEFORE", "AFTER"
    return (
        f'<div class="{cls}">'
        f'<div class="vs-side left"><span class="vs-tag">{l_tag}</span>'
        f'<h3>{rich(left["title"])}</h3><ul>{left_lis}</ul></div>'
        f'<div class="vs-mid">{mid}</div>'
        f'<div class="vs-side right"><span class="vs-tag">{r_tag}</span>'
        f'<h3>{rich(right["title"])}</h3><ul>{right_lis}</ul></div>'
        "</div>"
    )


def inner_quote(slide: dict[str, Any]) -> str:
    q = get_quote(slide)
    author = f'<div class="qs-author">— {esc(q["author"])}</div>' if q.get("author") else ""
    return (
        '<div class="content-quote">'
        '<div class="qs-mark">"</div>'
        f'<blockquote class="qs-text">{rich(q["text"])}</blockquote>'
        f"{author}</div>"
    )


def inner_timeline(slide: dict[str, Any]) -> str:
    steps = get_steps(slide, max_n=6)
    n = max(len(steps), 3)
    items = []
    for s in steps:
        items.append(
            '<div class="tl-item">'
            f'<div class="tl-when">{esc(s["when"] or s["title"][:14])}</div>'
            '<div class="tl-dot"></div>'
            f'<h4>{rich(s["title"])}</h4>'
            f'<p>{rich(s["body"])}</p></div>'
        )
    return (
        '<div class="content-timeline">'
        f'<div class="tl-line"></div>'
        f'<div class="tl-row" style="--n:{n}">{"".join(items)}</div>'
        '</div>'
    )


def inner_process_steps(slide: dict[str, Any]) -> str:
    steps = get_steps(slide, max_n=4)
    n = max(len(steps), 2)
    items = []
    for i, s in enumerate(steps):
        items.append(
            f'<div class="ps-step" data-n="{i + 1:02d}">'
            f'<div class="ps-num">STEP {i + 1:02d}</div>'
            f'<h4>{rich(s["title"])}</h4>'
            f'<p>{rich(s["body"])}</p></div>'
        )
    return f'<div class="content-steps" style="--n:{n}">{"".join(items)}</div>'


def render_inner(layout: str, slide: dict[str, Any], *, accent_grad: bool = False) -> str:
    """Dispatch a single content slide to its inner-HTML fragment."""
    if layout == "kpi-grid":
        return inner_kpi_grid(slide)
    if layout == "stat-highlight":
        return inner_stat(slide)
    if layout == "comparison":
        return inner_comparison(slide, pros_cons=False)
    if layout == "pros-cons":
        return inner_comparison(slide, pros_cons=True)
    if layout == "big-quote":
        return inner_quote(slide)
    if layout == "timeline":
        return inner_timeline(slide)
    if layout == "process-steps":
        return inner_process_steps(slide)
    if layout == "two-column":
        return inner_columns(slide, 2)
    if layout == "three-column":
        return inner_columns(slide, 3)
    if layout == "bullets":
        return inner_bullets(slide)
    return inner_cards(slide, accent_grad=accent_grad)


__all__ = [
    "esc", "rich", "rich_grad", "split_kv", "deck_subtitle",
    "planned_slides", "chapter_titles",
    "get_columns", "get_kpis", "get_stat",
    "get_quote", "get_compare", "get_steps", "get_bullets",
    "normalize_layout",
    "inner_cards", "inner_bullets", "inner_columns",
    "inner_kpi_grid", "inner_stat", "inner_comparison",
    "inner_quote", "inner_timeline", "inner_process_steps",
    "render_inner",
]
