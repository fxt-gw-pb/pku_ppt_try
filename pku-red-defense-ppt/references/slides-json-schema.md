# `data/slides.json` Schema

The runtime (`assets/runtime.js`) consumes this JSON. Unknown fields are ignored silently; missing required fields render as empty strings. **The validator (`scripts/validate_slides.py`) enforces required fields.**

## Top-level shape

```json
{
  "meta": { ... },
  "chapters": [ ... ],   // 3–6 entries
  "slides":   [ ... ]    // ordered slide list
}
```

## `meta` (object, optional but recommended)

Powers the cover, closing, and bottom-left footer.

| Field | Type | Used by | Notes |
|---|---|---|---|
| `title` | string | cover, fallback for `slides[].title` | Main deck title |
| `subtitle` | string | cover | English / bilingual subtitle line |
| `presenter` | string | cover, closing | 汇报人 |
| `advisor` | string | cover, closing | 指导老师 |
| `school` | string | cover, content footer | 学院 · 专业 |
| `date` | string | cover, closing | Free text, e.g. `2026 年 5 月` |
| `motto` | string | cover | 校训 / one-line caption |
| `logo` | string | cover, closing | Relative path, e.g. `assets/media/pku-logo.png` |

## `chapters` (array of 3–6 entries)

Each entry is either a string (title only) or an object:

```json
{ "title": "背景和意义", "subtitle": "Background & Significance" }
```

The string subtitle is shown under the chapter title in the `contents` layout, and the title appears in the top-right chapter nav on every content page.

## `slides` (array)

Every slide has:

| Field | Type | Required | Notes |
|---|---|---|---|
| `layout` | string | yes | One of the layouts below |
| `label` | string | no | Used in thumbnail rail and screen labels |
| `chapterIndex` | number | content layouts only | 0-based index into `chapters[]`; required for chapter nav to highlight |
| `sectionTitle` | string | content layouts only | Top-left section tag, e.g. `1.1 选题背景` |
| `sectionTitleEn` | string | optional | English subline under section tag |
| `headline` | string | content layouts | Big page title; supports rich text |
| `subheadline` | string | optional | Smaller line under headline |
| `footerTag` | string | optional | Overrides `meta.school` for the footer |
| `className` | string | optional | Extra CSS class on the `<section>` |

Layout-specific fields are listed per-layout below.

## Rich-text vocabulary

These run through `runtime.js → rich()`. Everything else is HTML-escaped.

| Markup | Renders as |
|---|---|
| `**关键短语**` | `<em>…</em>` (red emphasis) |
| `<em>关键短语</em>` | red emphasis |
| `<span class="accent">CO₂</span>` | red emphasis |
| `<br>` | line break |

Use sparingly. Two or three accents per headline maximum; one per body paragraph.

## Layouts

### `cover`
Cover page. Pulls everything from `meta`. Optional per-slide overrides:
- `title` (string), `subtitle` (string).

### `contents`
Five-segment table of contents.
- Uses `deck.chapters` by default; override with `chapters` field on the slide.
- Optional `note` (string) — meta line below the title block.

### `section-divider`
Red full-bleed chapter intro. No chrome, not page-numbered.
- `chapterIndex` (number, required)
- `points` (string[], up to 3) — bullet list shown right of the big number
- Optional `title` / `titleEn` to override the chapter title.

### `image-analysis`
Left image, right numbered analysis items.
- `images` (array, uses `images[0]`) — see image rules
- `items[]` of `{ title, body }`

### `chart-analysis`
Left chart / data figure, right insight blocks.
- `images` (uses `images[0]`; legacy `chartImage` also accepted)
- `insights[]` of `{ title, body }`

### `timeline`
Horizontal timeline / staged plan.
- `steps[]` of `{ label, title, body }`. 2–6 entries recommended.

### `theory-cards`
Three or four red-headed theory cards.
- `cards[]` of `{ title, label?, body }`. 2–4 entries.

### `multi-card`
Numbered content cards (research contents, innovations, etc.).
- `cards[]` of `{ title, body, tag? }`
- `cols` (optional number) — force column count.

### `framework`
Linear-flow framework with node tags. Used for 技术路线 / 研究框架.
- `nodes[]` of `{ title, body, tags?: string[], primary?: boolean }`

### `vs`
Two-column comparison.
- `leftKicker`, `leftTitle`, `leftItems[]`
- `rightKicker`, `rightTitle`, `rightItems[]`
- Items are either `{ title, body }` or strings.

### `swot`
Four-quadrant SWOT.
- `strengths[]`, `weaknesses[]`, `opportunities[]`, `threats[]` — arrays of strings (rich text OK).
- Optional `*Title` overrides for each quadrant.

### `method`
Research-method cards.
- `methods[]` of `{ title, en?, body }`
- Optional `cols`.

### `section-text`
Long-form conclusion / outlook / limitations text.
- `blocks[]` of `{ label, text }`
- `sideMark` (string, e.g. `"01"`), `sideMeta` (string, e.g. `"Chapter Five"`).

### `closing`
Thank-you page in cover style. Pulls from `meta`. Optional `title`, `subtitle`, `message`.

## Minimal example

```json
{
  "meta": {
    "title": "示例论文答辩",
    "presenter": "张三",
    "advisor": "李四 教授",
    "school": "化学与分子工程学院 · 物理化学",
    "date": "2026 年 6 月",
    "motto": "爱国 · 进步 · 民主 · 科学",
    "logo": "assets/media/pku-logo.png"
  },
  "chapters": [
    { "title": "背景和意义", "subtitle": "Background & Significance" },
    { "title": "综述和评述", "subtitle": "Literature Review" },
    { "title": "思路和内容", "subtitle": "Approach & Content" },
    { "title": "过程和方法", "subtitle": "Process & Method" },
    { "title": "成果与展望", "subtitle": "Results & Outlook" }
  ],
  "slides": [
    { "layout": "cover" },
    { "layout": "contents" },
    { "layout": "section-divider", "chapterIndex": 0,
      "points": ["宏观背景", "核心问题", "理论意义"] },
    { "layout": "image-analysis", "chapterIndex": 0,
      "sectionTitle": "1.1 选题背景",
      "sectionTitleEn": "RESEARCH BACKGROUND",
      "headline": "全球 <span class=\"accent\">碳中和</span> 议程推动 CO₂ 转化研究",
      "images": [{ "src": "assets/media/world-map.png", "fit": "contain",
                   "caption": "图 1.1 全球政策推进时间线" }],
      "items": [
        { "title": "外部驱动", "body": "政策、产业与社会的三重推动力。" },
        { "title": "现有局限", "body": "现有方法在 **稳定性** 与 **成本** 上仍受限。" },
        { "title": "新机遇",   "body": "新催化体系打开了可调性空间。" }
      ] },
    { "layout": "closing" }
  ]
}
```

For a fuller worked example covering all layouts, see the bundled `assets/template/data/slides.json`.

## Loading the data

- Default: served file at `data/slides.json`, picked up by `<deck-stage data-deck="data/slides.json">`.
- Inline (no server): before `runtime.js` runs, set `window.__PKU_DECK_INLINE = { meta, chapters, slides }`. Useful for single-file builds.
