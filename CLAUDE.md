# CLAUDE.md

Guidance for Claude Code on this repo. Codex has a parallel `AGENTS.md` — keep both in sync after non-trivial changes.

## What this is

A web service that turns a Chinese academic manuscript into a downloadable HTML deck. Multi-template: a `template_id` picks the renderer + asset bundle.

```
manuscript + template_id
  → DeepSeek (or mock)         ← src/llm/
  → generic slide_json         ← validated by src/schema/
  → template-specific HTML     ← src/renderer/* via src/renderer/dispatch.py
  → deck folder + zip          ← src/exporter/ copies templates/html-ppt/<id>/ or pku-red-defense-ppt/assets/template/
  → /decks/{id}/index.html and /decks/{id}.zip
```

Four co-located concerns:

1. **Backend** (`server/app.py`, FastAPI). Job state in `data/jobs/`; output decks in `outputs/<id>/` + `outputs/<id>.zip`.
2. **Frontend** (root `index.html` + `web/`), branded **`fxt ppt`**. Two-view static app, no API key.
3. **Templates** — 16 total: PKU red (root `demo.html` + `deck-stage.js` + `assets/`; export copy at `pku-red-defense-ppt/assets/template/`) plus 15 imported decks under `templates/html-ppt/<id>/`. `html-ppt-templates/` is an older archive — exporter stays independent; never expose it as a public gallery.
4. **Previews** (`previews/<id>/`, committed) — one mock-rendered deck per template, the only target of the per-card `预览` button. Rebuild via `python scripts/build_previews.py`.

## Live deployment

| Layer | Where | Notes |
|---|---|---|
| Repo | `git@github.com:fxt-gw-pb/pku_ppt_try.git` | SSH only |
| Frontend | `https://fxt-gw-pb.github.io/pku_ppt_try/` | Pages, source: main / root |
| Backend | `https://pku-ppt-try.onrender.com` | Render free tier; `LLM_PROVIDER=deepseek`; key in Render env vars |

Both auto-redeploy on push to `main` (1–3 min). After verified code/UI changes, commit and push to `origin/main` by default (still check `git status` / `remote` / `branch`; never commit secrets or runtime artifacts).

## Local dev

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                  # edit for deepseek, or leave mock for keyless

python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo
python scripts/build_previews.py      # rebuild committed sample decks

