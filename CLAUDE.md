# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Codex maintains a parallel `AGENTS.md` — keep both in sync after non-trivial changes.

## What this is

A web service that turns a Chinese academic manuscript into a downloadable HTML defense/presentation deck. The default visual theme is PKU red, but the pipeline is multi-template: a `template_id` chosen on the frontend picks which renderer + asset bundle is materialized.

```
manuscript + template_id
  → DeepSeek API (or mock)               ← src/llm/
  → generic slide_json                   ← validated by src/schema/
  → template-specific deck HTML          ← src/renderer/* dispatched via src/renderer/dispatch.py
  → materialized deck folder + zip       ← src/exporter/ (copies templates/html-ppt/<id>/ or pku-red-defense-ppt/assets/template/)
  → served at /decks/{id}/index.html and /decks/{id}.zip
```

The repo bundles **four things**, intentionally co-located:

1. **Backend** (`server/app.py`, FastAPI) — runs the LLM→render→export pipeline. Job state is JSON files in `data/jobs/`. Output decks land in `outputs/<id>/` with a sibling `outputs/<id>.zip`.
2. **Frontend** (root `index.html` + `web/`) — branded **`fxt ppt`**. Two-view static app: `#templates` (pick a template, with per-card `预览` button) → `#generate` (paste, generate, poll, download/preview). Pure static HTML/JS. **No API key.**
3. **Deck templates** — 16 total:
   - PKU red at `demo.html` + `deck-stage.js` + `assets/` + `data/slides.json`; export copy under `pku-red-defense-ppt/assets/template/`.
   - 15 imported full-deck templates under `templates/html-ppt/<id>/` (production source the exporter consumes). `html-ppt-templates/` is an older archive — keep the exporter independent of it and never expose it as a public gallery.
4. **Pre-generated previews** (`previews/<id>/`, committed) — one mock-rendered sample deck per template; the only target of the per-card `预览` button. Rebuild via `python scripts/build_previews.py`.

## Live deployment

| Layer | Where | Notes |
|---|---|---|
| Repo (origin/main) | `git@github.com:fxt-gw-pb/pku_ppt_try.git` | SSH only; HTTPS+token is not configured |
| Frontend | `https://fxt-gw-pb.github.io/pku_ppt_try/` (Pages, source: main / root) | root `index.html`; sample PKU deck at `/demo.html`; per-template samples at `/previews/<id>/index.html` |
| Backend | `https://pku-ppt-try.onrender.com` (Render free tier) | `LLM_PROVIDER=deepseek`, key in Render env vars |

Render auto-redeploys on push to `main`. Pages also rebuilds. Both take 1-3 min. User preference: after code/UI changes are verified, commit and push to `origin/main` by default so both surfaces redeploy (still run `git status` / `git remote -v` / `git branch --show-current` first; never commit secrets or runtime artifacts).

## Local dev quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate          # or invoke .venv/bin/<tool> directly

pip install -r requirements.txt    # fastapi, uvicorn, openai, python-dotenv, pydantic

cp .env.example .env               # then edit: LLM_PROVIDER=deepseek + real key
                                   # or leave LLM_PROVIDER=mock for keyless dev

# CLI (mock, no key)
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
# CLI (non-default template)
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo
# Rebuild the committed per-template sample decks under previews/
python scripts/build_previews.py

