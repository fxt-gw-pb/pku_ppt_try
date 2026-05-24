"""Compile a generic slide_json (produced by the LLM) into a PKU `slides.json`
that the HTML template's `runtime.js` renderer can consume.

The contract between LLM output and PPT skill is intentionally narrow:
  - LLM produces semantic content (cover / contents / section / content / closing)
    with bullets, optional `layout`, and optional structured fields
    (stat / quote / compare / kpis / steps / columns).
  - This compiler decides the concrete PKU layout per slide, assigns
    `chapterIndex` consistently, and fills in PKU-shaped fields
    (`headline`, `cards`, `blocks`, `nodes`, `leftItems`, `methods`, ...).

PKU `runtime.js` ships 14 layouts (cover, contents, section-divider,
image-analysis, chart-analysis, timeline, theory-cards, multi-card, framework,
vs, swot, method, section-text, closing). We route the LLM's generic-layout
names to the closest PKU layout and feed it the structured data when present,
otherwise we fall back to bullets-only heuristics.
"""
from __future__ import annotations

import copy
from typing import Any

from . import layouts as L

DEFAULT_CHAPTERS = [
    {"title": "背景和意义", "subtitle": "Background & Significance"},
    {"title": "综述和评述", "subtitle": "Literature Review"},
    {"title": "思路和内容", "subtitle": "Approach & Content"},
    {"title": "过程和方法", "subtitle": "Process & Method"},
    {"title": "成果与展望", "subtitle": "Results & Outlook"},
]

DEFAULT_META = {
    "title": "",
    "subtitle": "GRADUATION DEFENSE / OPENING REPORT",
    "date": "",
    "motto": "爱国 · 进步 · 民主 · 科学",
    "logo": "assets/media/pku-logo.png",
}

# Map the generic LLM-facing layout name to the concrete PKU layout we'll emit.
# When the LLM gives a name that's already a PKU layout we keep it as-is.
_GENERIC_TO_PKU = {
    "cards": "multi-card",
    "bullets": "section-text",
    "two-column": "multi-card",
    "three-column": "multi-card",
    "kpi-grid": "multi-card",       # rendered as value-led cards
    "stat-highlight": "section-text",  # value as first block with big formatting hint
    "comparison": "vs",
    "pros-cons": "vs",
    "big-quote": "section-text",    # single quote block, serif/italic via class
    "timeline": "timeline",
    "process-steps": "method",
    "quote-card": "section-text",
}


# ---------- bullet-driven card builders (legacy) ----------

