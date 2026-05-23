"""Compile a generic slide_json (produced by the LLM) into a PKU `slides.json`
that the HTML template's `runtime.js` renderer can consume.

The contract between LLM output and PPT skill is intentionally narrow:
  - LLM produces semantic content (cover / contents / section / content / closing)
    with bullets and an optional `layout` hint.
  - This compiler decides the concrete PKU layout per slide, assigns
    `chapterIndex` consistently, and fills in PKU-shaped fields
    (`headline`, `cards`, `blocks`, `points`, ...).

When the LLM provides a known `layout` hint, the compiler honors it for the
subset of layouts that can be reasonably produced from a bullets-only input:
  - "multi-card"     → bullets become cards (1 per bullet)
  - "section-text"   → bullets become labeled paragraph blocks
  - "theory-cards"   → same shape as multi-card with a red-headed card style
  - "method"         → bullets become method cards
  - "timeline"       → bullets become time steps (best-effort labels)

For richer layouts (image-analysis, chart-analysis, framework, vs, swot, ...)
the LLM would need to provide structured fields the bullets format doesn't
carry, so the compiler currently falls back to multi-card / section-text.
"""
from __future__ import annotations

import copy
from typing import Any

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

CARDLIKE_LAYOUTS = {"multi-card", "theory-cards", "method"}
BLOCKLIKE_LAYOUTS = {"section-text"}
STEPLIKE_LAYOUTS = {"timeline"}


def _split_kv(bullet: str) -> tuple[str, str]:
    """Split a 'title: body' bullet on either : or ：; otherwise return ('', body)."""
    for sep in ("：", ":"):
        if sep in bullet:
            head, _, tail = bullet.partition(sep)
            head, tail = head.strip(), tail.strip()
            if head and tail:
                return head, tail
    return "", bullet.strip()


def _as_cards(bullets: list[str]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        cards.append({
            "title": head or f"要点 {i + 1}",
            "body": body or b,
            "tag": f"{i + 1:02d}",
        })
    return cards


def _as_method_cards(bullets: list[str]) -> list[dict[str, str]]:
    methods: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        methods.append({
            "title": head or f"方法 {i + 1}",
            "en": f"METHOD {chr(64 + i + 1)}",
            "body": body or b,
        })
    return methods


def _as_blocks(bullets: list[str]) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        blocks.append({
            "label": head or f"要点 {i + 1:02d}",
            "text": body or b,
        })
    return blocks


def _as_steps(bullets: list[str]) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for i, b in enumerate(bullets):
        head, body = _split_kv(b)
        steps.append({
            "label": f"S{i + 1}",
            "title": head or f"阶段 {i + 1}",
            "body": body or b,
        })
    return steps


def _pick_layout(layout_hint: str | None, n_bullets: int) -> str:
    """Decide the concrete PKU layout for a content slide."""
    if layout_hint in CARDLIKE_LAYOUTS | BLOCKLIKE_LAYOUTS | STEPLIKE_LAYOUTS:
        return layout_hint
    # Heuristic by bullet count.
    if 2 <= n_bullets <= 4:
        return "multi-card"
    return "section-text"


def _render_content(
    slide: dict[str, Any], chapter_idx: int, section_title: str
) -> dict[str, Any]:
    bullets: list[str] = list(slide.get("bullets") or [])
    layout = _pick_layout(slide.get("layout"), len(bullets))
    base: dict[str, Any] = {
        "layout": layout,
        "chapterIndex": chapter_idx,
        "sectionTitle": section_title or slide.get("title", ""),
        "sectionTitleEn": "",
        "headline": slide.get("title", ""),
    }
    if layout == "multi-card":
        base["cols"] = min(max(len(bullets), 2), 4)
        base["cards"] = _as_cards(bullets) or [
            {"title": slide.get("title", "要点"), "body": ""}
        ]
    elif layout == "theory-cards":
        base["cards"] = [
            {"title": c["title"], "label": c["tag"], "body": c["body"]}
            for c in _as_cards(bullets)
        ] or [{"title": slide.get("title", "要点"), "body": ""}]
    elif layout == "method":
        base["cols"] = min(max(len(bullets), 2), 4)
        base["methods"] = _as_method_cards(bullets) or [
            {"title": slide.get("title", "方法"), "en": "METHOD", "body": ""}
        ]
    elif layout == "timeline":
        base["steps"] = _as_steps(bullets) or [
            {"label": "S1", "title": slide.get("title", "阶段"), "body": ""}
        ]
    else:  # section-text fallback
        base["blocks"] = _as_blocks(bullets) or [
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
            # If the LLM tagged this content with a section name, prefer that
            # over the most-recent section-divider context.
            sect = (s.get("section") or current_section_title or "").strip()
            if sect and sect in title_to_idx:
                current_chapter = title_to_idx[sect]
                current_section_title = sect
            pku_slides.append(
                _render_content(s, current_chapter, current_section_title)
            )

    # Always ensure cover at the front and closing at the back so the deck
    # opens and ends correctly even if the LLM forgot them.
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