# Backend + frontend together (uvicorn mounts web/ at "/", previews/ at /previews/)
uvicorn server.app:app --reload --port 8787
# then http://127.0.0.1:8787/
```

`examples/input.md` is a ~800-char defense abstract — cheap for live DeepSeek E2E tests.

## Repo layout

```
.
├── index.html                    # Frontend (Pages root). Two-view app. Refs web/style.css + web/app.js.
├── demo.html                     # Original PKU sample deck shell. Served at /demo.html on Pages.
├── deck-stage.js                 # PKU template's web component. Used by demo.html + every PKU-rendered deck.
├── assets/{base,theme-pku-red}.css, runtime.js, media/   # PKU template assets (root copy; mirrored under pku-red-defense-ppt/)
├── data/slides.json              # Sample PKU slides.json loaded by demo.html
├── 收款码/537a8a...jpg            # Donation QR image; FastAPI mounts /收款码 for local preview.
│
├── pku-red-defense-ppt/          # PKU skill bundle; assets/template/ is what the exporter copies for pku-red decks.
├── templates/html-ppt/<id>/      # Production source for the 15 imported full-deck templates.
│   ├── <id>/{manifest.json,style.css}   # per-template metadata + scoped CSS (.tpl-<id>)
│   └── shared/assets/                   # base.css (incl. @media print), fonts.css, runtime.js, animations/
├── html-ppt-templates/           # Older imported archive. Exporter is independent; not a public gallery.
│
├── previews/<id>/                # Pre-generated sample decks (one per template). Committed. Built by scripts/build_previews.py.
│
├── src/                          # Python pipeline (importable as `src.llm`, `src.renderer`, ...).
│   ├── llm/{deepseek,mock}.py    # provider dispatch. Entry: generate() / generate_slide_json().
│   ├── schema/__init__.py        # validate the GENERIC slide_json (LLM output).
│   ├── renderer/__init__.py      # compile_to_pku(): generic → PKU slides.json (layout heuristics).
│   ├── renderer/dispatch.py      # render_for(slug, generic, ...) — selects the dedicated renderer.
│   ├── renderer/<template>.py    # 15 dedicated renderers (pitch_deck, weekly_report, xhs_post, …).
│   ├── renderer/html_ppt_generic.py    # generic fallback (currently unused — every template has its own renderer).
│   ├── templates/registry.py     # template registry: used by API (/api/templates), CLI (--template), and frontend.
│   └── exporter/__init__.py      # export_deck (copy template + write data/slide.json) + zip_deck.
├── scripts/generate.py           # CLI wrapper. --template <id> selects renderer + asset bundle.
├── scripts/build_previews.py     # Materializes one mock deck per template into previews/<id>/; strips unused PKU stock media.
├── server/app.py                 # FastAPI: /api/health, /api/templates, /api/jobs (POST/GET),
│                                 #         /api/jobs/:id/{download,preview} (legacy/curl only).
│                                 # Static mounts: /decks → outputs/, /previews → previews/, /收款码 → 收款码/, / → web/.
├── web/                          # Local-dev frontend source. Root index.html duplicates this for GitHub Pages.
│                                 # web/style.css and web/app.js are canonical; root index.html refs them via web/... paths.
│
├── outputs/                      # (gitignored) generated decks + zips
├── data/jobs/                    # (gitignored) per-job state JSON
│
├── .env.example                  # public template only (placeholder key)
├── .env                          # (gitignored) real local key, LLM_PROVIDER=deepseek
├── requirements.txt
├── README.md, CLAUDE.md, AGENTS.md, prompt.md
└── _ref/                         # PNG reference shots of PKU template slides (not loaded at runtime).
```

## Architecture / data flow

### The two schemas (the most important thing to understand)

The LLM produces a deliberately narrow shape — see `src/schema/__init__.py` and the system prompt in `src/llm/deepseek.py`:

```json
{
  "title": "演示主标题",
  "subtitle": "...",
  "slides": [
    { "type": "cover | contents | section | content | closing",
      "title": "...",
      "bullets": ["..."],
      "layout": "cards"?,
      "section"?, "notes"?, "image_prompt"?, "chart_suggestion"?,
      // optional layout-specific structured fields (any may be absent):
      "stat"?:    { "value", "label", "sub?", "delta?" },
      "quote"?:   { "text", "author?" },
      "compare"?: { "left": {"title", "points":[]}, "right": {"title", "points":[]} },
      "kpis"?:    [ { "label", "value", "delta?", "status?: good|warn|bad" } ],
      "steps"?:   [ { "when?", "title", "body?" } ],
      "columns"?: [ { "title", "body", "kicker?" } ]
    }
  ]
}
```

The schema validator (`validate_slide_json`) only enforces shape — when a structured field is absent, every renderer falls back to parsing `bullets` heuristically. `KNOWN_LAYOUTS` is the union of `KNOWN_PKU_LAYOUTS` (the 14 PKU runtime layouts) and `KNOWN_GENERIC_LAYOUTS` (the 11 html-ppt-facing names: `cards / bullets / two-column / three-column / kpi-grid / stat-highlight / comparison / pros-cons / big-quote / timeline / process-steps`).

The PKU runtime (`assets/runtime.js`) needs much richer per-layout fields: `headline`, `images[]`, `items[]`, `cards[]`, `nodes[]`, `chapterIndex`, etc. — full grammar in `pku-red-defense-ppt/references/slides-json-schema.md`. Each html-ppt template has its own dedicated renderer that emits a complete `index.html` directly (no per-template slides.json schema).

### LLM layout selection — anti-fabrication rules (in the system prompt)

The DeepSeek prompt explicitly tells the model not to force a layout when the manuscript lacks the underlying material. Don't loosen these when editing the prompt:

- **`stat-highlight`** and **`big-quote`** each: **at most 1 per deck, and must be omittable**. If the manuscript has no single load-bearing number / no quotable line, do not synthesize one.
- **`kpi-grid`** requires ≥3 real quantitative metrics already present in the source.
- **`comparison` / `pros-cons`** require both sides to have 2-4 distinct points from the source.
- **`timeline`** requires actual time anchors (quarters, years, months); no fabricating `2024 Q3`-style markers.
- **`process-steps`** requires steps with dependency order, not a flat bullet list.
- Default fallbacks are `cards` and `bullets` — a deck that is 70% `cards` is fine.

Renderers also accept the legacy PKU layout names (`multi-card`, `theory-cards`, `method`, `section-text`, `vs`, `swot`, `framework`) for backwards compatibility; `layouts._LAYOUT_ALIASES` normalizes them to the generic set.

### Dispatch & rendering

`src/renderer/dispatch.py` maps a template slug to its render function. **All 15 html-ppt templates have dedicated renderers** under `src/renderer/<template>.py`; the `html_ppt_generic.py` fallback exists for safety but every registered template overrides it. PKU is handled separately by `src/renderer/__init__.compile_to_pku()` + the PKU runtime.

#### Shared helpers — `src/renderer/layouts.py`

Every html-ppt renderer imports `from . import layouts as L`. This module owns the boilerplate so each template file can focus on its own chrome (cover, contents, section dividers, brand-specific decorations):

- **Text**: `L.esc(value)`, `L.rich(value)` (`**phrase**` → `<em>`, `<br>` survives, everything else escaped), `L.rich_grad(value)` (same but wraps emphasis in `<span class="gradient-text">` for gradient-driven templates), `L.split_kv("标题：正文")` → `(head, body)`.
- **Planning**: `L.planned_slides(generic)` returns ordered `[(kind, slide), ...]` (always synthesizes a `cover` at index 0 and a `closing` at the end); `L.chapter_titles(generic)` collects every `type=section` title.
- **Structured-field extractors**: `L.get_columns / get_kpis / get_stat / get_quote / get_compare / get_steps / get_bullets`. Each returns the LLM-provided structured field when present, otherwise builds a best-effort fallback from `bullets` so the layout still renders.
- **Layout normalization**: `L.normalize_layout(layout, bullets_count)` collapses aliases (`multi-card → cards`, `theory-cards → cards`, `method → process-steps`, `section-text → bullets`, `vs/swot → comparison`, `framework → process-steps`, `image-analysis → cards`, `chart-analysis → kpi-grid`, `quote-card → big-quote`) and picks a sensible default when `layout` is missing.
- **Inner-HTML fragments**: `L.render_inner(layout, slide)` dispatches to `inner_cards / inner_bullets / inner_columns / inner_kpi_grid / inner_stat / inner_comparison / inner_quote / inner_timeline / inner_process_steps`. Each returns the *body* HTML of one content slide using a small set of stable class names (`.content-cards`, `.content-bullets`, `.content-cols`, `.content-kpis`, `.content-stat`, `.content-vs[.pc]`, `.content-quote`, `.content-timeline`, `.content-steps`) plus shared primitives `.card`, `.grid g2|g3|g4`, `.pill`, `.gradient-text`.

The renderers compose: their own brand chrome (kicker, headline, section number, decorative backdrops) + `L.render_inner(...)` + their own footer.

#### Shared content-layout CSS — `templates/html-ppt/shared/assets/base.css`

`base.css` now ships default rules for every `.content-*` class above so a new template gets all 11 layouts for free. Per-template `style.css` overrides the visual identity by retheming the CSS custom properties (`--accent`, `--accent-2`, `--accent-3`, `--surface`, `--surface-2`, `--text-1`, `--text-2`, `--text-3`, `--grad`, `--border`) — only override the `.content-*` class itself when the default tokens can't carry the look (e.g. dark templates needing different contrast on `.content-vs` borders). The shared `@media print` block (page-size, color-adjust, overflow reset) also lives here.

#### `compile_to_pku()` — generic → PKU bridge

`src/renderer/__init__.compile_to_pku()` is the PKU-only equivalent of the html-ppt renderers:

- **Chapter detection**: walks slides; every `type=section` slide contributes a chapter title. If 3-6 found, uses those; else falls back to the 5 default PKU chapters.
- **Layout resolution** for `type=content`: `_resolve_pku_layout(slide)` takes the LLM's `layout` hint, keeps it if it's already a PKU layout, otherwise translates via `_GENERIC_TO_PKU` (`cards → multi-card`, `bullets → section-text`, `kpi-grid → multi-card` rendered as value-led cards, `stat-highlight → section-text`, `comparison/pros-cons → vs`, `process-steps → method`, `big-quote → section-text`, `timeline → timeline`). No hint → bullet-count heuristic.
- **Structured-field → PKU shape**: `_kpi_cards`, `_theory_cards_from_columns`, `_vs_from_compare`, `_method_from_steps`, `_timeline_from_steps`, `_quote_blocks`, `_stat_blocks` consume the same `L.get_*` extractors and emit PKU-runtime fields (`cards`, `methods`, `steps`, `leftItems`/`rightItems`, `nodes`, `blocks`).
- **Bullet → card fallback**: bullets shaped as `"title: body"` / `"标题：正文"` split into card title + body; otherwise auto-numbered.
- Always inserts a `cover` at start and `closing` at end if the LLM omitted them.
- PKU layouts `image-analysis` / `chart-analysis` fall through to `section-text` because we have no real image assets to render — extend the LLM contract first, then add a real branch in `_render_content()`.

### Template registry

`src/templates/registry.py` is the single source of truth for which templates exist, which renderer they use, which asset directory the exporter copies, and what the frontend should advertise.

- API: `GET /api/templates` returns the registry via `public_dict()`.
- `public_dict()` deliberately **hides** `preview_url` and maps internal engines to public-facing display values (`classic` or `template`). Keep public API display data free of skill/source names (`html-ppt`, `pku-red-defense-ppt`, etc.).
- Current `template_id` values: `pku-red` (default) + 15 imported full-deck templates (`xhs-white-editorial`, `graphify-dark-graph`, `knowledge-arch-blueprint`, `hermes-cyber-terminal`, `obsidian-claude-gradient`, `testing-safety-alert`, `xhs-pastel-card`, `dir-key-nav-minimal`, `pitch-deck`, `product-launch`, `tech-sharing`, `weekly-report`, `xhs-post`, `course-module`, `presenter-mode-reveal`).
- Avoid user-visible `html-ppt` / skill-origin wording in the website, API display data, or generated deck copy. Internal folder names and engine strings can stay where compatibility requires.

### Job lifecycle (backend)

```
POST /api/jobs (template_id, manuscript)  → write data/jobs/{id}.json (status=pending), spawn daemon thread
   daemon thread:
     run LLM → validate generic → dispatch to renderer-for-template → exporter copies the template bundle → zip
     update job JSON to status=done with download_url + preview_url
