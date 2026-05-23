# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A data-driven, static HTML PPT template for PKU-style (北京大学) Chinese academic thesis defense / opening report decks. There is **no build step, no package manager, no test suite** — the entire deck is a single `index.html` + vanilla JS/CSS + a `data/slides.json` data file.

The repo currently contains **two parallel things**:

1. **The deck at the root** (`index.html`, `deck-stage.js`, `assets/`, `data/slides.json`) — a runnable, intermediate-artifact reference deck.
2. **The packaged Claude skill at `pku-red-defense-ppt/`** — `SKILL.md` + `references/` + `scripts/` + `assets/template/`. `assets/template/` is a **copy** of the root deck files; the skill produces decks by cloning that template and overwriting `data/slides.json`.

When editing the renderer/CSS/layouts, propagate changes to **both** the root files and `pku-red-defense-ppt/assets/template/` — they will silently drift otherwise.

Separately, `prompt.md` is a brief for a *different* future project: a manuscript-→-DeepSeek-→-PPT web service (backend + frontend + mock mode + `.env`-based key). **None of that has been built.** If the user asks about API keys, `.env.example`, `src/llm/`, `server/`, or `web/`, they are talking about the prompt.md brief, not the current code — confirm scope before scaffolding.

## Running

Must be served — `index.html` fetches `data/slides.json`, which fails under `file://`:

```bash
python3 -m http.server 8080      # or: npx serve .
# open http://localhost:8080/index.html
```

Workaround without a server: inline the JSON as `window.__PKU_DECK_INLINE = {...}` in the HTML; `runtime.js` prefers it over the fetch.

Export to PDF: browser Print → Save as PDF. `deck-stage.js` ships `@media print` rules that lay one slide per page at design size.

## Architecture

Three layers, loaded in order from `index.html`:

1. **`deck-stage.js`** — a `<deck-stage>` web component. Owns presentation concerns only: 1280×720 design canvas auto-scaled to viewport (letterboxed), keyboard nav (←/→, PgUp/PgDn, Space, Home/End, digits, R to reset), tap-left/right on touch, thumbnail rail (drag-reorder, right-click for skip/move/delete, persists width to localStorage), print stylesheet, `slidechange` CustomEvent. Slides are hidden (not unmounted) so their state survives navigation. Generic — knows nothing about PKU layouts.

2. **`assets/runtime.js`** — the PKU-specific renderer. Fetches `data/slides.json` (or reads `window.__PKU_DECK_INLINE`), then for each entry in `slides[]` picks a function from the `layouts` object keyed by `slide.layout` and injects the resulting HTML into a `<section>` under the stage. Exposes `window.PKU.{deck, layouts, render, init}`. **Adding a new layout = adding a key to `layouts` in this file**, plus matching CSS in `base.css`.

3. **`data/slides.json`** — the entire deck content. Shape: `{ meta, chapters[3–6], slides[] }`. Each slide has a `layout` string (one of: `cover`, `contents`, `section-divider`, `image-analysis`, `chart-analysis`, `timeline`, `theory-cards`, `multi-card`, `framework`, `vs`, `swot`, `method`, `section-text`, `closing`) plus layout-specific fields. See README.md for the field-per-layout table.

Styles split into `assets/theme-pku-red.css` (color/font tokens — `#9A0000` PKU red and friends) and `assets/base.css` (shared chrome + every layout's CSS in one file).

### Shared chrome (content pages)

Every layout except `cover` / `contents` / `section-divider` / `closing` renders via `chrome()` in `runtime.js`, which produces: top-left `sectionTitle` (+ optional English), top-right chapter nav with the active chapter underlined red, big `headline`, bottom-right auto page number (only content pages count — chapter dividers are skipped), bottom-left footer from `meta.school` or per-slide `footerTag`.

### Rich text in JSON strings

`headline` and body-ish fields run through `rich()` in `runtime.js`:

- `**phrase**` → `<em>` (renders as red emphasis)
- `<em>...</em>` → red emphasis
- `<span class="accent">...</span>` → red emphasis
- `<br>` → line break
- Everything else is HTML-escaped (no XSS).

### Image fit modes

`images[].fit` controls object-fit / framing in `imageSlot()`:

| fit | use |
|---|---|
| `cover` (default) | photos, scene shots — cropped to fill |
| `contain` | charts, paper screenshots — no distortion, letterboxed |
| `diagram` | complex flow diagrams — contain + padding |
| `logo` | school/institution marks — contain, framed |
| `fullBleed` | edge-to-edge background |

Optional `focalPoint: {x, y}` (0–1) tunes the crop anchor for `cover`.

## Visual rules (non-negotiable)

These are stated explicitly in README.md §视觉守则 and prompt.md, and must be preserved when editing layouts or CSS:

- 16:9, 1280×720 design canvas; white content pages; PKU red `#9A0000` as the only accent.
- Red is reserved for: nav highlight, ordinal numbers, key phrases, section-divider backgrounds, cover background.
- Cards use light-gray border + white fill, no heavy drop shadows.
- **Do not** turn pages into web landing pages, marketing card stacks, glassmorphism, purple/blue tech gradients, or dark full-bleed hero shots. This is an academic defense deck, not a product pitch.

## Skill bundle (`pku-red-defense-ppt/`)

```
pku-red-defense-ppt/
├── SKILL.md                       # Frontmatter + workflow for the skill
├── references/
│   ├── template-spec.md           # Color/font/canvas/chrome rules + don'ts
│   ├── slides-json-schema.md      # Field-by-field schema for slides.json
│   ├── layout-selection.md        # Content-type → layout decision table
│   ├── image-rules.md             # fit/focalPoint guidance per image type
│   └── visual-reference/          # Thumbnails for QA
├── scripts/
│   ├── create_deck.py             # Copies assets/template/ to <out>/, drops slides.json in
│   └── validate_slides.py         # Checks unknown layouts, missing fields, broken image paths
└── assets/template/               # Mirror of the root deck — index.html, deck-stage.js, assets/, data/
```

Typical skill invocation: write a new `slides.json`, then `python3 scripts/create_deck.py <slides.json> <out-dir>` and `python3 scripts/validate_slides.py <out-dir>/data/slides.json`. The "Validation checklist" in `SKILL.md` is the source of truth for what counts as "done."

The README at the repo root still references `docs/image-adaptation-rules.md` and `docs/next-agent-skill-brief.md` — **those files do not exist**; the equivalents now live under `pku-red-defense-ppt/references/`. Either fix the README links or create the `docs/` files when touching docs.

## Reference material

`_ref/screens/` holds rendered PNGs of each slide (`NN-s.png` / `NN-t.png`) plus `deck-cover-preview.png` and `media-contact-sheet.jpg` — visual ground truth for QA and style comparison, not loaded at runtime. `assets/media/` holds the sample images referenced by the default `slides.json`; replace them when generating a real deck.
