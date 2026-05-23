#!/usr/bin/env python3
"""Materialize a new PKU red defense deck from a slides.json.

Usage:
    python3 create_deck.py <slides.json> <output-dir> [--media DIR]

What it does:
    1. Copies the bundled assets/template/ tree to <output-dir>.
    2. Replaces <output-dir>/data/slides.json with the user's JSON.
    3. If --media is given, copies its contents into <output-dir>/assets/media/.
    4. Runs validate_slides.py against the new deck and prints the result.

Then preview with:
    cd <output-dir> && python3 -m http.server 8080
    open http://localhost:8080/index.html
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.normpath(os.path.join(HERE, "..", "assets", "template"))
VALIDATOR = os.path.join(HERE, "validate_slides.py")


def main() -> int:
    p = argparse.ArgumentParser(description="Materialize a PKU red defense deck.")
    p.add_argument("slides_json", help="Path to the slides.json to drop into data/")
    p.add_argument("output_dir", help="Directory to create (must not already contain index.html)")
    p.add_argument("--media", help="Optional directory of user images to copy into assets/media/", default=None)
    p.add_argument("--force", action="store_true", help="Overwrite output_dir if it exists")
    args = p.parse_args()

    if not os.path.isdir(TEMPLATE):
        print(f"template not found at {TEMPLATE}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.slides_json):
        print(f"slides.json not found: {args.slides_json}", file=sys.stderr)
        return 2
    if args.media and not os.path.isdir(args.media):
        print(f"--media directory not found: {args.media}", file=sys.stderr)
        return 2

    out = os.path.abspath(args.output_dir)
    if os.path.exists(out):
        if not args.force:
            print(f"refusing to overwrite existing {out} (use --force)", file=sys.stderr)
            return 2
        shutil.rmtree(out)

    shutil.copytree(TEMPLATE, out)
    shutil.copy2(args.slides_json, os.path.join(out, "data", "slides.json"))

    if args.media:
        dst = os.path.join(out, "assets", "media")
        for name in os.listdir(args.media):
            src = os.path.join(args.media, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(dst, name))

    print(f"✓ deck copied to {out}")
    print(f"  data/slides.json     ← {args.slides_json}")
    if args.media:
        print(f"  assets/media/        ← {args.media}/*")

    # Run the validator inline.
    rc = subprocess.call(
        [sys.executable, VALIDATOR, os.path.join(out, "data", "slides.json")]
    )
    if rc != 0:
        print("⚠ validator reported issues; deck materialized but may not render correctly.")
        return rc

    print()
    print("Preview with:")
    print(f"  cd {out} && python3 -m http.server 8080")
    print("  open http://localhost:8080/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
