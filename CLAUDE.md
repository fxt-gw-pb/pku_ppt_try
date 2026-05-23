# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Codex maintains a parallel `AGENTS.md` — keep both in sync after non-trivial changes.

## What this is

A web service that turns a Chinese academic manuscript into a downloadable HTML defense/presentation deck. The default visual theme is PKU red, but the pipeline is now multi-template: a `template_id` chosen on the frontend picks which renderer + asset bundle is materialized.

```
manuscript + template_id
  → DeepSeek API (or mock)               ← src/llm/
  → generic slide_json                   ← validated by src/schema/
  → template-specific slides.json        ← src/renderer/* (compile_to_pku() or html_ppt_generic / xhs_white_editorial)
  → materialized HTML deck folder + zip  ← src/exporter/  (copies templates/html-ppt/<id>/ or pku-red-defense-ppt/assets/template/)
  → served at /decks/{id}/index.html and /decks/{id}.zip
```

The repo bundles **three things**, intentionally co-located:

1. **Backend** (`server/app.py`, FastAPI) — runs the LLM-→-render-→-export pipeline. Job state is JSON files in `data/jobs/`. Output decks land in `outputs/<id>/` with a sibling `outputs/<id>.zip`.
2. **Frontend** (root `index.html` + `web/`) — branded **`fxt ppt`**. Two-view static app: `#templates` (pick a template) → `#generate` (paste, generate, poll, download/preview). Pure static HTML/JS. **No API key.**
3. **Deck templates**
   - PKU red template at `demo.html` + `deck-stage.js` + `assets/` + `data/slides.json`, with the export copy under `pku-red-defense-ppt/assets/template/`.
   - 15 imported full-deck templates under `templates/html-ppt/<id>/` (the production source of truth that the exporter consumes). `html-ppt-templates/` is a separate imported archive — keep the exporter independent of it and do not expose it as a public gallery.

## Live deployment

| Layer | Where | Notes |
|---|---|---|
| Repo (origin/main) | `git@github.com:fxt-gw-pb/pku_ppt_try.git` | SSH only; HTTPS+token is not configured |
| Frontend | `https://fxt-gw-pb.github.io/pku_ppt_try/` (Pages, source: main / root) | root `index.html`; sample PKU deck at `/demo.html` |
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

