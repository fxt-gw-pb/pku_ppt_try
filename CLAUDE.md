# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A web service that turns a Chinese academic manuscript into a downloadable PKU-red-themed HTML thesis-defense deck.

```
manuscript
  → DeepSeek API (or mock)              ← src/llm/
  → generic slide_json                  ← validated by src/schema/
  → PKU slides.json (chapters + layouts + headlines)
                                        ← src/renderer/compile_to_pku()
  → materialized HTML deck folder + zip ← src/exporter/
  → served at /decks/{id}/index.html and /decks/{id}.zip
```

The repo bundles **three things**, intentionally co-located:

1. **Backend** (`server/app.py`, FastAPI) — runs the LLM-→-render-→-export pipeline. Job state is JSON files in `data/jobs/`. Output decks land in `outputs/<id>/` with a sibling `outputs/<id>.zip`.
2. **Frontend** (root `index.html` + `web/`) — paste-text → click-generate → poll → download/preview. Pure static HTML/JS. **No API key.**
3. **PKU PPT template** (`demo.html` + `deck-stage.js` + `assets/` + `data/slides.json`) — a standalone runnable deck, independent of the LLM pipeline. Also packaged as a Claude skill at `pku-red-defense-ppt/`.

## Live deployment

| Layer | Where | Notes |
|---|---|---|
| Repo (origin/main) | `git@github.com:fxt-gw-pb/pku_ppt_try.git` | SSH only; HTTPS+token is not configured |
| Frontend | `https://fxt-gw-pb.github.io/pku_ppt_try/` (Pages, source: main / root) | root `index.html`. Sample deck at `/demo.html` |
| Backend | `https://pku-ppt-try.onrender.com` (Render free tier) | `LLM_PROVIDER=deepseek`, key in Render env vars |

Render auto-redeploys on push to `main`. Pages also rebuilds. Both take 1-3 min.

## Local dev quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate          # or invoke .venv/bin/<tool> directly

pip install -r requirements.txt    # fastapi, uvicorn, openai, python-dotenv, pydantic

cp .env.example .env               # then edit: LLM_PROVIDER=deepseek + real key
                                   # or leave LLM_PROVIDER=mock for keyless dev

# CLI
python scripts/generate.py --input examples/input.md --output outputs/demo

# Backend + frontend together (uvicorn mounts web/ at "/")
uvicorn server.app:app --reload --port 8787
# then http://127.0.0.1:8787/
```

`examples/input.md` is a ~800-char defense abstract — cheap for live DeepSeek E2E tests.

## Repo layout

```
.
├── index.html                  # Frontend (Pages root). Refs web/style.css + web/app.js.
├── demo.html                   # Original PKU sample deck shell.  At /demo.html on Pages.
├── deck-stage.js               # PKU template's web component.   Used by demo.html + every generated deck.
├── assets/{base,theme-pku-red}.css, runtime.js, media/   # PKU template assets
├── data/slides.json            # Sample PKU slides.json loaded by demo.html
│
├── pku-red-defense-ppt/        # Claude skill bundle; assets/template/ mirrors the deck-runtime files.
│
├── src/                        # Python pipeline (importable as `src.llm`, `src.renderer`, ...).
│   ├── llm/{deepseek,mock}.py  # provider dispatch.  Entry: generate_slide_json(text, options).
│   ├── schema/__init__.py      # validate the GENERIC slide_json (LLM output, NOT the PKU shape).
│   ├── renderer/__init__.py    # compile_to_pku(): generic → PKU slides.json (layout heuristics).
│   └── exporter/__init__.py    # export_deck (copy template + write slides.json) + zip_deck.
├── scripts/generate.py         # CLI wrapper.
├── server/app.py               # FastAPI: /api/health, /api/jobs (POST/GET),
│                               # /api/jobs/:id/{download,preview} (legacy/curl only).
│                               # Static-mounts /decks → outputs/, / → web/.
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
├── README.md, CLAUDE.md, prompt.md
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