GET  /api/jobs/{id}                       → read job JSON (strips traceback for the response)
GET  /api/templates                       → registry list for the frontend
GET  /decks/{id}.zip                      ← what download_url points at (StaticFiles)
GET  /decks/{id}/index.html               ← what preview_url points at
GET  /api/jobs/{id}/download              ← legacy/curl; FileResponse — broken under Render+Origin, see quirks
GET  /api/jobs/{id}/preview               ← legacy/curl; 307 to /decks/{id}/index.html
GET  /previews/{template_id}/index.html   ← committed per-template sample deck; the only entry point for the 预览 button
GET  /收款码/...                           ← static mount for the donation QR image
```

The job runner is still a daemon thread inside the FastAPI process — no queue. Fine for the free-tier MVP; not for production load.

### Job phase / progress fields

While a job is `running`, `_run_job` writes two extra fields at each pipeline boundary:

- `phase`: `"llm"` → `"render"` → `"zip"` → `"done"`
- `progress`: `5` → `60` → `90` → `100` (coarse, informational; the frontend ignores the number)

The frontend (`web/app.js`) reads only `phase` and renders a one-line spinner + label (`AI 正在生成大纲...` / `正在渲染幻灯片...` / `正在打包网页...`). The `progress` integer is kept in the JSON for debugging / future use; do not surface it in the UI without a re-design (the LLM phase dominates wall time and any %-bar visually freezes there).

### Post-LLM layout diversification

`src/llm/__init__.generate_slide_json` calls `src.renderer.diversify.diversify_layouts(raw)` after validation. The pass rewrites the third-and-beyond slide in any run of 3+ consecutive content slides with the same `layout`, choosing a content-fit alternative — it never invents a structured field (`kpis`/`stat`/`quote`/etc.) to justify a flashier layout. If you're debugging "why did this slide end up as `two-column` when the LLM emitted `cards`?", that's the answer.

Every materialized deck (both PKU and html-ppt) also gets a `data/slide.json` (singular) alongside its real assets — that's the raw generic LLM JSON dumped by `scripts/generate.py` for debugging / re-runs. Don't confuse it with PKU's `data/slides.json` (plural), which is the rich PKU-runtime format consumed by `runtime.js`. html-ppt decks only have `slide.json`; PKU decks have both.

## Frontend (two-view static app)

The public UI exposes exactly two views. Do not re-add a third.

- `#templates` — select a template. Cards have two actions: `使用模板` (red filled, selects the template and jumps to `#generate`) and `预览` (light outline, opens `previews/<template_id>/index.html` in a new tab). The 预览 link is the **only** path to a preview; do not re-introduce a separate template-library page.
- `#generate` — paste manuscript, generate, poll, download/preview the result.