# Backend + frontend together (uvicorn mounts web/ at "/")
uvicorn server.app:app --reload --port 8787
# then http://127.0.0.1:8787/
```

`examples/input.md` is a ~800-char defense abstract — cheap for live DeepSeek E2E tests.

## Repo layout

```
.
├── index.html                  # Frontend (Pages root). Two-view app. Refs web/style.css + web/app.js.
├── demo.html                   # Original PKU sample deck shell.  At /demo.html on Pages.
├── deck-stage.js               # PKU template's web component.   Used by demo.html + every PKU-rendered deck.
├── assets/{base,theme-pku-red}.css, runtime.js, media/   # PKU template assets (root copy)
├── data/slides.json            # Sample PKU slides.json loaded by demo.html
├── 收款码/537a8a...jpg          # Donation QR image; FastAPI mounts /收款码 for local preview.
│
├── pku-red-defense-ppt/        # PKU skill bundle; assets/template/ is what the exporter copies for pku-red decks.
├── templates/html-ppt/<id>/    # Production source for the 15 imported full-deck templates (exporter reads here).
├── html-ppt-templates/         # Imported archive of upstream HTML decks. NOT a public gallery; exporter is independent.
│
├── src/                        # Python pipeline (importable as `src.llm`, `src.renderer`, ...).
│   ├── llm/{deepseek,mock}.py  # provider dispatch.  Entry: generate_slide_json(text, options).
│   ├── schema/__init__.py      # validate the GENERIC slide_json (LLM output, NOT any per-template shape).
│   ├── renderer/__init__.py    # compile_to_pku(): generic → PKU slides.json (layout heuristics).
│   ├── renderer/xhs_white_editorial.py  # dedicated renderer for the XHS white editorial template.
│   ├── renderer/html_ppt_generic.py     # generic renderer for the other imported full-deck templates.
│   ├── templates/registry.py   # template registry: used by API (/api/templates), CLI (--template), and frontend.
│   └── exporter/__init__.py    # export_deck (copy template + write slides.json) + zip_deck.
├── scripts/generate.py         # CLI wrapper.  --template <id> selects renderer + asset bundle.
├── server/app.py               # FastAPI: /api/health, /api/templates, /api/jobs (POST/GET),
│                               # /api/jobs/:id/{download,preview} (legacy/curl only).
│                               # Static mounts: /decks → outputs/, /收款码 → 收款码/, / → web/.
├── web/                        # Local-dev frontend source. The root index.html duplicates it for
│                               # GitHub Pages.  web/style.css and web/app.js are the canonical CSS/JS;
│                               # root index.html references them via `web/...` paths.
│
├── outputs/                    # (gitignored) generated decks + zips
├── data/jobs/                  # (gitignored) per-job state JSON
│
├── .env.example                # public template only (placeholder key)
├── .env                        # (gitignored) real local key, LLM_PROVIDER=deepseek
├── requirements.txt
├── README.md, CLAUDE.md, AGENTS.md, prompt.md
└── _ref/                       # PNG reference shots of PKU template slides (not loaded at runtime).
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
      "layout": "multi-card"?,
      "section"?, "notes"?, "image_prompt"?, "chart_suggestion"? }
  ]
}
```

The PKU runtime (`assets/runtime.js`) needs much richer per-layout fields: `headline`, `images[]`, `items[]`, `cards[]`, `nodes[]`, `chapterIndex`, etc. — full grammar in `pku-red-defense-ppt/references/slides-json-schema.md`. Other templates have their own runtime expectations.

`src/renderer/compile_to_pku()` bridges generic → PKU:

- **Chapter detection**: walks slides; every `type=section` slide contributes a chapter title. If 3-6 found, uses those; else falls back to the 5 default PKU chapters.
- **Layout pick** for `type=content`: honors `slide.layout` if it's one of `multi-card / theory-cards / method / timeline / section-text`; else heuristic — 2-4 bullets → `multi-card`, else `section-text`.
- **Bullet → card** conversion: bullets shaped as `"title: body"` or `"标题：正文"` split into card title + body; otherwise auto-numbered.
- Always inserts a `cover` at start and `closing` at end if the LLM omitted them.

Richer PKU layouts (image-analysis, chart-analysis, framework, vs, swot) need structured fields the bullets format can't carry — you'd need to extend the LLM contract first, then add a branch in `_render_content()`.

For non-PKU templates, `xhs-white-editorial` has its own dedicated renderer; the other 14 imported templates currently fall back to `src/renderer/html_ppt_generic.py` until they need template-specific refinement.

### Template registry

`src/templates/registry.py` is the single source of truth for which templates exist, which renderer they use, which asset directory the exporter copies, and what the frontend should advertise.

- API: `GET /api/templates` returns the registry via `public_dict()`.
- `public_dict()` deliberately **hides** `preview_url` and maps internal engines to public-facing display values (`classic` or `template`). Keep public API display data free of skill/source names (`html-ppt`, `pku-red-defense-ppt`, etc.).
- Current `template_id` values: `pku-red` (default) + 15 imported full-deck templates.
- Avoid user-visible `html-ppt` / skill-origin wording in the website, API display data, or generated deck copy. Internal folder names and engine strings can stay where compatibility requires.

### Job lifecycle (backend)

```
POST /api/jobs (template_id, text)  → write data/jobs/{id}.json (status=pending), spawn daemon thread
   daemon thread:
     run LLM → validate generic → renderer-for-template → exporter copies the right template bundle → zip
     update job JSON to status=done with download_url + preview_url
GET  /api/jobs/{id}                 → read job JSON (strips traceback for the response)
GET  /api/templates                 → registry list for the frontend
GET  /decks/{id}.zip                ← what download_url points at (StaticFiles)
GET  /decks/{id}/index.html         ← what preview_url points at
GET  /api/jobs/{id}/download        ← legacy/curl; FileResponse — broken under Render+Origin, see quirks
GET  /api/jobs/{id}/preview         ← legacy/curl; 307 to /decks/{id}/index.html
GET  /收款码/...                     ← static mount for the donation QR image
```

The job runner is still a daemon thread inside the FastAPI process — no queue. Fine for the free-tier MVP; not for production load.

## Frontend (two-view static app)

The public UI exposes exactly two views. Do not re-add a third.

- `#templates` — select a template. Cards have two actions: `使用模板` (red filled, selects the template and jumps to `#generate`) and `预览` (light outline, opens `previews/<template_id>/index.html` in a new tab). The 预览 link is the **only** path to a preview; do not re-introduce a separate template-library page.
- `#generate` — paste manuscript, generate, poll, download/preview the result.

