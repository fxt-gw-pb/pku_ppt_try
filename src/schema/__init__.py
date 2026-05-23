"""Validation for the generic slide_json shape that the LLM is contracted to
produce. The PKU-format slides.json has a separate validator under
`pku-red-defense-ppt/scripts/validate_slides.py`; that one runs against the
*materialized* deck and also checks image-file existence.
"""
from __future__ import annotations

from typing import Any

KNOWN_TYPES = {"cover", "contents", "section", "content", "closing"}

KNOWN_PKU_LAYOUTS = {
    "cover", "contents", "section-divider",
    "image-analysis", "chart-analysis", "timeline",
    "theory-cards", "multi-card", "framework",
    "vs", "swot", "method", "section-text", "closing",
}


def validate_slide_json(data: Any) -> list[str]:
    """Return a list of human-readable errors. Empty list = valid."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["top-level JSON is not an object"]

    if not isinstance(data.get("title"), str) or not data["title"].strip():
        errors.append("missing or empty 'title' at top level")

    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("'slides' is missing or empty")
        return errors

    for i, s in enumerate(slides):
        prefix = f"slides[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{prefix}: not an object")
            continue

        t = s.get("type")
        if t not in KNOWN_TYPES:
            errors.append(
                f"{prefix}: unknown type {t!r} (expected one of {sorted(KNOWN_TYPES)})"
            )
            continue

        title = s.get("title")
        if t in {"section", "content", "contents"} and (
            not isinstance(title, str) or not title.strip()
        ):
            errors.append(f"{prefix}: missing or empty 'title'")

        bullets = s.get("bullets")
        if bullets is not None and not isinstance(bullets, list):
            errors.append(f"{prefix}: 'bullets' must be a list when present")
        elif isinstance(bullets, list):
            for j, b in enumerate(bullets):
                if not isinstance(b, str):
                    errors.append(f"{prefix}.bullets[{j}]: must be a string")

        layout = s.get("layout")
        if layout is not None and layout not in KNOWN_PKU_LAYOUTS:
            errors.append(
                f"{prefix}: unknown layout hint {layout!r} (expected one of {sorted(KNOWN_PKU_LAYOUTS)})"
            )

    return errors


__all__ = ["validate_slide_json", "KNOWN_TYPES", "KNOWN_PKU_LAYOUTS"]