The PKU runtime (`assets/runtime.js`) needs much richer per-layout fields: `headline`, `images[]`, `items[]`, `cards[]`, `nodes[]`, `chapterIndex`, etc. — full grammar in `pku-red-defense-ppt/references/slides-json-schema.md`.

`src/renderer/compile_to_pku()` bridges the two:

- **Chapter detection**: walks slides; every `type=section` slide contributes a chapter title. If 3-6 found, uses those; else falls back to the 5 default PKU chapters.
- **Layout pick** for `type=content`: honors `slide.layout` if it's one of `multi-card / theory-cards / method / timeline / section-text`; else heuristic — 2-4 bullets → `multi-card`, else `section-text`.
- **Bullet → card** conversion: bullets shaped as `"title: body"` or `"标题：正文"` split into card title + body; otherwise auto-numbered.
- Always inserts a `cover` at start and `closing` at end if the LLM omitted them.

If you want to support a richer layout (image-analysis, framework, vs, swot), it needs structured fields the bullets format can't carry — you'd need to extend the LLM contract first, then add a branch in `_render_content()`.

### Job lifecycle (backend)

```
POST /api/jobs                  → write data/jobs/{id}.json (status=pending), spawn daemon thread
   daemon thread:
     run LLM → validate → compile → export → zip
     update job JSON to status=done with download_url + preview_url
GET  /api/jobs/{id}             → read job JSON (strips traceback for the response)
GET  /decks/{id}.zip            ← what download_url points at (StaticFiles)
GET  /decks/{id}/index.html     ← what preview_url points at
GET  /api/jobs/{id}/download    ← legacy/curl; FileResponse — broken under Render+Origin, see quirks
GET  /api/jobs/{id}/preview     ← legacy/curl; 307 to /decks/{id}/index.html
```

The job runner is a daemon thread inside the FastAPI process — no queue. Fine for the free-tier MVP; not for production load.

## Two `index.html` files (don't delete one assuming it's a duplicate)

- **Root `index.html`** — GitHub Pages serves it at the bare site URL. References `web/style.css` and `web/app.js`. Has a link to `demo.html`.
- **`web/index.html`** — local uvicorn serves it at `/` via `app.mount("/", StaticFiles(directory="web"))`. References sibling `style.css` and `app.js`.

Keep them in sync when editing the UI. Root used to be the deck (`demo.html`); the deck moved so Pages' root URL surfaces the interactive site.

## PKU template specifics (preserved across decks)

### Shared chrome (content pages)

Every layout except `cover` / `contents` / `section-divider` / `closing` renders via `chrome()` in `assets/runtime.js`: top-left `sectionTitle` (+ optional English), top-right chapter nav with the active chapter underlined red, big `headline`, bottom-right auto page number (only content pages count — chapter dividers are skipped), bottom-left footer from `meta.school` or per-slide `footerTag`.

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

- 16:9 / 1280×720 canvas; white content pages; PKU red `#9A0000` is the only accent.
- Red is reserved for: nav highlight, ordinal numbers, key phrases, section-divider backgrounds, cover background.
- Cards: light-gray border + white fill, no heavy drop shadows.
- **Not** a marketing page. No glassmorphism, purple/blue tech gradients, dark hero pages, or landing-page card stacks. Source of truth: `pku-red-defense-ppt/references/template-spec.md`.

## Render quirks (the deploy-time gotchas)

### Edge routing weirdness with FileResponse + Origin

A `GET /api/jobs/{id}/download` request with `Origin: https://fxt-gw-pb.github.io` returns:

```
HTTP/2 404
content-type: text/plain
content-length: 10
x-render-routing: no-server
```

— bare "Not Found" from Render's edge, never reaching uvicorn. The same path **without** the Origin header reaches uvicorn fine and returns the 9.6 MB zip. The same bytes served via `/decks/{id}.zip` (Starlette `StaticFiles`) work with Origin set.

This is why the API's `download_url` / `preview_url` fields point at `/decks/...` instead of `/api/jobs/{id}/...`. The `/api/jobs/{id}/{download,preview}` endpoints still exist for curl/CLI (no Origin) but the frontend doesn't use them. Root cause is between Render's edge layer (Cloudflare) and FastAPI's `FileResponse`; we worked around rather than diagnosed.

