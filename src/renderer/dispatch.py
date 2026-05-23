"""Lookup table for html-ppt template renderers.

Each renderer takes the generic slide_json plus the template's id/body_class
and returns a complete index.html string. Templates without a dedicated
renderer fall back to render_html_ppt_generic.
"""
from __future__ import annotations

from typing import Any, Callable

from .course_module import render_course_module
from .dir_key_nav_minimal import render_dir_key_nav_minimal
from .graphify_dark_graph import render_graphify_dark_graph
from .hermes_cyber_terminal import render_hermes_cyber_terminal
from .html_ppt_generic import render_html_ppt_generic
from .knowledge_arch_blueprint import render_knowledge_arch_blueprint
from .obsidian_claude_gradient import render_obsidian_claude_gradient
from .pitch_deck import render_pitch_deck
from .presenter_mode_reveal import render_presenter_mode_reveal
from .product_launch import render_product_launch
from .tech_sharing import render_tech_sharing
from .testing_safety_alert import render_testing_safety_alert
from .weekly_report import render_weekly_report
from .xhs_pastel_card import render_xhs_pastel_card
from .xhs_post import render_xhs_post
from .xhs_white_editorial import render_xhs_white_editorial

RendererFn = Callable[..., str]


def _wrap_simple(fn: Callable[[dict[str, Any]], str]) -> RendererFn:
    def _inner(generic: dict[str, Any], *, template_id: str, body_class: str) -> str:
        return fn(generic)
    return _inner


_RENDERERS: dict[str, RendererFn] = {
    "xhs-white-editorial": _wrap_simple(render_xhs_white_editorial),
    "xhs-pastel-card": _wrap_simple(render_xhs_pastel_card),
    "xhs-post": _wrap_simple(render_xhs_post),
    "graphify-dark-graph": _wrap_simple(render_graphify_dark_graph),
    "hermes-cyber-terminal": _wrap_simple(render_hermes_cyber_terminal),
    "obsidian-claude-gradient": _wrap_simple(render_obsidian_claude_gradient),
    "tech-sharing": _wrap_simple(render_tech_sharing),
    "knowledge-arch-blueprint": _wrap_simple(render_knowledge_arch_blueprint),
    "weekly-report": _wrap_simple(render_weekly_report),
    "pitch-deck": _wrap_simple(render_pitch_deck),
    "product-launch": _wrap_simple(render_product_launch),
    "course-module": _wrap_simple(render_course_module),
    "dir-key-nav-minimal": _wrap_simple(render_dir_key_nav_minimal),
    "testing-safety-alert": _wrap_simple(render_testing_safety_alert),
    "presenter-mode-reveal": _wrap_simple(render_presenter_mode_reveal),
}


def render_for(renderer_slug: str, generic: dict[str, Any], *, template_id: str, body_class: str) -> str:
    """Dispatch to a dedicated renderer if registered; otherwise generic."""
    fn = _RENDERERS.get(renderer_slug)
    if fn is None:
        return render_html_ppt_generic(generic, template_id=template_id, body_class=body_class)
    return fn(generic, template_id=template_id, body_class=body_class)


def register(renderer_slug: str, fn: Callable[[dict[str, Any]], str] | RendererFn) -> None:
    """Register a new template-specific renderer."""
    # Heuristic: if fn accepts only one positional arg, wrap it.
    try:
        import inspect
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        kw_count = sum(1 for p in params if p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD))
        if kw_count <= 1:
            _RENDERERS[renderer_slug] = _wrap_simple(fn)  # type: ignore[arg-type]
            return
    except (TypeError, ValueError):
        pass
    _RENDERERS[renderer_slug] = fn  # type: ignore[assignment]


__all__ = ["render_for", "register"]
