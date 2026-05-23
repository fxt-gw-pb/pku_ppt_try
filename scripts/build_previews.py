#!/usr/bin/env python3
"""Build one sample deck per template into ./previews/<template_id>/.

Uses the mock LLM provider (no API key required) + examples/input.md as the
manuscript. The PKU bundle ships ~9 MB of stock photos under
assets/media/; this script keeps only the files referenced by the sample's
slides.json so the previews directory stays small enough to commit.

Run from repo root:

    python scripts/build_previews.py

Frontends point at /previews/<id>/index.html (relative URL — works from both
GitHub Pages and the local FastAPI mount).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.templates import list_templates  # noqa: E402

PREVIEWS_DIR = REPO_ROOT / "previews"
SAMPLE_INPUT = REPO_ROOT / "examples" / "input.md"


def trim_media(deck_dir: Path) -> None:
    """Drop asset/media files the sample slides don't actually reference."""
    media_dir = deck_dir / "assets" / "media"
    if not media_dir.is_dir():
        return
    slides_json = deck_dir / "data" / "slides.json"
    if not slides_json.is_file():
        return
    text = slides_json.read_text(encoding="utf-8")
    referenced = set(re.findall(r"media/([^\s\"']+)", text))
    for path in media_dir.iterdir():
        if path.is_file() and path.name not in referenced:
            path.unlink()


def main() -> int:
    if not SAMPLE_INPUT.is_file():
        print(f"missing sample manuscript: {SAMPLE_INPUT}", file=sys.stderr)
        return 1

    if PREVIEWS_DIR.exists():
        shutil.rmtree(PREVIEWS_DIR)
    PREVIEWS_DIR.mkdir(parents=True)

    failures: list[str] = []
    for tpl in list_templates():
        tid = tpl["template_id"]
        out = PREVIEWS_DIR / tid
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate.py"),
            "--provider",
            "mock",
            "--template",
            tid,
            "--input",
            str(SAMPLE_INPUT),
            "--output",
            str(out),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not (out / "index.html").is_file():
            failures.append(tid)
            print(f"FAIL  {tid}: {result.stderr.strip()[:200]}", file=sys.stderr)
            continue
        trim_media(out)
        size_kb = sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) // 1024
        print(f"OK    {tid} ({size_kb} KB)")

    if failures:
        print(f"\n{len(failures)} template(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