### Ephemeral filesystem

Every deploy / cold-start / restart wipes `outputs/` and `data/jobs/`. A job's zip is only guaranteed available immediately after it finishes. For persistence: attach a Render disk (paid) or move outputs to S3/R2 and return signed URLs.

### Cold start

After 15 min idle, free tier spins down. Next request waits ~30 s. The frontend's first `/api/health` poll may time out — the page silently no-ops on failed health (since this commit removed the "backend offline" banner). The user sees the error when they click Generate.

## CORS

`server/app.py` allowlist: `https://fxt-gw-pb.github.io` + localhost dev ports (8787, 8090). Override with `CORS_ORIGINS="a,b,c"` env var. **Do not loosen back to `["*"]`** without adding rate limits — DeepSeek calls cost money and your Render URL is technically discoverable via `web/app.js`.

## API key handling (zero compromises)

- `.env` (gitignored) holds the real local key. `.env.example` always has the placeholder string.
- Render holds the production key in Settings → Environment.
- The frontend never sees the key. `web/app.js` only knows the backend's public URL.
- If a real key ever lands in a tracked file, the key is **compromised the moment that commit is pushed** — rotate immediately on the DeepSeek dashboard, even after force-pushing to strip the commit. GitHub keeps detached commits reachable for a while after force-push.

## Local-dev gotchas

- **HTTP proxy**: this machine has `http_proxy=127.0.0.1:7897` in the shell. `curl http://127.0.0.1:8787/…` will 502 through the proxy. Use `curl --noproxy 127.0.0.1 …` for local-loopback hits.
- **curl on PATH**: `which curl` → `/opt/anaconda3/bin/curl`. Some compound shell forms (e.g. `eval` with `for` loops through the Bash tool) strip anaconda from PATH and produce "command not found: curl". Use `/usr/bin/curl` explicitly when scripting.

## Skill bundle (`pku-red-defense-ppt/`)

Independent of the LLM pipeline; usable as a Claude skill to compose a PKU deck from a user outline. The pipeline's exporter consumes its `assets/template/` directory directly. If you change the PKU template (`deck-stage.js`, `assets/base.css`, `assets/runtime.js`, `assets/theme-pku-red.css`), update BOTH:

- Root-level files (`deck-stage.js`, `assets/*`) — used by `demo.html` and as the visual ground truth.
- `pku-red-defense-ppt/assets/template/*` — what the exporter copies for every generated deck.

They will silently drift otherwise. The skill has its own README (`SKILL.md`) and references (`references/{template-spec, slides-json-schema, layout-selection, image-rules}.md`).

## Extending

- **New PKU layout from LLM**: (a) extend the system prompt in `src/llm/deepseek.py` so the model emits the layout-specific fields; (b) add a branch in `_render_content()` in `src/renderer/__init__.py`; (c) confirm the layout name is in `KNOWN_PKU_LAYOUTS` of `src/schema/__init__.py`.
- **Server-side PDF**: add Playwright; in `_run_job()` after the zip step, launch headless Chromium, navigate to the deck's `index.html`, `page.pdf(landscape=True, width="1280px", height="720px")`. Add a `pdf_url` field on done jobs.
- **PPTX export**: harder — either re-implement each PKU layout via `python-pptx`, or use LibreOffice headless to convert the HTML deck. Layout-specific work for either path.
- **Object storage for outputs**: replace `OUTPUT_DIR` writes with `boto3` calls to S3/R2; return signed URLs in `download_url`. The `/decks` static mount becomes obsolete and the Render ephemeral-filesystem problem goes away.

## What's not built (deliberate MVP scope)

- No persistence (Render's ephemeral disk; no DB).
- No auth, no rate limits, no per-user quotas.
- No queue (job runner is a daemon thread inside the FastAPI process).
- No PDF/PPTX server-side export.
- No image generation (`image_prompt` LLM field is captured but unused).
- No PR-style flow / preview-before-publish.