The per-template sample decks live under `previews/` and are committed to the repo. Regenerate them with `python scripts/build_previews.py` whenever you change a renderer, the LLM mock, or a template's bundled assets. GitHub Pages serves them as `previews/<id>/index.html`; FastAPI mounts the same path at `/previews/` for local dev. Do not link to previews from anywhere else (no nav, no list page, no embed) — the only access point is the per-card 预览 button.

Removed and not coming back without an explicit ask: `template-preview.html`, `web/template-preview.html`, `html-ppt-templates/index.html`, `html-ppt-templates/templates/full-decks-index.html`. `server/app.py` must not mount `/html-ppt-templates` for public browsing.

UI copy that is canonical (keep both root `index.html` and `web/index.html` in sync):

- Brand string: **`fxt ppt`**.
- Donation note, on both views, with a clickable `.donation-trigger` opening a shared QR modal backed by `收款码/537a8a731804791d569387f56522fa2a.jpg`:
  > 该网页暂时免费使用，生成 PPT 需要一定的 API tokens 花费，该费用由作者承担，请勿滥用，如果感到有用，也欢迎 打赏给作者 <=1 元的奖赏~
- Generate view warning:
  > PPT 生成需要约 30s，生成过程中切勿刷新页面，刷新页面也会丢失您的既往文件生成记录。
- Export wording in the public UI: `网页包和 PDF` (not `HTML/PPTX`, except when explicitly explaining that PPTX is unsupported).
- Generated-job action buttons are high contrast: **`进入预览页`** red filled, **`下载网页包`** light filled with red text/border.

### Two `index.html` files (don't delete one assuming it's a duplicate)

- **Root `index.html`** — GitHub Pages serves it at the bare site URL. References `web/style.css` and `web/app.js`. Has a link to `demo.html`.
- **`web/index.html`** — local uvicorn serves it at `/` via `app.mount("/", StaticFiles(directory="web"))`. References sibling `style.css` and `app.js`.

Keep them in sync when editing the UI, adjusting paths as needed.

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

## Visual rules (non-negotiable)

- 16:9 / 1280×720 canvas; white content pages; PKU red `#9A0000` is the only strong accent.
- Red is reserved for: nav highlight, ordinal numbers, key phrases, section-divider backgrounds, cover/closing backgrounds.
- Cards: light-gray border + white fill, no heavy drop shadows.
- **Not** a marketing page. No glassmorphism, purple/blue tech gradients, dark hero pages, or landing-page card stacks. Source of truth: `pku-red-defense-ppt/references/template-spec.md`, `layout-selection.md`, `image-rules.md`, `slides-json-schema.md`.

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

### Cold start

After 15 min idle, free tier spins down. Next request waits ~30 s. The frontend's first `/api/health` poll may time out — the page silently no-ops on failed health. The user sees the error when they click Generate.

## CORS

`server/app.py` allowlist: `https://fxt-gw-pb.github.io` + localhost dev ports (8787, 8090). Override with `CORS_ORIGINS="a,b,c"` env var. **Do not loosen back to `["*"]`** without adding rate limits — DeepSeek calls cost money and your Render URL is technically discoverable via `web/app.js`.

## API key handling (zero compromises)

- `.env` (gitignored) holds the real local key. `.env.example` always has the placeholder string.
- Render holds the production key in Settings → Environment.
- Never print or inspect `.env` unless the user explicitly asks.
- The frontend never sees the key. `web/app.js` only knows the backend's public URL.
- If a real key ever lands in a tracked file, the key is **compromised the moment that commit is pushed** — rotate immediately on the DeepSeek dashboard, even after force-pushing to strip the commit. GitHub keeps detached commits reachable for a while after force-push.

## Local-dev gotchas

- **HTTP proxy**: this machine has `http_proxy=127.0.0.1:7897` in the shell. `curl http://127.0.0.1:8787/…` will 502 through the proxy. Use `curl --noproxy 127.0.0.1 …` for local-loopback hits.
- **curl on PATH**: `which curl` → `/opt/anaconda3/bin/curl`. Some compound shell forms (e.g. `eval` with `for` loops through the Bash tool) strip anaconda from PATH and produce "command not found: curl". Use `/usr/bin/curl` explicitly when scripting.
- Always preview generated decks over HTTP (uvicorn), not `file://`, because `runtime.js` fetches `data/slides.json`.