uvicorn server.app:app --reload --port 8787      # then http://127.0.0.1:8787/
```

`examples/input.md` is a ~800-char defense abstract — cheap for live DeepSeek E2E.

## Architecture

### The two schemas (most important thing to understand)

The LLM emits a deliberately narrow shape — see `src/schema/__init__.py` and the prompt in `src/llm/deepseek.py`:

```json
{
  "title": "...", "subtitle": "...",
  "slides": [
    { "type": "cover|contents|section|content|closing",
      "title": "...", "bullets": ["..."], "layout": "cards"?,
      "section"?, "notes"?, "image_prompt"?, "chart_suggestion"?,
      "stat"?, "quote"?, "compare"?, "kpis"?, "steps"?, "columns"? }
  ]
}
```

`validate_slide_json` only checks shape — every renderer falls back to parsing `bullets` heuristically when a structured field is absent. `KNOWN_LAYOUTS` = `KNOWN_PKU_LAYOUTS` (14 PKU runtime names) ∪ `KNOWN_GENERIC_LAYOUTS` (11 html-ppt: `cards / bullets / two-column / three-column / kpi-grid / stat-highlight / comparison / pros-cons / big-quote / timeline / process-steps`).

The PKU runtime (`assets/runtime.js`) needs much richer per-layout fields (`headline`, `images[]`, `items[]`, `cards[]`, `nodes[]`, `chapterIndex`, …). Full grammar: `pku-red-defense-ppt/references/slides-json-schema.md`. Each html-ppt template emits a complete `index.html` directly — no per-template slides.json schema.

### Anti-fabrication rules in the LLM prompt (don't loosen)

- `stat-highlight` and `big-quote`: at most 1 per deck, and omittable. No synthesizing numbers/quotes.
- `kpi-grid` requires ≥3 real quantitative metrics from the source.
- `comparison` / `pros-cons` require both sides to have 2–4 distinct source points.
- `timeline` requires real time anchors (no inventing `2024 Q3`-style markers).
- `process-steps` requires dependency-ordered steps, not a flat list.
- Default fallbacks: `cards` and `bullets`. A 70%-`cards` deck is fine.

Legacy PKU names (`multi-card`, `theory-cards`, `method`, `section-text`, `vs`, `swot`, `framework`) are accepted; `layouts._LAYOUT_ALIASES` normalizes them.

### Dispatch & rendering

`src/renderer/dispatch.py` maps slug → render function. All 15 html-ppt templates have dedicated renderers (`src/renderer/<template>.py`); `html_ppt_generic.py` is a safety fallback nothing currently uses. PKU is `compile_to_pku()` in `src/renderer/__init__.py` + the PKU runtime.

**`src/renderer/layouts.py` owns the shared boilerplate**, imported by every html-ppt renderer as `L`:

- Text: `L.esc`, `L.rich` (`**phrase**` → `<em>`), `L.rich_grad`, `L.split_kv`.
- Planning: `L.planned_slides(generic)` (synthesizes cover+closing), `L.chapter_titles(generic)`.
- Extractors: `L.get_columns / get_kpis / get_stat / get_quote / get_compare / get_steps / get_bullets` — each returns the structured field or a bullet-based fallback.
- `L.normalize_layout(layout, bullets_count)` collapses aliases and picks defaults.
- `L.render_inner(layout, slide)` dispatches to `inner_*` fragments using stable classes (`.content-cards`, `.content-bullets`, `.content-cols`, `.content-kpis`, `.content-stat`, `.content-vs[.pc]`, `.content-quote`, `.content-timeline`, `.content-steps`) plus shared primitives (`.card`, `.grid g2|g3|g4`, `.pill`, `.gradient-text`).

Renderers compose their own brand chrome + `L.render_inner(...)` + footer.

**`templates/html-ppt/shared/assets/base.css`** ships default rules for every `.content-*` class so new templates get all 11 layouts free. Per-template `style.css` retheme by overriding CSS custom properties (`--accent`, `--accent-2`, `--accent-3`, `--surface`, `--surface-2`, `--text-1/2/3`, `--grad`, `--border`). Override `.content-*` only when tokens can't carry the look. Shared `@media print` block also lives there.

### `compile_to_pku()` — generic → PKU bridge

In `src/renderer/__init__.py`:

- Walks slides; every `type=section` is a chapter. 3–6 → use those; else fall back to 5 default PKU chapters.
- `_resolve_pku_layout(slide)` keeps PKU layouts, else translates via `_GENERIC_TO_PKU` (`cards → multi-card`, `bullets → section-text`, `kpi-grid → multi-card` value-led, `stat-highlight → section-text`, `comparison/pros-cons → vs`, `process-steps → method`, `big-quote → section-text`, `timeline → timeline`). No hint → bullet-count heuristic.
- Structured fields → PKU shape via `_kpi_cards`, `_theory_cards_from_columns`, `_vs_from_compare`, `_method_from_steps`, `_timeline_from_steps`, `_quote_blocks`, `_stat_blocks`.
- Bullets shaped `"title: body"` / `"标题：正文"` split into card title+body; otherwise auto-numbered.
- Always inserts cover at start and closing at end if missing.
- `image-analysis` / `chart-analysis` currently fall through to `section-text` (no real image assets). Extend the LLM contract before adding a branch.

### Template registry

`src/templates/registry.py` is the single source of truth. `GET /api/templates` returns `public_dict()`, which **hides** `preview_url` and maps internal engines to `classic` or `template`. Keep public API display data free of skill/source names (no `html-ppt`, `pku-red-defense-ppt` in user-visible copy).

Current `template_id`s: `pku-red` (default) + 15 html-ppt templates (`xhs-white-editorial`, `graphify-dark-graph`, `knowledge-arch-blueprint`, `hermes-cyber-terminal`, `obsidian-claude-gradient`, `testing-safety-alert`, `xhs-pastel-card`, `dir-key-nav-minimal`, `pitch-deck`, `product-launch`, `tech-sharing`, `weekly-report`, `xhs-post`, `course-module`, `presenter-mode-reveal`).

### Job lifecycle

```
POST /api/jobs (template_id, manuscript)  → writes data/jobs/{id}.json (pending), daemon thread runs LLM→render→export→zip
GET  /api/jobs/{id}                       → reads job JSON
GET  /api/templates                       → registry list
GET  /decks/{id}.zip and /decks/{id}/index.html   ← what download_url/preview_url point at (StaticFiles)
GET  /api/jobs/{id}/{download,preview}    ← legacy/curl only; do not switch the frontend back (see edge quirk below)
GET  /previews/{template_id}/index.html   ← committed sample deck (only entry point for 预览)
GET  /收款码/...                          ← donation QR mount
```

Job runner is a daemon thread inside FastAPI — no queue. Fine for the MVP, not for prod.

While running, `_run_job` writes `phase` (`llm` → `render` → `zip` → `done`) and `progress` (5/60/90/100). Frontend renders `phase` as a labeled spinner only — the integer is for debugging; don't surface a % bar (LLM dominates wall time, the bar visually freezes).

`src/llm/__init__.generate_slide_json` calls `src.renderer.diversify.diversify_layouts(raw)` after validation. It rewrites the third+ slide in runs of 3+ same-layout content slides to a content-fit alternative — never invents structured fields. This is why a slide may end up `two-column` when the LLM emitted `cards`.

Every materialized deck (PKU and html-ppt) gets a `data/slide.json` (singular) = the raw generic LLM JSON, for debug/re-runs. Don't confuse with PKU's `data/slides.json` (plural) — the rich PKU-runtime JSON consumed by `runtime.js`. html-ppt decks only have `slide.json`; PKU decks have both.

## Frontend

Exactly two views — do not re-add a third:

- `#templates` — cards with `使用模板` (red filled, jumps to `#generate`) and `预览` (light outline, opens `previews/<id>/index.html` in a new tab). The 预览 link is the **only** path to a preview.
- `#generate` — paste, generate, poll, download/preview.