Per-template sample decks live under `previews/` and are committed to the repo. Regenerate them with `python scripts/build_previews.py` whenever you change a renderer, the LLM mock, or a template's bundled assets. GitHub Pages serves them as `previews/<id>/index.html`; FastAPI mounts the same path at `/previews/` for local dev. Do not link to previews from anywhere else (no nav, no list page, no embed) — the only access point is the per-card 预览 button.

Removed and not coming back without an explicit ask: `template-preview.html`, `web/template-preview.html`, `html-ppt-templates/index.html`, `html-ppt-templates/templates/full-decks-index.html`. `server/app.py` must not mount `/html-ppt-templates` for public browsing.

UI copy that is canonical (keep both root `index.html` and `web/index.html` in sync):

- Brand string: **`fxt ppt`**.
- Donation note, on both views, with a clickable `.donation-trigger` opening a shared QR modal backed by `收款码/537a8a731804791d569387f56522fa2a.jpg`:
  > 该网页暂时免费使用，生成 PPT 需要一定的 API tokens 花费，该费用由作者承担，请勿滥用，如果感到有用，也欢迎 打赏给作者 <=1 元的奖赏~
- Generate view warning:
  > PPT 生成约需 30s–2min，生成过程中切勿刷新页面，刷新页面也会丢失您的既往文件生成记录。
- Export wording in the public UI: `网页包和 PDF` (not `HTML/PPTX`, except when explicitly explaining that PPTX is unsupported).
- Generated-job action buttons are high contrast: **`进入预览页`** red filled, **`下载网页包`** light filled with red text/border.

