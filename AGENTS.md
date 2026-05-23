# AGENTS.md

Codex handoff notes for this repository. Read this before making changes.

## Project Summary

This is an MVP web service that turns a Chinese academic manuscript into a PKU-red-themed HTML thesis-defense deck.

Pipeline:

```text
manuscript
  -> src/llm/ DeepSeek API or mock provider
  -> generic slide_json validated by src/schema/
  -> PKU slides.json compiled by src/renderer/compile_to_pku()
  -> runnable HTML deck copied from pku-red-defense-ppt/assets/template/
  -> zip + static preview served by server/app.py
```

The repository intentionally contains these related surfaces:

- Backend: `server/app.py`, FastAPI, job state in `data/jobs/`, generated decks in `outputs/`.
- Frontend: root `index.html` for GitHub Pages plus `web/` for local FastAPI static serving. The public UI is branded `fxt ppt`.
- PKU deck template / skill: root `demo.html`, `deck-stage.js`, `assets/`, `data/slides.json`, and the mirrored skill bundle under `pku-red-defense-ppt/`.

## Critical Constraints

- Never put API keys in frontend code, HTML, README, commits, or GitHub Pages.
- Never print or inspect `.env` unless the user explicitly asks and understands it may contain secrets.
- Real keys belong only in local `.env` or backend platform environment variables.
- `web/app.js` must remain keyless. It only calls the public backend URL or same-origin local backend.
- Do not loosen CORS to `["*"]` without adding rate limiting and abuse controls.
- Render/GitHub Pages production download links must use `/decks/{id}.zip` and previews must use `/decks/{id}/index.html`. Do not switch the frontend back to `/api/jobs/{id}/download`; Render's edge has a known cross-origin `FileResponse` issue.
- `outputs/` and `data/jobs/` are runtime artifacts and are gitignored. Render's filesystem is ephemeral, so generated files disappear on deploy/restart/cold start.
- The backend job runner is a daemon thread in the FastAPI process. It is fine for MVP, not for production load.
- Public UI must only expose two views: `选模板` and `输入文稿`. Do not add or relink a separate template-library page.
- Avoid user-visible `html-ppt` / skill-origin wording in the website, API display data, or generated deck copy. Internal folder names and engine strings may remain where needed for compatibility.

## Git / Deployment Facts

- Remote: `git@github.com:fxt-gw-pb/pku_ppt_try.git`
- Main branch: `main`
- GitHub Pages frontend: `https://fxt-gw-pb.github.io/pku_ppt_try/`
- Render backend: `https://pku-ppt-try.onrender.com`
- Render auto-redeploys on push to `main`; GitHub Pages also rebuilds from root.

Before push-oriented work, check:

```bash
pwd
git status --short
git remote -v
git branch --show-current
```

Do not revert user changes. Avoid touching generated artifacts.

User preference: after code or website changes are completed and verified,
commit and push them to `origin/main` by default so GitHub Pages and Render can
pick them up. Still check status/remote/branch first, and never include secrets
or ignored runtime outputs.

## Current Product/UI State

- Brand: `fxt ppt`.
- Public Pages URL: `https://fxt-gw-pb.github.io/pku_ppt_try/`.
- The root page is a two-view static app:
  - `#templates`: select a template.
  - `#generate`: paste manuscript, generate, poll jobs, preview/download results.
- There is intentionally no separate template library page. The files `template-preview.html`, `web/template-preview.html`, `html-ppt-templates/index.html`, and `html-ppt-templates/templates/full-decks-index.html` were deleted.
- `server/app.py` must not mount `/html-ppt-templates` for public browsing.
- Template cards only have `使用模板`; do not re-add `预览` links unless the user explicitly asks to restore a third page.
- The template and generate views both include this donation note, with a clickable `.donation-trigger` opening the shared QR modal:
  `该网页暂时免费使用，生成 PPT 需要一定的 API tokens 花费，该费用由作者承担，请勿滥用，如果感到有用，也欢迎 打赏给作者 <=1 元的奖赏~`