## Template sync rule (PKU)

The PKU red visual template exists in two mirrored places:

- Root runtime used by `demo.html`: `deck-stage.js`, `assets/base.css`, `assets/runtime.js`, `assets/theme-pku-red.css`, `data/slides.json`.
- Skill/export template used by generated PKU decks: `pku-red-defense-ppt/assets/template/...`.

If any of those files change, update **both** copies and verify they still match:

```bash
cmp -s deck-stage.js pku-red-defense-ppt/assets/template/deck-stage.js
cmp -s assets/runtime.js pku-red-defense-ppt/assets/template/assets/runtime.js
cmp -s assets/base.css pku-red-defense-ppt/assets/template/assets/base.css
cmp -s assets/theme-pku-red.css pku-red-defense-ppt/assets/template/assets/theme-pku-red.css
cmp -s data/slides.json pku-red-defense-ppt/assets/template/data/slides.json
```

The exporter copies `pku-red-defense-ppt/assets/template/`, not the root template files. Imported full-deck templates live under `templates/html-ppt/`; keep the exporter independent from `html-ppt-templates/`, and do not expose that folder as a public gallery.

## Validation checklist

After backend / pipeline / renderer changes, run at least:

```bash
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
python pku-red-defense-ppt/scripts/validate_slides.py outputs/demo/data/slides.json
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo
```

For API changes, start uvicorn and:

```bash
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/health
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/templates
```

## Important files

- `AGENTS.md` — Codex handoff notes; keep aligned with this file.
- `README.md` — user-facing setup and usage docs.
- `prompt.md` — original build brief.
- `.env.example` — public environment template.
- `server/app.py` — FastAPI API, job lifecycle, CORS, static mounts.
- `web/app.js` — keyless frontend, GitHub Pages backend URL selection, polling.
- `src/llm/deepseek.py` — DeepSeek OpenAI-compatible provider and strict JSON prompt.
- `src/llm/mock.py` — deterministic provider for keyless E2E tests.
- `src/schema/__init__.py` — generic LLM output validator.
- `src/renderer/__init__.py` — generic-to-PKU compiler.
- `src/renderer/xhs_white_editorial.py` — generic-to-XHS template renderer.
- `src/renderer/html_ppt_generic.py` — generic-to-imported-template renderer for the other full-deck templates.
- `src/exporter/__init__.py` — copy template, write `slides.json`, zip deck.
- `src/templates/registry.py` — template registry used by API, CLI, and frontend.
- `scripts/generate.py` — CLI entrypoint.
- `pku-red-defense-ppt/scripts/validate_slides.py` — validator for PKU runtime JSON.
- `pku-red-defense-ppt/scripts/create_deck.py` — standalone skill materializer.

## Extending

- **New PKU layout from LLM**: (a) extend the system prompt in `src/llm/deepseek.py` so the model emits the layout-specific fields; (b) add a branch in `_render_content()` in `src/renderer/__init__.py`; (c) confirm the layout name is in `KNOWN_PKU_LAYOUTS` of `src/schema/__init__.py`.
- **New full-deck template**: drop the asset bundle under `templates/html-ppt/<id>/`, register it in `src/templates/registry.py`, and either add a dedicated renderer or rely on `html_ppt_generic.py` until refinement is needed.
- **Server-side PDF**: add Playwright; in `_run_job()` after the zip step, launch headless Chromium, navigate to the deck's `index.html`, `page.pdf(landscape=True, width="1280px", height="720px")`. Add a `pdf_url` field on done jobs.
- **PPTX export**: harder — either re-implement each layout via `python-pptx`, or use LibreOffice headless to convert the HTML deck. Layout-specific work for either path.
- **Object storage for outputs**: replace `OUTPUT_DIR` writes with `boto3` calls to S3/R2; return signed URLs in `download_url`. The `/decks` static mount becomes obsolete and the Render ephemeral-filesystem problem goes away.
- **Production queueing**: replace daemon threads with Redis/RQ/Celery or another job system.

## What's not built (deliberate MVP scope)

- No persistence (Render's ephemeral disk; no DB).
- No auth, no rate limits, no per-user quotas.
- No queue (job runner is a daemon thread inside the FastAPI process).
- No PDF/PPTX server-side export.
- No image generation (`image_prompt` LLM field is captured but unused).
- No PR-style flow / preview-before-publish.