Removed and not coming back without an ask: `template-preview.html`, `web/template-preview.html`, `html-ppt-templates/index.html`, `html-ppt-templates/templates/full-decks-index.html`. `server/app.py` must not mount `/html-ppt-templates` for public browsing.

Canonical copy (keep root `index.html` and `web/index.html` in sync):

- Brand: **`fxt ppt`**.
- Donation note on both views, with `.donation-trigger` opening a shared QR modal (`收款码/537a8a731804791d569387f56522fa2a.jpg`):
  > 该网页暂时免费使用，生成 PPT 需要一定的 API tokens 花费，该费用由作者承担，请勿滥用，如果感到有用，也欢迎 打赏给作者 <=1 元的奖赏~
- Generate-view warning:
  > PPT 生成约需 30s–2min，生成过程中切勿刷新页面，刷新页面也会丢失您的既往文件生成记录。
- Export wording: `网页包和 PDF` (not `HTML/PPTX`, except when explaining PPTX is unsupported).
- Job action buttons: **`进入预览页`** red filled, **`下载网页包`** light filled with red text/border.

**Two `index.html` files** (don't delete one as a duplicate): root serves on Pages, references `web/style.css` + `web/app.js`. `web/index.html` is served by local uvicorn at `/`. Keep them in sync.

**Cold-start warmup**: `web/app.js` pings `/api/health` whenever the user enters `#generate`, throttled to once per 60s, to hide Render's ~30s cold start behind paste/read time. Don't remove it without solving the underlying sleep.

## Per-deck features (both templates)

### 导出 PDF button

Floating pill at bottom-right of every deck (and every preview) calls `window.print()`. Save-as-PDF → one-page-per-slide at native 1280×720. Keyboard shortcut **P**.

- html-ppt: injected by `templates/html-ppt/shared/assets/runtime.js`; print rules in `templates/html-ppt/shared/assets/base.css`.
- PKU: injected by `pku-red-defense-ppt/assets/template/assets/runtime.js` (mirrored to root `assets/runtime.js`). PKU's print rules live inside `deck-stage.js`'s shadow DOM; `@page` size is set via the inline `<style id="deck-stage-print-page">` that `connectedCallback` injects into `<head>` (at-rule has no effect inside shadow DOM).

Shared print stack: `@page { size: 1280px 720px; margin: 0 }`, `.deck { overflow: visible; position: static }`, `.slide { width: 1280px; height: 720px; opacity: 1; page-break-after: always; overflow: hidden }`, `* { print-color-adjust: exact }`. Chrome (`.progress-bar`, `.notes-overlay`, `.overview`, `.pdf-export-btn`, `.edit-panel`, `.nav-arrows`) hidden in print.

`xhs-post` is 3:4 portrait (810×1080). Its `style.css` has a trailing `@media print` block overriding `@page` and `.slide`. Per-template `style.css` loads after shared `base.css`, so the override sticks. Follow this pattern for any non-16:9 template.

### Field-edit panel + re-export

`✎ 修改字段` toggle (above the PDF button) opens a 360px sidebar with verbatim find/replace, undo, clear-all, and `⇩ 下载修改后的网页包`. Same panel in both runtimes; PKU copy mirrored to root.

- Each replace appends to `localStorage["fxt-ppt-deck-edits:" + location.pathname]` as `{find, replace, slideIndex, ts}`. Pathname keys keep `/decks/<id>/` and `/previews/<id>/` histories separate.
- On init, ops replay **only against the recorded `slideIndex`** so slide-3 edits don't bleed into slide-7. Pre-`slideIndex` ops fall back to whole-deck.
- Undo pops the latest op so refresh agrees with the screen.

Re-export only enabled on `/decks/<id>/index.html`. Lazy-loads JSZip from **vendored** `assets/jszip.min.js` (shipped with every deck), CDN is fallback only — don't switch back to CDN-first (offline / firewall use). Rewrites `index.html` (stripped of injected chrome) in the zip; for PKU also rewrites `data/slides.json` so edits survive (PKU re-renders from JSON each load and would wipe DOM edits otherwise).

When changing the panel, keep both runtimes feature-parity and run `python scripts/build_previews.py` so committed samples ship the new behavior.

## Typography rule (CJK-first)

All html-ppt stylesheets target Chinese titles on 1280×720:

- Cover headline (`.h1` / `.xp-h1` / `.xw-title` / `.hc-h1` / `.gd-h1` / `.kb-h1` / `.oc-h1` / `.ts-h1` / `.dk-h0` …): **56–74px**, line-height ~1.16, near-zero `letter-spacing`, `max-width:1040–1080px`, `word-break:break-word`.
- Slide title (`.h2` etc.): **40–48px**, line-height ~1.2.
- Decorative watermark numerals (`.section-num`, `.dk-big`, `.kb-big-num`, `.hc-big`, `.gd-big`, `.oc-big`, `.mega`): capped ~144–180px, positioned as backdrops.
- Body / lede: 18–22px, card body 14–16px, kicker / footer 11–13px.

Every headline rule keeps a `:lang(en)` override restoring 74–96px Latin sizes (triggered by `html.lang === "en"` or `lang="en"`).

Don'ts: no `letter-spacing` more negative than `-0.5px` on CJK; always set `max-width` on wrappable hero headlines; exclude decorative absolutely-positioned children (`.section-num`, `.cover-bg`, `.cover-blob`) from any `.slide > *` rule.

## PKU template specifics

### Shared chrome (content pages)

Every non-`cover`/`contents`/`section-divider`/`closing` layout renders via `chrome()` in `assets/runtime.js`: top-left `sectionTitle` (+ optional English), top-right chapter nav with active chapter underlined red, big `headline`, bottom-right auto page number (only content pages count), bottom-left footer from `footerTag`.

Already removed — don't re-add without an ask:

- Cover white metadata box (`汇报人` / `指导老师` / `学院专业`).
- Auto-rendering `meta.school` in the lower-left footer (per-slide `footerTag` still works).
- `X X X` / `X X X 教授` / `X X 学院 · X X 专业` placeholders in `DEFAULT_META`, root `data/slides.json`, and the mirrored copy.

### Rich text

`headline` and body-ish fields run through `rich()`: `**phrase**` → `<em>`, `<em>...</em>` → red emphasis, `<span class="accent">...</span>` → red, `<br>` → line break, everything else HTML-escaped.

### Image fit modes

`images[].fit`: `cover` (default; photos), `contain` (charts, screenshots — no distortion), `diagram` (contain + padding), `logo` (framed), `fullBleed` (edge-to-edge). Optional `focalPoint: {x, y}` (0–1) tunes the crop anchor. Anything with readable text uses `contain` or `diagram`, never cropped `cover`.

## Visual rules (PKU-only, non-negotiable for that template)

The 15 html-ppt templates each carry their own theme (dark, neon, gradient, sticker — all fine). For `pku-red` only:

- 16:9 / 1280×720, white content pages, PKU red `#9A0000` is the only strong accent.
- Red is for: nav highlight, ordinal numbers, key phrases, section-divider backgrounds, cover/closing backgrounds.
- Cards: light-gray border + white fill, no heavy drop shadows.
- **Not** a marketing page. No glassmorphism, no purple/blue tech gradients, no dark heroes, no landing-page card stacks.

Sources of truth: `pku-red-defense-ppt/references/{template-spec,layout-selection,image-rules,slides-json-schema}.md`.

## Render quirks (deploy-time gotchas)

### Edge routing breaks `FileResponse` with `Origin`

`GET /api/jobs/{id}/download` with `Origin: https://fxt-gw-pb.github.io` returns Render's edge 404 (`x-render-routing: no-server`) — never reaches uvicorn. Same path without Origin works; same bytes via `/decks/{id}.zip` (StaticFiles) work with Origin. This is why `download_url` / `preview_url` point at `/decks/...`. `/api/jobs/{id}/{download,preview}` remain for curl/CLI. **Do not switch the frontend back to `/api/jobs/{id}/download`** — root cause unfixed.

### Ephemeral filesystem

Every deploy/cold-start/restart wipes `outputs/` and `data/jobs/`. A zip is only guaranteed right after the job finishes. For persistence: attach a Render disk (paid) or move outputs to S3/R2 + signed URLs.

`previews/` is committed and survives restarts. Don't put user decks there.

### Cold start

Free tier sleeps after 15 min idle, next request waits ~30s. First `/api/health` may time out — page silently no-ops; user sees the error on Generate.

## CORS

`server/app.py` allowlist: `https://fxt-gw-pb.github.io` + localhost (8787, 8090). Override via `CORS_ORIGINS="a,b,c"`. **Do not widen to `["*"]`** without rate limits — DeepSeek calls cost money and the Render URL is technically discoverable in `web/app.js`.

## API key handling

- `.env` (gitignored) holds the local key; `.env.example` always carries the placeholder.
- Render holds the production key in Settings → Environment.
- DeepSeek calls default to `DEEPSEEK_MODEL=deepseek-v4-pro`; legacy `deepseek-chat` / `deepseek-reasoner` env values are coerced; `extra_body={"thinking":{"type":"disabled"}}` is always sent. Don't enable thinking mode unless asked.
- Never print/inspect `.env` unless explicitly asked. Frontend never sees the key.
- **A real key in a tracked file is compromised the moment it's pushed** — rotate immediately on the DeepSeek dashboard, even after force-push (GitHub keeps detached commits reachable for a while).

## Local-dev gotchas

- Shell has `http_proxy=127.0.0.1:7897`. Use `curl --noproxy 127.0.0.1 …` for loopback hits, else 502.
- `which curl` → `/opt/anaconda3/bin/curl`. Some compound shell forms strip anaconda from PATH and produce "command not found: curl" — use `/usr/bin/curl` explicitly when scripting.
- Always preview decks over HTTP (uvicorn), never `file://`, because `runtime.js` fetches `data/slides.json`.
- Background uvicorn killed via `pkill -9` reports status `failed` — expected, not an error.

## PKU template sync rule

The PKU red template lives in two mirrored places:

- Root (used by `demo.html`): `deck-stage.js`, `assets/{base,theme-pku-red}.css`, `assets/runtime.js`, `assets/jszip.min.js`, `data/slides.json`.
- Skill/export (used by generated PKU decks): `pku-red-defense-ppt/assets/template/...`.

After changing any of those, update both copies and verify with `cmp -s`. The exporter copies the `pku-red-defense-ppt/...` tree, not the root files.

## Validation checklist

After backend / pipeline / renderer changes:

```bash
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
python pku-red-defense-ppt/scripts/validate_slides.py outputs/demo/data/slides.json
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo
python scripts/build_previews.py            # if renderers/CSS changed
```

API changes:

```bash
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/health
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/templates
```

PDF/print regressions:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --print-to-pdf=/tmp/deck.pdf --print-to-pdf-no-header \
  --virtual-time-budget=8000 \
  "http://127.0.0.1:8787/previews/pitch-deck/index.html"
# expect ~14 pages at 960×540 PDF points (= 1280×720 CSS px)
```

## Extending

- **New generic layout**: add the name to `KNOWN_GENERIC_LAYOUTS` (extend `_check_structured_fields` if it needs a new field) → describe + anti-fab rules in the DeepSeek prompt → add `get_<field>` extractor and `inner_<layout>` fragment in `layouts.py`, route in `render_inner` → default `.content-<layout>` rule in shared `base.css` using only CSS tokens → optionally extend `compile_to_pku()`.
- **New PKU layout**: extend the DeepSeek prompt → add a branch in `_render_content()` (`src/renderer/__init__.py`) → confirm in `KNOWN_PKU_LAYOUTS`.
- **New full-deck template**: drop assets under `templates/html-ppt/<id>/` (`manifest.json` + scoped `style.css`) → add `src/renderer/<id_slug>.py` with `render_<slug>(generic)` returning complete `index.html` (use `L.planned_slides` / `L.normalize_layout` / `L.render_inner` so all 11 generic layouts work for free; only hand-write brand chrome) → follow CJK type hierarchy → register in `dispatch.py` and `registry.py` → `python scripts/build_previews.py`.
- **Server-side PDF**: add Playwright; in `_run_job()` after zip, headless Chromium + `page.pdf(landscape=True, width="1280px", height="720px")`; add `pdf_url` on done jobs.
- **PPTX**: either re-implement layouts via `python-pptx` or use LibreOffice headless.
- **Object storage**: replace `OUTPUT_DIR` writes with S3/R2; return signed URLs; the `/decks` mount becomes obsolete.
- **Production queueing**: replace daemon threads with Redis/RQ/Celery.

## What's not built (intentional MVP scope)

No persistence (ephemeral disk, no DB; `previews/` is the only stable served folder). No auth, no rate limits, no per-user quotas. No queue. PDF is client-side only (`window.print()` + `@media print` + the 导出 PDF button). No image generation (`image_prompt` captured but unused). No preview-before-publish flow.

## Key files

- `server/app.py` — FastAPI: jobs, CORS, static mounts (`/decks`, `/previews`, `/收款码`, `/`).
- `web/app.js`, `web/style.css` — keyless frontend, backend URL selection, polling, 预览 link.
- `src/llm/{deepseek,mock}.py` — providers + strict JSON prompt.
- `src/schema/__init__.py` — generic validator + `KNOWN_LAYOUTS`.
- `src/renderer/__init__.py` — `compile_to_pku()`.
- `src/renderer/dispatch.py` — slug → render function.
- `src/renderer/layouts.py` — shared helpers (`planned_slides`, `normalize_layout`, `render_inner`, extractors).
- `src/renderer/<template>.py` — 15 dedicated renderers.
- `src/renderer/diversify.py` — post-LLM same-layout-run breaker.
- `src/exporter/__init__.py` — copy template + write `data/slide.json` + zip.
- `src/templates/registry.py` — template registry (used by API/CLI/frontend).
- `scripts/{generate,build_previews}.py` — CLI entrypoints.
- `templates/html-ppt/shared/assets/{base.css,runtime.js,jszip.min.js}` — shared deck CSS / runtime / vendored JSZip.
- `pku-red-defense-ppt/assets/template/assets/{runtime.js,jszip.min.js}` — PKU runtime + vendored JSZip (mirrored to root `assets/`).
- `pku-red-defense-ppt/scripts/validate_slides.py` — PKU JSON validator.
- `AGENTS.md` — Codex mirror; keep aligned.
- `.env.example` — public env template.
