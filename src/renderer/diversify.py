"""Layout-diversification pass that runs after LLM generation.

The DeepSeek prompt asks the model to vary layouts, but in practice it tends
to lock onto ``cards`` for long stretches when the manuscript is mostly
prose. This module post-processes the validated generic ``slide_json`` and
breaks runs of three-or-more consecutive content slides with the same
``layout`` by picking an honest, content-fit alternative for the offending
slide.

Rules:
- A "run" only counts adjacent ``type=content`` slides. ``section`` /
  ``cover`` / ``closing`` slides reset the streak.
- The first and second slide in a run are left alone (two-in-a-row is
  acceptable cadence). The third and beyond get rewritten.
- The replacement layout must fit the slide's actual content shape — we
  never invent ``kpis`` / ``stat`` / ``quote`` data just to use a flashier
  layout. If the slide has no fit alternative, we leave it (rare).
"""
from __future__ import annotations

import copy
from typing import Any

from . import layouts as L

# Layouts considered when picking a replacement, ordered by visual
# distinctiveness vs. ``cards`` (the most-common offender).
_CANDIDATE_ORDER = (
    "two-column",
    "three-column",
    "process-steps",
    "timeline",
    "comparison",
    "pros-cons",
    "kpi-grid",
    "stat-highlight",
    "big-quote",
    "bullets",
    "cards",
)


def _fits(slide: dict[str, Any], layout: str) -> bool:
    """True when `slide` carries enough real data for `layout` without
    fabrication. Mirrors the gating logic in `render_inner` /
    `compile_to_pku` so post-processing never picks a layout that would
    immediately be downgraded.
    """
    bullets = L.get_bullets(slide)
    n = len(bullets)

    if layout == "kpi-grid":
        return len(L.get_kpis(slide)) >= 2
    if layout == "stat-highlight":
        return L.get_stat(slide) is not None
    if layout == "big-quote":
        q = slide.get("quote")
        return isinstance(q, dict) and bool((q.get("text") or "").strip())
    if layout in {"comparison", "pros-cons"}:
        cmp = slide.get("compare")
        if not isinstance(cmp, dict):
            return False
        left = cmp.get("left") or {}
        right = cmp.get("right") or {}
        lp = left.get("points") if isinstance(left, dict) else None
        rp = right.get("points") if isinstance(right, dict) else None
        return (isinstance(lp, list) and len(lp) >= 1
                and isinstance(rp, list) and len(rp) >= 1)
    if layout == "timeline":
        steps = slide.get("steps")
        if not (isinstance(steps, list) and len(steps) >= 3):
            return False
        # Require time anchors to feel like a timeline.
        return any(isinstance(s, dict) and (s.get("when") or "").strip() for s in steps)
    if layout == "process-steps":
        steps = slide.get("steps")
        if isinstance(steps, list) and len(steps) >= 2:
            return True
        # Bullets shaped as "标题: 正文" can carry a process when 3+ exist.
        return n >= 3 and all(L.split_kv(b)[0] for b in bullets[:n])
    if layout == "two-column":
        cols = slide.get("columns")
        if isinstance(cols, list) and len(cols) >= 2:
            return True
        return n == 2 or (n >= 2 and all(L.split_kv(b)[0] for b in bullets[:2]))
    if layout == "three-column":
        cols = slide.get("columns")
        if isinstance(cols, list) and len(cols) >= 3:
            return True
        return n == 3 and all(L.split_kv(b)[0] for b in bullets[:3])
    if layout == "bullets":
        return n >= 4
    if layout == "cards":
        return n >= 1 or bool(slide.get("title"))
    return False


def _pick_alternative(slide: dict[str, Any], current: str, recent: list[str]) -> str | None:
    """Return a layout that (a) fits the slide's data, (b) differs from
    `current`, and (c) ideally doesn't appear in the last few used layouts.
    Returns None if no fit alternative exists."""
    avoid_recent = set(recent[-2:]) | {current}
    # First pass: layouts not seen recently
    for candidate in _CANDIDATE_ORDER:
        if candidate in avoid_recent:
            continue
        if _fits(slide, candidate):
            return candidate
    # Second pass: at least differ from current
    for candidate in _CANDIDATE_ORDER:
        if candidate == current:
            continue
        if _fits(slide, candidate):
            return candidate
    return None


def diversify_layouts(generic: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `generic` with consecutive identical content-slide
    layouts broken up. Three-or-more in a row triggers a rewrite of the
    third (and any further) slides until the streak is broken."""
    if not isinstance(generic, dict):
        return generic
    slides = generic.get("slides")
    if not isinstance(slides, list):
        return generic

    out = copy.deepcopy(generic)
    out_slides = out["slides"]
    streak_layout: str | None = None
    streak_len = 0
    used_recent: list[str] = []

    for s in out_slides:
        if not isinstance(s, dict):
            streak_layout = None
            streak_len = 0
            continue
        if s.get("type") != "content":
            streak_layout = None
            streak_len = 0
            continue
        cur = L.normalize_layout(s.get("layout"), len(L.get_bullets(s)))
        if cur == streak_layout:
            streak_len += 1
            if streak_len >= 3:
                # Try to swap this third-or-later slide to something else.
                alt = _pick_alternative(s, cur, used_recent)
                if alt and alt != cur:
                    s["layout"] = alt
                    cur = alt
                    # Reset streak around the swap.
                    streak_layout = alt
                    streak_len = 1
        else:
            streak_layout = cur
            streak_len = 1
        used_recent.append(cur)
        if len(used_recent) > 6:
            used_recent.pop(0)

    return out


__all__ = ["diversify_layouts"]
