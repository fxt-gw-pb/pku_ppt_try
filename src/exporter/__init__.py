"""Materialize a PKU slides.json into a runnable deck directory + zip.

The template tree lives at `pku-red-defense-ppt/assets/template/` (a mirror
of the root deck, intended as the canonical bundle to copy from). The
exporter copies that tree to the output directory and overwrites
`data/slides.json` with the freshly-compiled deck.
"""
from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "pku-red-defense-ppt" / "assets" / "template"
HTML_PPT_SHARED_DIR = REPO_ROOT / "templates" / "html-ppt" / "shared" / "assets"
HTML_PPT_TEMPLATE_ROOT = REPO_ROOT / "templates" / "html-ppt"


def export_deck(
    pku_json: dict[str, Any], output_dir: str | Path, *, force: bool = True
) -> Path:
    """Copy the template to output_dir and drop pku_json into data/slides.json.

    Returns the absolute path of the materialized deck directory.
    """
    if not TEMPLATE_DIR.is_dir():
        raise FileNotFoundError(
            f"template dir missing: {TEMPLATE_DIR}. The skill bundle at "
            "`pku-red-defense-ppt/assets/template/` is required."
        )

    out = Path(output_dir).resolve()
    if out.exists():
        if not force:
            raise FileExistsError(f"output dir already exists: {out}")
        shutil.rmtree(out)

    shutil.copytree(TEMPLATE_DIR, out)
    slides_path = out / "data" / "slides.json"
    slides_path.parent.mkdir(parents=True, exist_ok=True)
    slides_path.write_text(
        json.dumps(pku_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def zip_deck(deck_dir: str | Path, zip_path: str | Path) -> Path:
    """Zip the materialized deck. Inside the zip, paths are rooted at the
    deck dir's own name so unzipping produces a single folder."""
    deck_dir = Path(deck_dir).resolve()
    zip_path = Path(zip_path).resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(deck_dir):
            for fname in files:
                abs_p = Path(root) / fname
                rel_p = abs_p.relative_to(deck_dir.parent)
                zf.write(abs_p, rel_p)
    return zip_path


def export_html_ppt_deck(
    html_text: str,
    output_dir: str | Path,
    *,
    template_id: str,
    force: bool = True,
) -> Path:
    """Materialize an html-ppt deck with shared runtime assets.

    html-ppt full-deck templates are static HTML sections, so the renderer
    returns a complete index.html. The exporter copies only the production
    assets needed at runtime, not the entire preview gallery.
    """
    template_dir = HTML_PPT_TEMPLATE_ROOT / template_id
    style_src = template_dir / "style.css"
    if not HTML_PPT_SHARED_DIR.is_dir():
        raise FileNotFoundError(f"html-ppt shared assets missing: {HTML_PPT_SHARED_DIR}")
    if not style_src.is_file():
        raise FileNotFoundError(f"html-ppt template style missing: {style_src}")

    out = Path(output_dir).resolve()
    if out.exists():
        if not force:
            raise FileExistsError(f"output dir already exists: {out}")
        shutil.rmtree(out)

    out.mkdir(parents=True)
    assets_out = out / "assets"
    shutil.copytree(HTML_PPT_SHARED_DIR, assets_out)
    shutil.copy2(style_src, out / "style.css")
    manifest = template_dir / "manifest.json"
    if manifest.is_file():
        shutil.copy2(manifest, out / "template-manifest.json")
    (out / "index.html").write_text(html_text, encoding="utf-8")
    return out


__all__ = [
    "export_deck",
    "export_html_ppt_deck",
    "zip_deck",
    "TEMPLATE_DIR",
    "HTML_PPT_SHARED_DIR",
    "HTML_PPT_TEMPLATE_ROOT",
    "REPO_ROOT",
]