### Two `index.html` files (don't delete one assuming it's a duplicate)

- **Root `index.html`** — GitHub Pages serves it at the bare site URL. References `web/style.css` and `web/app.js`. Has a link to `demo.html`.
- **`web/index.html`** — local uvicorn serves it at `/` via `app.mount("/", StaticFiles(directory="web"))`. References sibling `style.css` and `app.js`.

Keep them in sync when editing the UI, adjusting paths as needed.

### Cold-start warmup

Render's free tier sleeps after 15 min idle, so the first `/api/jobs` hit waits ~30s. `web/app.js` fires a `/api/health` ping in `route()` whenever the user enters `#generate`, self-throttled to once per 60s. The point is to hide the cold-start cost behind the user's paste/read time; don't remove this without first solving the underlying sleep behavior.

## Per-deck "导出 PDF" button

Every generated deck (and every committed preview) carries a floating **导出 PDF** pill button at the bottom-right that calls `window.print()`. Save-as-PDF in the print dialog produces a one-page-per-slide PDF at native 1280×720.

- html-ppt decks: injected by `templates/html-ppt/shared/assets/runtime.js` and hidden in print via `@media print` rules in `templates/html-ppt/shared/assets/base.css`. Keyboard shortcut **P**.
- PKU decks: injected by `pku-red-defense-ppt/assets/template/assets/runtime.js` (also mirrored to root `assets/runtime.js`). PKU's print rules already live inside `deck-stage.js`'s shadow-DOM `@media print` block; the `@page` size is set via the inline `<style id="deck-stage-print-page">` that `connectedCallback` injects into `<head>` (the at-rule has no effect inside shadow DOM). Keyboard shortcut **P**.

The shared print stack:

- `@page { size: 1280px 720px; margin: 0; }` — fixed-size landscape sheet matching the canvas
- `.deck { overflow: visible; position: static }` — drop the screen-mode `overflow:hidden` so every slide reaches the printer (the previous CSS clipped everything past the first slide)
- `.slide { position: relative; width: 1280px; height: 720px; opacity: 1; page-break-after: always; break-after: page; overflow: hidden }`
- `* { -webkit-print-color-adjust: exact; print-color-adjust: exact }` — so dark backgrounds, gradients, and accent fills survive printing
- Chrome (`.progress-bar`, `.notes-overlay`, `.overview`, `.pdf-export-btn`) is hidden in print

Verified in headless Chrome (`--print-to-pdf`): both `pitch-deck` and `pku-red` produce 14-page PDFs at 960×540 PDF points (= 1280×720 CSS px at 96/72 DPR), with all backgrounds intact.

### Per-template print overrides

`xhs-post` is a 3:4 portrait template (slide is 810×1080), not 16:9. Its `style.css` ends with an `@media print` block that re-sets `@page size: 810px 1080px` and overrides `.slide` to 810×1080. The override works because per-template `style.css` is loaded **after** the shared `base.css` (see the renderer header order in `src/renderer/xhs_post.py`). When adding another non-16:9 template, follow the same pattern instead of editing the shared base.

## In-deck field-edit panel + re-export

Every generated deck (and every committed preview) carries an `✎ 修改字段` toggle (bottom-right, above the PDF button) that opens a 360px sidebar with verbatim find/replace, undo, clear-all, and `⇩ 下载修改后的网页包`. Both runtimes (`templates/html-ppt/shared/assets/runtime.js` and `pku-red-defense-ppt/assets/template/assets/runtime.js`) implement the same panel; the PKU copy is mirrored to root `assets/runtime.js`.

Persistence:

- Each successful replace is appended to `localStorage["fxt-ppt-deck-edits:" + location.pathname]` as `{find, replace, slideIndex, ts}`. The pathname key means a generated deck (`/decks/abc/index.html`) and a preview (`/previews/abc/index.html`) keep separate edit histories.
- On runtime init, every saved op is replayed **only against the slide at its recorded `slideIndex`** — so an edit on slide 3 doesn't bleed into slide 7 just because they share a substring. Ops written before `slideIndex` was tracked fall back to whole-deck replay.
- Undo pops the most recent op from storage so a refresh agrees with the visible state.

Re-export (`⇩ 下载修改后的网页包`):

- Only enabled on URLs that match `/decks/<id>/index.html` (the only place we can derive `/decks/<id>.zip`). Previews and `file://` get a clear error.
- Lazy-loads JSZip from a **vendored** copy at `assets/jszip.min.js` (shipped with every deck via the exporter), falling back to `cdn.jsdelivr.net` only if the local file is missing. Don't switch back to CDN-first — the local copy makes re-export work offline and behind firewalls.
- Rewrites `index.html` in the zip with the current DOM (stripped of injected chrome: `.edit-panel`, `.pdf-export-btn`, `.nav-arrows`, etc.). For PKU decks, also rewrites `data/slides.json` by applying each saved op to the corresponding slide object (so the edits survive a fresh open — PKU decks re-render from JSON on every load and would otherwise wipe DOM edits).

