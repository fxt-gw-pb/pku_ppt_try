# Visual Reference

These PNGs are **ground truth**, not loaded at runtime. Use them when deciding whether a generated deck looks correct.

| File | Layout | What to look for |
|---|---|---|
| `01-cover.png` | `cover` | Red full-bleed, big white title, presenter/advisor/school pills, motto strip, top-right sparse dot grid, bottom-right arrow |
| `deck-cover-preview.png` | `cover` | Higher-res cover preview for color/typography QA |
| `04-image-analysis.png` | `image-analysis` | Left image slot + right 2–4 numbered analysis items; top-right chapter nav with red underline on active |
| `07-chart-analysis.png` | `chart-analysis` | Left chart + right insight column with red ordinal heads |
| `08-timeline.png` | `timeline` | Horizontal stages with year/label, dots, body text |
| `timeline-r2.png` | `timeline` | Alt timeline composition reference |
| `11-framework.png` | `framework` | Linear node flow with tags; one `primary: true` node is red-headed |

Fuller archive of per-slide screens lives in the source repo's `_ref/screens/` — bring more into this folder only if a new layout reference is needed.