- Donation QR image: `收款码/537a8a731804791d569387f56522fa2a.jpg`. FastAPI mounts `/收款码` for local preview.
- Generate view warning text:
  `PPT 生成需要约 30s，生成过程中切勿刷新页面，刷新页面也会丢失您的既往文件生成记录。`
- Export wording in the public UI should say `网页包和 PDF`, not `HTML/PPTX` except where explicitly explaining PPTX is unsupported.
- Generated job buttons are high contrast: `进入预览页` red filled, `下载网页包` light filled with red text/border.

## Local Development

Install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Mock CLI generation:

```bash
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
```

Backend + local frontend:

```bash
uvicorn server.app:app --reload --host 127.0.0.1 --port 8787
```

Then open:

```text
http://127.0.0.1:8787/
```

Local proxy gotcha from the previous handoff: if loopback `curl` fails via proxy, use:

```bash
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/health
```

## Schemas

There are two JSON shapes. Keep them separate.

Generic LLM output, validated by `src/schema/__init__.py`:

```json
{
  "title": "演示主标题",
  "subtitle": "GRADUATION DEFENSE / OPENING REPORT",
  "slides": [
    {
      "type": "cover | contents | section | content | closing",
      "title": "页面标题",
      "bullets": ["要点"],
      "layout": "optional PKU layout hint"
    }
  ]
}
```

PKU runtime input, consumed by `assets/runtime.js` and documented in `pku-red-defense-ppt/references/slides-json-schema.md`:

```json
{
  "meta": {},
  "chapters": [],
  "slides": [
    {
      "layout": "cover | contents | section-divider | image-analysis | chart-analysis | timeline | theory-cards | multi-card | framework | vs | swot | method | section-text | closing"
    }
  ]
}
```

`src/renderer/compile_to_pku()` is the bridge. It currently maps bullet-only content into:

- `multi-card`
- `theory-cards`
- `method`
- `timeline`
- `section-text`

Richer layouts such as `image-analysis`, `chart-analysis`, `framework`, `vs`, and `swot` need structured fields that the generic LLM contract does not currently collect. Extend the LLM prompt/schema first, then the renderer.

## Template Sync Rule

The PKU red visual template exists in two mirrored places:

- Root runtime used by `demo.html`: `deck-stage.js`, `assets/base.css`, `assets/runtime.js`, `assets/theme-pku-red.css`, `data/slides.json`
- Skill/export template used by generated decks: `pku-red-defense-ppt/assets/template/...`

If any template file changes, update both copies and verify they still match. Useful checks:

```bash
cmp -s deck-stage.js pku-red-defense-ppt/assets/template/deck-stage.js
cmp -s assets/runtime.js pku-red-defense-ppt/assets/template/assets/runtime.js
cmp -s assets/base.css pku-red-defense-ppt/assets/template/assets/base.css
cmp -s assets/theme-pku-red.css pku-red-defense-ppt/assets/template/assets/theme-pku-red.css
cmp -s data/slides.json pku-red-defense-ppt/assets/template/data/slides.json
```

The exporter copies `pku-red-defense-ppt/assets/template/`, not the root template files.

Imported full-deck templates are managed separately. Production assets live
under `templates/html-ppt/`; keep the exporter independent from
`html-ppt-templates/`, and do not expose that copied folder as a public template
gallery.

PKU red template-specific current behavior:

- The cover page no longer renders the old white metadata box for `汇报人`, `指导老师`, or `学院专业`.
- Content slides no longer auto-render `meta.school` in the lower-left footer.
- `DEFAULT_META`, root `data/slides.json`, and mirrored `pku-red-defense-ppt/assets/template/data/slides.json` no longer contain `X X X`, `X X X 教授`, or `X X 学院 · X X 专业` placeholders.

## Visual Rules

This is an academic PKU defense template, not a marketing deck.

- Canvas is 16:9, 1280 x 720.
- White content pages; PKU red `#9A0000` is the only strong accent.
- Red is reserved for nav highlights, ordinal numbers, key phrases, section-divider backgrounds, and cover/closing backgrounds.
- Cards use light borders and white fills; avoid heavy shadows.
- No glassmorphism, purple/blue tech gradients, dark hero pages, or landing-page card stacks.
- Charts, screenshots, diagrams, and anything with readable text must use `contain` or `diagram`, not cropped `cover`.