When changing the panel, keep the PKU and html-ppt runtimes feature-parity. After editing either, run `python scripts/build_previews.py` so the committed sample decks ship the new behavior.

## Typography rule (CJK-first)

All html-ppt template stylesheets follow a unified scale tuned for Chinese titles on a 1280×720 canvas:

- Cover headline (.h1 / .xp-h1 / .xw-title / .hc-h1 / .gd-h1 / .kb-h1 / .oc-h1 / .ts-h1 / .dk-h0 …): **56–74px**, line-height ~1.16, near-zero `letter-spacing`, `max-width:1040–1080px`, `word-break:break-word`.
- Slide title (.h2 and equivalents): **40–48px** with line-height ~1.2.
- Decorative watermark numerals (`.section-num`, `.dk-big`, `.kb-big-num`, `.hc-big`, `.gd-big`, `.oc-big`, `.mega`): capped around **144–180px**, positioned as backdrops.
- Body / lede: 18–22px, card body 14–16px, kicker / footer 11–13px.

Each headline rule keeps a `:lang(en)` override (`html.lang === "en"`, or any element with `lang="en"`) that restores the original Latin-keynote sizes (74–96px). So CJK titles never overflow, while Latin titles keep their punch.

When adding a new template or editing typography:

- Don't use negative `letter-spacing` more aggressive than `-0.5px` on the default CJK rule — it crushes adjacent glyphs.
- Always set `max-width` on hero headlines that can wrap.
- If you change a `.slide > *` rule, exclude decorative absolutely-positioned children (e.g. `.section-num`, `.cover-bg`, `.cover-blob`) so they don't get forced into the normal flow.

## PKU template specifics (preserved across PKU-rendered decks)

### Shared chrome (content pages)

Every layout except `cover` / `contents` / `section-divider` / `closing` renders via `chrome()` in `assets/runtime.js`: top-left `sectionTitle` (+ optional English), top-right chapter nav with the active chapter underlined red, big `headline`, bottom-right auto page number (only content pages count — chapter dividers are skipped), bottom-left footer from per-slide `footerTag`.

Current PKU-template behavior (post codex cleanup — do not re-add the removed pieces unless explicitly asked):

- The cover page **no longer** renders the old white metadata box for `汇报人`, `指导老师`, or `学院专业`.
- Content slides **no longer** auto-render `meta.school` in the lower-left footer (per-slide `footerTag` still works).
- `DEFAULT_META`, root `data/slides.json`, and mirrored `pku-red-defense-ppt/assets/template/data/slides.json` no longer contain `X X X`, `X X X 教授`, or `X X 学院 · X X 专业` placeholders.

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

Optional `focalPoint: {x, y}` (0–1) tunes the crop anchor for `cover`. Anything with readable text (charts, screenshots, diagrams) must use `contain` or `diagram`, not cropped `cover`.

## Visual rules (PKU-only, non-negotiable for that template)

These apply **only to the `pku-red` template**. The 15 html-ppt templates each carry their own theme and may use dark backgrounds, gradients, neon, sticker UI, etc.

- 16:9 / 1280×720 canvas; white content pages; PKU red `#9A0000` is the only strong accent.
- Red is reserved for: nav highlight, ordinal numbers, key phrases, section-divider backgrounds, cover/closing backgrounds.
- Cards: light-gray border + white fill, no heavy drop shadows.
- **Not** a marketing page. No glassmorphism, purple/blue tech gradients, dark hero pages, or landing-page card stacks.

Source of truth for PKU: `pku-red-defense-ppt/references/template-spec.md`, `layout-selection.md`, `image-rules.md`, `slides-json-schema.md`.

## Render quirks (the deploy-time gotchas)

### Edge routing weirdness with FileResponse + Origin

A `GET /api/jobs/{id}/download` request with `Origin: https://fxt-gw-pb.github.io` returns:

```
HTTP/2 404
content-type: text/plain
content-length: 10
x-render-routing: no-server
```

— bare "Not Found" from Render's edge, never reaching uvicorn. The same path **without** the Origin header reaches uvicorn fine and returns the zip. The same bytes served via `/decks/{id}.zip` (Starlette `StaticFiles`) work with Origin set.

This is why the API's `download_url` / `preview_url` fields point at `/decks/...` instead of `/api/jobs/{id}/...`. The `/api/jobs/{id}/{download,preview}` endpoints still exist for curl/CLI (no Origin) but the frontend doesn't use them. **Do not switch the frontend back to `/api/jobs/{id}/download`.** Root cause is between Render's edge layer and FastAPI's `FileResponse`; we worked around rather than diagnosed.

### Ephemeral filesystem

Every deploy / cold-start / restart wipes `outputs/` and `data/jobs/`. A job's zip is only guaranteed available immediately after it finishes. For persistence: attach a Render disk (paid) or move outputs to S3/R2 and return signed URLs.

`previews/` is **committed** and survives restarts — Pages serves it natively, FastAPI mounts it. Don't put generated user decks there.

### Cold start

After 15 min idle, free tier spins down. Next request waits ~30 s. The frontend's first `/api/health` poll may time out — the page silently no-ops on failed health. The user sees the error when they click Generate.

