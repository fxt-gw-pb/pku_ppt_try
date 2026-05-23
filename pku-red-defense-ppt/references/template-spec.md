# Template Spec — Visual Language

Read this before adjusting any CSS or before deciding whether a slide composition is "on brand."

## Canvas

- **Aspect ratio:** 16:9.
- **Design size:** 1280 × 720 px (set on `<deck-stage width="1280" height="720">`).
- `deck-stage.js` auto-scales the canvas to the viewport with `transform: scale()` and letterboxes against `#1a1a1a`.
- Print: each `<section.slide>` lays out one page at design size — `Ctrl/Cmd+P → Save as PDF` is the supported export.

## Color tokens (`assets/theme-pku-red.css`)

| Token | Value | Use |
|---|---|---|
| `--pku-red` | `#9A0000` | Primary accent — nav underline, ordinals, `<em>`, section-divider bg, cover bg |
| `--pku-red-deep` | `#7A0000` | Darker red shadow / depth in section-divider |
| `--red-2` | `#C4373D` | Secondary red — sparing |
| `--red-3` | `#EE6E7A` | Tint, e.g. tag/pill backgrounds |
| `--red-4` | `#E54C5E` | Tint variant |
| `--accent-green` | `#75BD42` | Reserved — almost never used |
| `--accent-teal` | `#30C0B4` | Reserved — almost never used |
| `--text` | `#1A1A1A` | Body copy |
| `--text-muted` | `#5A5A5A` | Captions, eyebrows |
| `--text-light` | `#8A8A8A` | Page numbers, footer |
| `--gray-50…300` | greys | Card borders, rules, fills |
| `--white` | `#FFFFFF` | Content page background |

**Hard rule:** red is reserved for the items in the `--pku-red` row above. Do not introduce gradients, blues, purples, or saturated tech palettes.

## Typography

- Font stack (display + body, identical):
  `"Source Han Sans SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", sans-serif`
- Mono (rare): `"JetBrains Mono", "SF Mono", Consolas, monospace`
- Type scale (1280×720 base, in px): cover title 56 / cover subtitle 20 / section number 200 / section title 64 / headline 32 / body 20 / small 17 / tiny 15 / nav 17 / page-num 17.

Body copy lives in the 15–32 px band. Avoid going below 15 or above 32 outside cover / section-divider.

## Shared chrome (content pages)

Every layout EXCEPT `cover`, `contents`, `section-divider`, `closing` renders this chrome via `runtime.js → chrome()`:

| Slot | Source field | Notes |
|---|---|---|
| Top-left | `sectionTitle` + `sectionTitleEn` | Small section tag, e.g. `1.1 选题背景 / RESEARCH BACKGROUND` |
| Top-right | `chapterIndex` ↔ `deck.chapters[]` | Five-segment nav; active item gets red bold underline |
| Below chrome | `top-rule` | Thin red horizontal rule |
| Title area | `headline` (+ optional `subheadline`) | 32 px; supports rich text |
| Bottom-right | auto page number | Only content pages counted; chapter dividers do not advance the counter |
| Bottom-left | `footerTag` ‖ `meta.school` | Org/department footer |

Setting `chapterIndex` is what activates the right chapter in the top nav — never omit it on content pages.

## Cover / divider / closing

- **`cover`**: red background, large title, presenter/advisor/school pills, motto strip, big right-arrow accent, sparse decorative dot grid top-right. Pulls from `deck.meta` by default.
- **`section-divider`**: red full-bleed, huge `200px` chapter number, chapter title in white, optional 3 bullets. No page number, no chrome.
- **`closing`**: same red world as cover. Title (`感谢您的倾听！`), subtitle (`THANK YOU FOR LISTENING`), single closing message, presenter + date in footer.

## Style do-nots

| ❌ Don't | ✅ Do instead |
|---|---|
| Landing-page hero layouts, marketing card stacks | Paper-grade card grids with light borders |
| Glassmorphism, frosted blurs | Solid white / `--gray-50` fills |
| Purple/blue tech gradients | Single red accent on white |
| Dark mode hero pages | White content pages, red dividers only |
| Heavy box-shadows | `1px solid var(--gray-200)` borders, no shadows |
| Photo full-bleed under text | Photo in an image-slot with caption, text alongside |
| English-only typography | Chinese display font as primary, English as secondary kicker |

## Adding a new layout

1. Add a function `layouts.myLayout = (s, ctx) => \`${chrome(s, ctx)} <div class="content">…</div>\`` in `assets/runtime.js`.
2. Add `.layout-myLayout .content { … }` rules to `assets/base.css`. Reuse `--pad-x`, `--content-top`, and existing card / item classes wherever possible.
3. Document the new layout's fields in `references/slides-json-schema.md` and its triggering content in `references/layout-selection.md`.