Reference files:

- `pku-red-defense-ppt/references/template-spec.md`
- `pku-red-defense-ppt/references/layout-selection.md`
- `pku-red-defense-ppt/references/image-rules.md`
- `pku-red-defense-ppt/references/slides-json-schema.md`

## Important Files

- `CLAUDE.md`: previous handoff and operational source of truth.
- `README.md`: user-facing setup and usage docs.
- `prompt.md`: original build brief.
- `.env.example`: public environment template.
- `server/app.py`: FastAPI API, job lifecycle, CORS, static mounts.
- `web/app.js`: keyless frontend, GitHub Pages backend URL selection, polling.
- `src/llm/deepseek.py`: DeepSeek OpenAI-compatible provider and strict JSON prompt.
- `src/llm/mock.py`: deterministic provider for keyless E2E tests.
- `src/schema/__init__.py`: generic LLM output validator.
- `src/renderer/__init__.py`: generic-to-PKU compiler.
- `src/renderer/xhs_white_editorial.py`: generic-to-imported-template renderer for the XHS template.
- `src/exporter/__init__.py`: copy template, write `data/slides.json`, zip deck.
- `src/templates/registry.py`: template registry used by API, CLI, and frontend.
- `scripts/generate.py`: CLI generation entrypoint.
- `pku-red-defense-ppt/scripts/validate_slides.py`: validator for PKU runtime JSON.
- `pku-red-defense-ppt/scripts/create_deck.py`: standalone skill materializer.

## API Behavior

Endpoints:

- `GET /api/health`
- `GET /api/templates`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/download` for legacy/curl use
- `GET /api/jobs/{job_id}/preview` for legacy/curl use
- `/decks/...` static output mount
- `/收款码/...` static mount for the donation QR image
- `/` static frontend mount from `web/`

Job states:

```text
pending -> running -> done | failed
```

Done jobs return:

```json
{
  "download_url": "/decks/{id}.zip",
  "preview_url": "/decks/{id}/index.html"
}
```

`POST /api/jobs` accepts `template_id`. Current values:

- `pku-red`: default, existing PKU JSON runtime.
- 15 imported full-deck templates.
  `xhs-white-editorial` has a dedicated renderer; the other imported templates
  use `src/renderer/html_ppt_generic.py` until they need template-specific
  refinement.

`src/templates/registry.py` intentionally hides `preview_url` from
`public_dict()` and maps internal engines to display values (`classic` or
`template`). Keep public API display data free of skill/source names.

## Frontend Duplication

There are two `index.html` files by design:

- Root `index.html`: GitHub Pages root, references `web/style.css` and `web/app.js`.
- `web/index.html`: local FastAPI static frontend, references sibling `style.css` and `app.js`.

Keep them in sync when changing the UI, adjusting paths as needed.

## Validation Checklist

After backend/pipeline changes, run at least:

```bash
python scripts/generate.py --provider mock --input examples/input.md --output outputs/demo
python pku-red-defense-ppt/scripts/validate_slides.py outputs/demo/data/slides.json
python scripts/generate.py --provider mock --template xhs-white-editorial --input examples/input.md --output outputs/xhs-demo
```

For API changes, start uvicorn and test:

```bash
curl --noproxy 127.0.0.1 http://127.0.0.1:8787/api/health
```

For template changes, also preview the deck over HTTP, not `file://`, because `runtime.js` fetches `data/slides.json`.

## Extension Notes

- Server-side PDF export: add Playwright in `_run_job()` after zip generation, load the generated deck, and write a landscape 1280x720 PDF. Return `pdf_url`.
- PPTX export: non-trivial. Either reimplement layouts in `python-pptx` or try headless browser/LibreOffice conversion.
- Persistent production outputs: move from local `outputs/` to S3/R2 and return signed URLs.
- Production queueing: replace daemon threads with Redis/RQ/Celery or another job system.
- Image generation: `image_prompt` exists in the generic schema but is currently unused.