## CORS

`server/app.py` allowlist: `https://fxt-gw-pb.github.io` + localhost dev ports (8787, 8090). Override with `CORS_ORIGINS="a,b,c"` env var. **Do not loosen back to `["*"]`** without adding rate limits — DeepSeek calls cost money and your Render URL is technically discoverable via `web/app.js`.

## API key handling (zero compromises)

- `.env` (gitignored) holds the real local key. `.env.example` always has the placeholder string.
- Render holds the production key in Settings → Environment.
- DeepSeek API calls default to `DEEPSEEK_MODEL=deepseek-v4-pro`, coerce legacy `deepseek-chat` / `deepseek-reasoner` env values to `deepseek-v4-pro`, and explicitly send `extra_body={"thinking":{"type":"disabled"}}`; do not enable thinking mode unless explicitly requested.
- Never print or inspect `.env` unless the user explicitly asks.
- The frontend never sees the key. `web/app.js` only knows the backend's public URL.
- If a real key ever lands in a tracked file, the key is **compromised the moment that commit is pushed** — rotate immediately on the DeepSeek dashboard, even after force-pushing to strip the commit. GitHub keeps detached commits reachable for a while after force-push.

## Local-dev gotchas

- **HTTP proxy**: this machine has `http_proxy=127.0.0.1:7897` in the shell. `curl http://127.0.0.1:8787/…` will 502 through the proxy. Use `curl --noproxy 127.0.0.1 …` for local-loopback hits.
- **curl on PATH**: `which curl` → `/opt/anaconda3/bin/curl`. Some compound shell forms (e.g. `eval` with `for` loops through the Bash tool) strip anaconda from PATH and produce "command not found: curl". Use `/usr/bin/curl` explicitly when scripting.
- Always preview generated decks over HTTP (uvicorn), not `file://`, because `runtime.js` fetches `data/slides.json`.
- Background uvicorn processes from the harness may report a `failed` status when killed — that's expected on `pkill -9`, not an error.

## Template sync rule (PKU)

The PKU red visual template exists in two mirrored places:

- Root runtime used by `demo.html`: `deck-stage.js`, `assets/base.css`, `assets/runtime.js`, `assets/theme-pku-red.css`, `assets/jszip.min.js`, `data/slides.json`.
- Skill/export template used by generated PKU decks: `pku-red-defense-ppt/assets/template/...`.

If any of those files change, update **both** copies and verify they still match:

```bash
cmp -s deck-stage.js pku-red-defense-ppt/assets/template/deck-stage.js
cmp -s assets/runtime.js pku-red-defense-ppt/assets/template/assets/runtime.js
cmp -s assets/base.css pku-red-defense-ppt/assets/template/assets/base.css
cmp -s assets/theme-pku-red.css pku-red-defense-ppt/assets/template/assets/theme-pku-red.css
cmp -s assets/jszip.min.js pku-red-defense-ppt/assets/template/assets/jszip.min.js
cmp -s data/slides.json pku-red-defense-ppt/assets/template/data/slides.json
```

The exporter copies `pku-red-defense-ppt/assets/template/`, not the root template files. Imported full-deck templates live under `templates/html-ppt/`; keep the exporter independent from `html-ppt-templates/`, and do not expose that folder as a public gallery.

## Validation checklist

After backend / pipeline / renderer changes, run at least:

```bash
# generic + PKU validate
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
python pku-red-defense-ppt/scripts/validate_slides.py outputs/demo/data/slides.json

# spot-check a non-PKU template
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo

# regenerate the committed sample decks (if renderers/CSS changed)
python scripts/build_previews.py
```

For API changes, start uvicorn and:

```bash
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/health
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/templates
```

For PDF/print regressions, render one deck with headless Chrome and count pages:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --print-to-pdf=/tmp/deck.pdf --print-to-pdf-no-header \
  --virtual-time-budget=8000 \
  "http://127.0.0.1:8787/previews/pitch-deck/index.html"
