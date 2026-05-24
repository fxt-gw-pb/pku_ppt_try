"""Validation for the generic slide_json shape that the LLM is contracted to
produce. The PKU-format slides.json has a separate validator under
`pku-red-defense-ppt/scripts/validate_slides.py`; that one runs against the
*materialized* deck and also checks image-file existence.
"""
from __future__ import annotations

from typing import Any

KNOWN_TYPES = {"cover", "contents", "section", "content", "closing"}

# PKU runtime layouts (consumed by `compile_to_pku`).
KNOWN_PKU_LAYOUTS = {
    "cover", "contents", "section-divider",
    "image-analysis", "chart-analysis", "timeline",
    "theory-cards", "multi-card", "framework",
    "vs", "swot", "method", "section-text", "closing",
}

# Generic / html-ppt-style layouts (consumed by html-ppt renderers). Mostly
# inspired by `html-ppt-templates/templates/single-page/*.html`; rendered by
# template-specific functions in `src/renderer/<template>.py`.
KNOWN_GENERIC_LAYOUTS = {
    "bullets", "cards",
    "two-column", "three-column",
    "kpi-grid", "stat-highlight",
    "comparison", "pros-cons",
    "big-quote", "quote-card",
    "process-steps",
    # also accepted (already in PKU set, but valid for html-ppt too):
    "timeline",
}

# Union — anything in either set is a valid `layout` hint.
KNOWN_LAYOUTS = KNOWN_PKU_LAYOUTS | KNOWN_GENERIC_LAYOUTS


def _check_str_list(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{prefix}: must be a list")
        return
    for i, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{prefix}[{i}]: must be a string")


def _check_structured_fields(slide: dict[str, Any], prefix: str, errors: list[str]) -> None:
    """Validate the optional structured fields layouts can lean on.

    All structured fields are optional — when absent, renderers fall back to
    parsing `bullets` heuristically. We only validate *shape*, not whether
    the data matches the chosen layout.
    """
    stat = slide.get("stat")
    if stat is not None:
        if not isinstance(stat, dict):
            errors.append(f"{prefix}.stat: must be an object")
        else:
            if "value" not in stat or not isinstance(stat.get("value"), (str, int, float)):
                errors.append(f"{prefix}.stat.value: required (str/number)")

    quote = slide.get("quote")
    if quote is not None:
        if not isinstance(quote, dict):
            errors.append(f"{prefix}.quote: must be an object")
        elif not isinstance(quote.get("text"), str) or not quote.get("text", "").strip():
            errors.append(f"{prefix}.quote.text: required non-empty string")

    compare = slide.get("compare")
    if compare is not None:
        if not isinstance(compare, dict):
            errors.append(f"{prefix}.compare: must be an object")
        else:
            for side in ("left", "right"):
                side_obj = compare.get(side)
                if side_obj is None:
                    continue
                if not isinstance(side_obj, dict):
                    errors.append(f"{prefix}.compare.{side}: must be an object")
                    continue
                points = side_obj.get("points") or side_obj.get("bullets")
                if points is not None:
                    _check_str_list(points, f"{prefix}.compare.{side}.points", errors)

    kpis = slide.get("kpis")
    if kpis is not None:
        if not isinstance(kpis, list):
            errors.append(f"{prefix}.kpis: must be a list")
        else:
            for i, k in enumerate(kpis):
                if not isinstance(k, dict):
                    errors.append(f"{prefix}.kpis[{i}]: must be an object")
                    continue
                if not isinstance(k.get("label"), str):
                    errors.append(f"{prefix}.kpis[{i}].label: required string")
                if "value" not in k:
                    errors.append(f"{prefix}.kpis[{i}].value: required")

    steps = slide.get("steps")
    if steps is not None:
        if not isinstance(steps, list):
            errors.append(f"{prefix}.steps: must be a list")
        else:
            for i, st in enumerate(steps):
                if not isinstance(st, dict):
                    errors.append(f"{prefix}.steps[{i}]: must be an object")
                    continue
                if not isinstance(st.get("title"), str):
                    errors.append(f"{prefix}.steps[{i}].title: required string")

    columns = slide.get("columns")
    if columns is not None:
        if not isinstance(columns, list):
            errors.append(f"{prefix}.columns: must be a list")
        else:
            for i, c in enumerate(columns):
                if not isinstance(c, dict):
                    errors.append(f"{prefix}.columns[{i}]: must be an object")
                    continue
                if not isinstance(c.get("title"), str):
                    errors.append(f"{prefix}.columns[{i}].title: required string")


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
        if layout is not None and layout not in KNOWN_LAYOUTS:
            errors.append(
                f"{prefix}: unknown layout hint {layout!r} (expected one of {sorted(KNOWN_LAYOUTS)})"
            )

        _check_structured_fields(s, prefix, errors)

    return errors


__all__ = [
    "validate_slide_json",
    "KNOWN_TYPES",
    "KNOWN_LAYOUTS",
    "KNOWN_PKU_LAYOUTS",
    "KNOWN_GENERIC_LAYOUTS",
]