def _as_cards_from_bullets(bullets: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = L.split_kv(b)
        out.append({
            "title": head or f"要点 {i + 1}",
            "body": body or b,
            "tag": f"{i + 1:02d}",
        })
    return out


def _as_method_cards_from_bullets(bullets: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = L.split_kv(b)
        out.append({
            "title": head or f"方法 {i + 1}",
            "en": f"METHOD {chr(64 + i + 1)}",
            "body": body or b,
        })
    return out


def _as_blocks_from_bullets(bullets: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = L.split_kv(b)
        out.append({
            "label": head or f"要点 {i + 1:02d}",
            "text": body or b,
        })
    return out


def _as_steps_from_bullets(bullets: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = L.split_kv(b)
        out.append({
            "label": f"S{i + 1}",
            "title": head or f"阶段 {i + 1}",
            "body": body or b,
        })
    return out


# ---------- structured-field → PKU shape ----------

def _kpi_cards(slide: dict[str, Any]) -> list[dict[str, str]]:
    """Convert KPI list to PKU multi-card cards with value-led body."""
    kpis = L.get_kpis(slide, max_n=4)
    out = []
    for i, k in enumerate(kpis):
        # Lead the body with the value (**bold** triggers PKU red emphasis in rich text).
        body_parts = [f"**{k['value']}**"]
        if k.get("delta"):
            body_parts.append(k["delta"])
        body = "<br>".join(body_parts)
        out.append({
            "title": k["label"] or f"指标 {i + 1}",
            "body": body,
            "tag": f"{i + 1:02d}",
        })
    return out


def _theory_cards_from_columns(slide: dict[str, Any], n: int) -> list[dict[str, str]]:
    """Convert columns to PKU theory-cards style cards."""
    cols = L.get_columns(slide, n)
    out = []
    for i, c in enumerate(cols):
        out.append({
            "title": c["title"] or f"维度 {i + 1}",
            "body": c["body"],
            "tag": f"{i + 1:02d}",
        })
    return out


def _vs_from_compare(slide: dict[str, Any], pros_cons: bool) -> dict[str, Any]:
    cmp = L.get_compare(slide)
    left, right = cmp["left"], cmp["right"]
    left_items = [{"body": p} for p in left["points"][:6]]
    right_items = [{"body": p} for p in right["points"][:6]]
    if pros_cons:
        left_kicker, right_kicker = "PROS · 优势", "CONS · 局限"
    else:
        left_kicker, right_kicker = "BEFORE · 现状", "AFTER · 改进"
    return {
        "leftKicker": left_kicker,
        "leftTitle": left["title"] or ("我们的优势" if pros_cons else "现状"),
        "leftItems": left_items,
        "rightKicker": right_kicker,
        "rightTitle": right["title"] or ("仍存局限" if pros_cons else "改进后"),
        "rightItems": right_items,
    }


def _method_from_steps(slide: dict[str, Any]) -> list[dict[str, str]]:
    steps = L.get_steps(slide, max_n=4)
    out = []
    for i, s in enumerate(steps):
        out.append({
            "title": s["title"] or f"方法 {i + 1}",
            "en": s.get("when") or f"METHOD {chr(64 + i + 1)}",
            "body": s.get("body") or "",
        })
    return out


def _timeline_from_steps(slide: dict[str, Any]) -> list[dict[str, str]]:
    steps = L.get_steps(slide, max_n=6)
    out = []
    for i, s in enumerate(steps):
        label = s.get("when") or f"S{i + 1}"
        out.append({
            "label": label,
            "title": s["title"] or f"阶段 {i + 1}",
            "body": s.get("body") or "",
        })
    return out


def _quote_blocks(slide: dict[str, Any]) -> list[dict[str, str]]:
    q = L.get_quote(slide)
    blocks = [{
        "label": "引述",
        "text": f"**{q['text']}**",
    }]
    if q.get("author"):
        blocks.append({"label": "出处", "text": q["author"]})
    return blocks


def _stat_blocks(slide: dict[str, Any]) -> list[dict[str, str]] | None:
    """Return PKU section-text blocks for a stat slide, or None when the LLM
    didn't supply a real numeric value. Callers must downgrade to bullet
    blocks rather than fabricate a `—` stat."""
    st = L.get_stat(slide)
    if not st:
        return None
    blocks = [{
        "label": st["label"] or "关键数字",
        "text": f"**{st['value']}**" + (f"<br>{st['sub']}" if st.get("sub") else ""),
    }]
    if st.get("delta"):
        blocks.append({"label": "对比基线", "text": st["delta"]})
    # Also pull the rest of bullets in case the LLM gave extra context.
    for b in L.get_bullets(slide)[1:4]:
        head, body = L.split_kv(b)
        blocks.append({"label": head or "—", "text": body or b})
    return blocks


# ---------- per-slide compiler ----------

def _resolve_pku_layout(slide: dict[str, Any]) -> str:
    """Pick the concrete PKU layout for a content slide."""
    hint = slide.get("layout")
    if hint:
        # If it's already a PKU layout name, use it directly.
        if hint in {
            "multi-card", "theory-cards", "method", "timeline", "section-text",
            "vs", "swot", "framework", "image-analysis", "chart-analysis",
        }:
            return hint
        # Else translate the generic name.
        if hint in _GENERIC_TO_PKU:
            return _GENERIC_TO_PKU[hint]
    # No hint → bullet-count heuristic.
    n = len(L.get_bullets(slide))
    if 2 <= n <= 4:
        return "multi-card"
    return "section-text"


def _render_content(
    slide: dict[str, Any], chapter_idx: int, section_title: str
) -> dict[str, Any]:
    bullets = L.get_bullets(slide)
    layout = _resolve_pku_layout(slide)
    hint = slide.get("layout") or ""
    base: dict[str, Any] = {
        "layout": layout,
        "chapterIndex": chapter_idx,
        "sectionTitle": section_title or slide.get("title", ""),
        "sectionTitleEn": "",
        "headline": slide.get("title", ""),
    }

    if layout == "multi-card":
        # Route based on what the LLM actually emitted.
        # kpi-grid requires real numeric KPIs; if not present, fall through
        # to bullet-driven cards rather than fabricate numeric "values".
        kpi_cards = _kpi_cards(slide) if (hint == "kpi-grid" or slide.get("kpis")) else []
        if kpi_cards:
            base["cards"] = kpi_cards
            base["cols"] = min(max(len(base["cards"]), 2), 4)
        elif hint in {"two-column"} or (slide.get("columns") and not slide.get("kpis")):
            base["cards"] = _theory_cards_from_columns(slide, 2 if hint == "two-column" else (3 if hint == "three-column" else len(slide.get("columns") or [])))
            base["cols"] = 2 if hint == "two-column" else min(max(len(base["cards"]), 2), 4)
        elif hint == "three-column":
            base["cards"] = _theory_cards_from_columns(slide, 3)
            base["cols"] = 3
        else:
            base["cards"] = _as_cards_from_bullets(bullets) or [
                {"title": slide.get("title", "要点"), "body": ""}
            ]
            base["cols"] = min(max(len(bullets), 2), 4)

    elif layout == "theory-cards":
        base["cards"] = [
            {"title": c["title"], "label": c["tag"], "body": c["body"]}
            for c in _as_cards_from_bullets(bullets)
        ] or [{"title": slide.get("title", "要点"), "body": ""}]

    elif layout == "method":
        if slide.get("steps"):
            base["methods"] = _method_from_steps(slide)
        else:
            base["methods"] = _as_method_cards_from_bullets(bullets)
        if not base["methods"]:
            base["methods"] = [{"title": slide.get("title", "方法"), "en": "METHOD", "body": ""}]
        base["cols"] = min(max(len(base["methods"]), 2), 4)

    elif layout == "timeline":
        if slide.get("steps"):
            base["steps"] = _timeline_from_steps(slide)
        else:
            base["steps"] = _as_steps_from_bullets(bullets)
        if not base["steps"]:
            base["steps"] = [{"label": "S1", "title": slide.get("title", "阶段"), "body": ""}]

    elif layout == "vs":
        base.update(_vs_from_compare(slide, pros_cons=(hint == "pros-cons")))

    elif layout == "swot":
        cmp = L.get_compare(slide)
        base["strengths"] = cmp["left"]["points"][:4] or []
        base["weaknesses"] = cmp["right"]["points"][:4] or []
        base["opportunities"] = []
        base["threats"] = []

    elif layout == "framework":
        steps = L.get_steps(slide, max_n=5)
        if not steps:
            steps = [
                {"title": h or b, "body": body, "when": ""}
                for b in bullets
                for h, body in [L.split_kv(b)]
            ]
        base["nodes"] = [
            {"title": s["title"], "body": s.get("body") or "", "primary": (i == 0)}
            for i, s in enumerate(steps)
        ]

    elif layout in {"image-analysis", "chart-analysis"}:
        # PKU's image-analysis / chart-analysis layouts expect images/headline +
        # paragraph body. Without real image assets we fall through to a
        # section-text shape so the deck still renders.
        base["layout"] = "section-text"
        layout = "section-text"

    if layout == "section-text":
        if hint == "big-quote" or slide.get("quote"):
            base["blocks"] = _quote_blocks(slide)
            base["mood"] = "quote"
        else:
            stat_blocks = (
                _stat_blocks(slide) if (hint == "stat-highlight" or slide.get("stat")) else None
            )
            if stat_blocks:
                base["blocks"] = stat_blocks
                base["mood"] = "stat"
            else:
                # Downgrade: no real number, render bullets as blocks.
                base["blocks"] = _as_blocks_from_bullets(bullets) or [
                    {"label": "要点 01", "text": slide.get("title", "")}
                ]

    return base


def compile_to_pku(
    generic: dict[str, Any], options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Turn the generic slide_json into a PKU-format slides.json dict."""
    options = options or {}

    # meta -------------------------------------------------------------
    meta = copy.deepcopy(DEFAULT_META)
    meta["title"] = generic.get("title", "") or meta["title"]
    if generic.get("subtitle"):
        meta["subtitle"] = generic["subtitle"]
    for key in ("presenter", "advisor", "school", "date", "motto", "logo"):
        if options.get(key):
            meta[key] = options[key]

    # chapters from section slides (preserving order, deduped) --------
    chapter_titles: list[str] = []
    for s in generic.get("slides", []):
        if s.get("type") == "section":
            t = (s.get("title") or s.get("section") or "").strip()
            if t and t not in chapter_titles:
                chapter_titles.append(t)
    if 3 <= len(chapter_titles) <= 6:
        chapters: list[dict[str, str]] = [
            {"title": t, "subtitle": ""} for t in chapter_titles
        ]
    else:
        chapters = copy.deepcopy(DEFAULT_CHAPTERS)
    title_to_idx = {c["title"]: i for i, c in enumerate(chapters)}

    # slides ------------------------------------------------------------
    pku_slides: list[dict[str, Any]] = []
    current_chapter = 0
    current_section_title = ""
    has_cover = False
    has_closing = False

    for s in generic.get("slides", []):
        t = s.get("type")
        if t == "cover":
            pku_slides.append({"layout": "cover"})
            has_cover = True
        elif t == "contents":
            pku_slides.append({"layout": "contents"})
        elif t == "section":
            title = (s.get("title") or "").strip()
            if title in title_to_idx:
                current_chapter = title_to_idx[title]
            current_section_title = title
            bullets = [b for b in (s.get("bullets") or []) if isinstance(b, str)]
            points = bullets[:5] or [title or "章节要点"]
            pku_slides.append({
                "layout": "section-divider",
                "chapterIndex": current_chapter,
                "points": points,
            })
        elif t == "closing":
            pku_slides.append({
                "layout": "closing",
                "title": s.get("title", "感谢您的倾听！"),
                "subtitle": "THANK YOU FOR LISTENING",
                "message": (
                    s.get("notes")
                    or s.get("speaker_notes")
                    or "感谢导师的悉心指导，感谢各位老师与同学的支持。敬请各位老师批评指正。"
                ),
            })
            has_closing = True
        elif t == "content":
            sect = (s.get("section") or current_section_title or "").strip()
            if sect and sect in title_to_idx:
                current_chapter = title_to_idx[sect]
                current_section_title = sect
            pku_slides.append(
                _render_content(s, current_chapter, current_section_title)
            )

    if not has_cover:
        pku_slides.insert(0, {"layout": "cover"})
    if not has_closing:
        pku_slides.append({
            "layout": "closing",
            "title": "感谢您的倾听！",
            "subtitle": "THANK YOU FOR LISTENING",
            "message": "敬请各位老师批评指正。",
        })

    return {"meta": meta, "chapters": chapters, "slides": pku_slides}


__all__ = ["compile_to_pku", "DEFAULT_CHAPTERS", "DEFAULT_META"]