# expect ~14 pages at 960×540 PDF points (= 1280×720 CSS px)
```

## Important files

- `AGENTS.md` — Codex handoff notes; keep aligned with this file.
- `README.md` — user-facing setup and usage docs.
- `prompt.md` — original build brief.
- `.env.example` — public environment template.
- `server/app.py` — FastAPI API, job lifecycle, CORS, static mounts (`/decks`, `/previews`, `/收款码`, `/`).
- `web/app.js` — keyless frontend, GitHub Pages backend URL selection, polling, per-card `预览` link.
- `web/style.css` — frontend styling, including `.text-button.ghost` for the 预览 button.
- `src/llm/deepseek.py` — DeepSeek OpenAI-compatible provider and strict JSON prompt.
- `src/llm/mock.py` — deterministic provider for keyless E2E tests.
- `src/schema/__init__.py` — generic LLM output validator.
- `src/renderer/__init__.py` — generic-to-PKU compiler (`compile_to_pku`).
- `src/renderer/dispatch.py` — html-ppt slug → render function map.
- `src/renderer/layouts.py` — shared helpers consumed by every html-ppt renderer and by `compile_to_pku`: `planned_slides`, `chapter_titles`, `normalize_layout`, `render_inner`, structured-field extractors.
- `src/renderer/<template>.py` — 15 dedicated renderers (pitch_deck, weekly_report, hermes_cyber_terminal, etc.).
- `src/renderer/html_ppt_generic.py` — generic fallback (kept for safety; not currently used).
- `src/exporter/__init__.py` — copy template, write `data/slide.json`, zip deck.
- `src/templates/registry.py` — template registry used by API, CLI, and frontend.
- `scripts/generate.py` — single-deck CLI entrypoint.
- `scripts/build_previews.py` — rebuild all per-template `previews/<id>/` sample decks.
- `templates/html-ppt/shared/assets/base.css` — shared deck CSS (incl. `@media print` rules driving PDF export, default content-layout styles, edit-panel + nav-arrows styles).
- `templates/html-ppt/shared/assets/runtime.js` — keyboard runtime, presenter mode, **导出 PDF** floating button injection, **field-edit panel** (localStorage-persisted per-slide edits + JSZip-based re-export).
- `templates/html-ppt/shared/assets/jszip.min.js` — vendored JSZip (3.10.1), shipped with every html-ppt deck so re-export works offline. CDN is fallback only.
- `pku-red-defense-ppt/assets/template/assets/runtime.js` — PKU runtime, also injects 导出 PDF and the edit panel (mirrored to root `assets/runtime.js`).
- `pku-red-defense-ppt/assets/template/assets/jszip.min.js` — vendored JSZip for PKU decks (mirrored to root `assets/jszip.min.js`).
- `src/renderer/diversify.py` — post-LLM pass that breaks runs of 3+ same-layout slides with content-fit alternatives (called from `src/llm/__init__.generate_slide_json`).
- `pku-red-defense-ppt/scripts/validate_slides.py` — validator for PKU runtime JSON.
- `pku-red-defense-ppt/scripts/create_deck.py` — standalone skill materializer.

## Extending

- **New generic layout (consumed by every html-ppt template)**: (a) add the layout name to `KNOWN_GENERIC_LAYOUTS` in `src/schema/__init__.py` and, if it needs a new structured field, extend `_check_structured_fields`; (b) describe the layout (+ pre-conditions, anti-fabrication rules) in the DeepSeek system prompt in `src/llm/deepseek.py`; (c) add a `get_<field>` extractor and an `inner_<layout>` fragment in `src/renderer/layouts.py`, then route it in `render_inner`; (d) add a default `.content-<layout>` rule in `templates/html-ppt/shared/assets/base.css` using only the shared CSS custom properties; (e) optionally extend `compile_to_pku()` so PKU benefits too.
- **New PKU layout from LLM**: (a) extend the system prompt in `src/llm/deepseek.py` so the model emits the layout-specific fields; (b) add a branch in `_render_content()` in `src/renderer/__init__.py`; (c) confirm the layout name is in `KNOWN_PKU_LAYOUTS` of `src/schema/__init__.py`.
- **New full-deck template**:
  1. Drop the asset bundle under `templates/html-ppt/<id>/` (`manifest.json` + scoped `style.css`).
  2. Add `src/renderer/<id_slug>.py` with a `render_<slug>(generic)` function returning a complete `index.html`. Use `L.planned_slides` / `L.normalize_layout` / `L.render_inner` from `src/renderer/layouts.py` for the content-page body so the template inherits all 11 generic layouts for free; only write bespoke HTML for the brand chrome (cover, contents, section divider, closing) and any layout you want to override.
  3. Follow the CJK type hierarchy rule above (cover h1 56–74px CJK / 74–96px `:lang(en)`).
  4. Register it in `src/renderer/dispatch.py` and `src/templates/registry.py`.
  5. Run `python scripts/build_previews.py` to add a committed sample under `previews/<id>/`.
- **Server-side PDF (instead of the current client-side print button)**: add Playwright; in `_run_job()` after the zip step, launch headless Chromium, navigate to the deck's `index.html`, `page.pdf(landscape=True, width="1280px", height="720px")`. Add a `pdf_url` field on done jobs.
- **PPTX export**: harder — either re-implement each layout via `python-pptx`, or use LibreOffice headless to convert the HTML deck. Layout-specific work for either path.
- **Object storage for outputs**: replace `OUTPUT_DIR` writes with `boto3` calls to S3/R2; return signed URLs in `download_url`. The `/decks` static mount becomes obsolete and the Render ephemeral-filesystem problem goes away.
- **Production queueing**: replace daemon threads with Redis/RQ/Celery or another job system.

## What's not built (deliberate MVP scope)

- No persistence (Render's ephemeral disk; no DB; `previews/` is the only stable served folder and it's committed).
- No auth, no rate limits, no per-user quotas.
- No queue (job runner is a daemon thread inside the FastAPI process).
- PDF export is **client-side** (`window.print()` + `@media print` CSS, plus the 导出 PDF button). No server-side PDF/PPTX rendering.
- No image generation (`image_prompt` LLM field is captured but unused).
- No PR-style flow / preview-before-publish for user-generated decks.
