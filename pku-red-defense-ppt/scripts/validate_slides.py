#!/usr/bin/env python3
"""Validate a data/slides.json against the PKU red defense template schema.

Usage:
    python3 validate_slides.py <path/to/slides.json>

The deck root is inferred as the parent of the parent of slides.json
(i.e. <root>/data/slides.json), and image paths are resolved relative
to that root. Exits non-zero on any error.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

KNOWN_LAYOUTS = {
    "cover",
    "contents",
    "section-divider",
    "image-analysis",
    "chart-analysis",
    "timeline",
    "theory-cards",
    "multi-card",
    "framework",
    "vs",
    "swot",
    "method",
    "section-text",
    "closing",
}

KNOWN_FITS = {"cover", "contain", "diagram", "logo", "fullBleed"}

REQUIRED_FIELDS = {
    "section-divider": ["chapterIndex"],
    "image-analysis": ["chapterIndex", "headline", "items"],
    "chart-analysis": ["chapterIndex", "headline", "insights"],
    "timeline": ["chapterIndex", "headline", "steps"],
    "theory-cards": ["chapterIndex", "headline", "cards"],
    "multi-card": ["chapterIndex", "headline", "cards"],
    "framework": ["chapterIndex", "headline", "nodes"],
    "vs": ["chapterIndex", "headline", "leftItems", "rightItems"],
    "swot": ["chapterIndex", "headline"],
    "method": ["chapterIndex", "headline", "methods"],
    "section-text": ["chapterIndex", "headline", "blocks"],
}


def validate(deck: dict[str, Any], root: str) -> list[str]:
    errors: list[str] = []

    if not isinstance(deck, dict):
        return ["top-level JSON is not an object"]

    chapters = deck.get("chapters") or []
    if not isinstance(chapters, list) or not (3 <= len(chapters) <= 6):
        errors.append(
            f"chapters[]: expected 3–6 entries, got {len(chapters) if isinstance(chapters, list) else 'non-list'}"
        )

    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        return errors + ["slides[]: missing or empty"]

    for i, s in enumerate(slides):
        prefix = f"slides[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{prefix}: not an object")
            continue

        layout = s.get("layout")
        if layout not in KNOWN_LAYOUTS:
            errors.append(f"{prefix}: unknown layout {layout!r}")
            continue

        for field in REQUIRED_FIELDS.get(layout, []):
            if field not in s or s[field] in (None, "", [], {}):
                errors.append(f"{prefix} ({layout}): missing required field {field!r}")

        ch_idx = s.get("chapterIndex")
        if ch_idx is not None:
            if not isinstance(ch_idx, int) or not (0 <= ch_idx < len(chapters)):
                errors.append(
                    f"{prefix}: chapterIndex {ch_idx!r} out of range for {len(chapters)} chapters"
                )

        for j, img in enumerate(s.get("images") or []):
            if not isinstance(img, dict):
                errors.append(f"{prefix}.images[{j}]: not an object")
                continue
            src = img.get("src")
            if not src:
                errors.append(f"{prefix}.images[{j}]: missing src")
            else:
                abs_path = os.path.join(root, src)
                if not os.path.isfile(abs_path):
                    errors.append(f"{prefix}.images[{j}]: src not found on disk: {src}")
            fit = img.get("fit")
            if fit is not None and fit not in KNOWN_FITS:
                errors.append(
                    f"{prefix}.images[{j}]: unknown fit {fit!r} (expected one of {sorted(KNOWN_FITS)})"
                )

        logo = (deck.get("meta") or {}).get("logo")
        if i == 0 and logo:
            if not os.path.isfile(os.path.join(root, logo)):
                errors.append(f"meta.logo not found on disk: {logo}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_slides.py <path/to/slides.json>", file=sys.stderr)
        return 2

    json_path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(json_path):
        print(f"file not found: {json_path}", file=sys.stderr)
        return 2

    # Deck root: parent of the data/ directory.
    deck_root = os.path.dirname(os.path.dirname(json_path))

    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            deck = json.load(fh)
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {json_path}: {e}", file=sys.stderr)
        return 1

    errors = validate(deck, deck_root)
    if errors:
        print(f"✘ {len(errors)} issue(s) in {json_path}:")
        for e in errors:
            print(f"  - {e}")
        return 1

    n_slides = len(deck.get("slides") or [])
    n_chapters = len(deck.get("chapters") or [])
    print(f"✓ {json_path}: {n_slides} slides, {n_chapters} chapters, no issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
