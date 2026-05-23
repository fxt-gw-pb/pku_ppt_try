"""LLM adapter layer.

Public entry: `generate_slide_json(manuscript, options)`.

The adapter dispatches to a provider implementation based on
`options["provider"]` (overrides) or the `LLM_PROVIDER` env var.

Each provider is responsible for:
  - Calling its LLM with a strict-JSON system prompt.
  - Returning a Python dict that conforms to the generic slide_json schema
    (validated separately by `src.schema.validate_slide_json`).

The renderer step (`src.renderer.compile_to_pku`) then converts that generic
shape to the PKU `slides.json` format that the HTML template expects.
"""
from __future__ import annotations

import os
from typing import Any

from .deepseek import generate as _deepseek_generate
from .mock import generate as _mock_generate


def generate_slide_json(
    manuscript: str, options: dict[str, Any] | None = None
) -> dict[str, Any]:
    options = options or {}
    provider = (options.get("provider") or os.environ.get("LLM_PROVIDER") or "mock").lower()
    if provider == "deepseek":
        return _deepseek_generate(manuscript, options)
    if provider == "mock":
        return _mock_generate(manuscript, options)
    raise ValueError(
        f"unknown LLM_PROVIDER {provider!r} (expected: 'deepseek' or 'mock')"
    )


__all__ = ["generate_slide_json"]
