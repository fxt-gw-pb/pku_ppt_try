#!/usr/bin/env python3
"""CLI: manuscript file → PKU defense deck.

    python scripts/generate.py --input examples/input.md --output outputs/demo

Reads .env if present so you can drop a DEEPSEEK_API_KEY there. Defaults to
LLM_PROVIDER=mock if nothing is set, so the command works out-of-the-box
without a real key.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from src.exporter import export_deck  # noqa: E402
from src.llm import generate_slide_json  # noqa: E402
from src.renderer import compile_to_pku  # noqa: E402
from src.schema import validate_slide_json  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description="Generate a PKU defense deck from a manuscript file."
    )
    p.add_argument("--input", required=True, help="Path to manuscript (text/markdown)")
    p.add_argument(
        "--output", required=True, help="Output dir (will be created / overwritten)"
    )
    p.add_argument(
        "--provider",
        help="Override LLM_PROVIDER (deepseek | mock). Defaults to env LLM_PROVIDER or 'mock'.",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=int(os.environ.get("MAX_INPUT_CHARS", "30000")),
        help="Truncate manuscript to this many chars before sending to the LLM.",
    )
    args = p.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 2

    manuscript = input_path.read_text(encoding="utf-8")
    if len(manuscript) > args.max_chars:
        print(
            f"⚠ manuscript truncated from {len(manuscript)} to {args.max_chars} chars",
            file=sys.stderr,
        )
        manuscript = manuscript[: args.max_chars]

    options: dict[str, str] = {}
    if args.provider:
        options["provider"] = args.provider

    provider_label = options.get("provider") or os.environ.get("LLM_PROVIDER", "mock")
    print(f"→ generating slide_json via LLM provider={provider_label}…")
    generic = generate_slide_json(manuscript, options)
    errors = validate_slide_json(generic)
    if errors:
        print("✘ generic slide_json failed validation:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("→ compiling to PKU slides.json…")
    pku = compile_to_pku(generic)

    out_dir = Path(args.output).resolve()
    print(f"→ materializing deck at {out_dir}…")
    deck_path = export_deck(pku, out_dir, force=True)

    # Drop the raw LLM JSON alongside for debugging / re-runs.
    (deck_path / "data" / "slide.json").write_text(
        json.dumps(generic, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✓ deck ready: {deck_path}")
    print(f"  preview:  cd {deck_path} && python3 -m http.server 8080")
    print(f"            open http://localhost:8080/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
