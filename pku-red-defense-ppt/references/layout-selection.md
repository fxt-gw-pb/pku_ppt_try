# Layout Selection

Map user content to the right layout. Pick the **first** matching row.

## Content-type → layout

| User says / content is | Layout | Key signal |
|---|---|---|
| Title slide / opening | `cover` | First slide; pulls from `meta` |
| Table of contents / 目录 | `contents` | Second slide, lists chapters |
| Chapter intro (第 N 章 / Part N) | `section-divider` | Numbered chapter handover; 0–3 bullets |
| **Background**, 意义, 现状 with a supporting **photo or scene image** | `image-analysis` | Photo/scene + 2–4 numbered analysis items |
| **Data figure**, 文献图谱, **chart**, distribution, statistical comparison | `chart-analysis` | Chart/figure + 2–4 insights |
| **Timeline**, 技术演进, 研究计划阶段, project schedule | `timeline` | 2–6 sequential time points |
| **Theoretical foundations**, prior theories, conceptual buckets | `theory-cards` | 2–4 named theories / approaches |
| **Research contents**, 研究内容, 创新点, contributions, sub-projects | `multi-card` | 3–4 parallel items with short bodies |
| **Research framework**, 总体框架, 技术路线 (flow), 闭环, pipeline | `framework` | 4–6 connected steps in a flow |
| **Comparison** of two paths / approaches (old vs new, ours vs theirs) | `vs` | Exactly two columns being contrasted |
| **SWOT** analysis | `swot` | Explicit S/W/O/T quadrants |
| **Research methods**, methodology stack | `method` | 3–4 named methods, possibly with English labels |
| **Conclusions**, 不足, 展望, outlook, prose-heavy summary | `section-text` | Multi-paragraph reflective text |
| Thank-you slide / 致谢 | `closing` | Final slide |

## Default deck shape

For a typical 论文答辩 with the canonical five chapters, the **minimum viable deck** is ~13 slides:

```
01  cover
02  contents
03  section-divider                    Chapter 1 背景和意义
04  image-analysis                     1.1 选题背景
05  theory-cards or section-text       1.2 研究意义
06  section-divider                    Chapter 2 综述和评述
07  chart-analysis                     2.1 国内外现状
08  timeline                           2.2 技术演进
09  theory-cards                       2.3 文献评述
10  section-divider                    Chapter 3 思路和内容
11  framework                          3.1 总体框架
12  multi-card                         3.2 研究内容
13  vs  or  swot                       3.3 路径对比 / SWOT
14  section-divider                    Chapter 4 过程和方法
15  method                             4.1 研究方法
16  timeline                           4.2 技术路线
17  image-analysis                     4.3 实验设计
18  section-divider                    Chapter 5 成果与展望
19  section-text                       5.1 主要结论
20  multi-card                         5.2 创新点
21  section-text                       5.3 不足与展望
22  closing
```

The bundled `assets/template/data/slides.json` is exactly this shape — use it as the starting scaffold for any new defense deck.

## Picking between similar layouts

**`image-analysis` vs `chart-analysis`**: photo or scene image → `image-analysis`. Chart, plot, paper figure, network diagram → `chart-analysis`. The difference is mostly framing/captioning style.

**`theory-cards` vs `multi-card`**: cards with a *theoretical / methodological* identity (concepts, named theories) → `theory-cards` (gets a red `理论 0N · THEORY` head). Cards that are *parallel items of work* (sub-projects, innovations, contributions) → `multi-card` (gets a numbered ordinal).

**`timeline` vs `framework`**: real time axis (years, semesters S1–S6) → `timeline`. Logical pipeline with no time → `framework`.

**`vs` vs `swot`**: exactly two things being contrasted → `vs`. Internal/external × positive/negative analysis → `swot`.

**`section-text` vs `multi-card`**: long prose with rationale, hedging, future work → `section-text`. Short parallel bullets where each item is a discrete thing → `multi-card`.

## Slide-count guidance

- **15–20 minute defense**: 20–25 slides total, ~4 content slides per chapter.
- **5–8 minute opening report**: 12–15 slides, ~2 content slides per chapter, possibly drop one chapter.
- **Lab meeting / 中期汇报**: 18–22 slides, heavy on `chart-analysis`, `timeline`, `multi-card`.

Whenever the user gives a slide budget, distribute roughly evenly across chapters and bias content layouts toward `image-analysis` / `chart-analysis` if they provide images, toward `multi-card` / `theory-cards` if they don't.

## When the user provides only text

If there are no user images at all, still use `image-analysis` / `chart-analysis` for the bullets they fit — fill the image slot with a placeholder from `assets/media/` (e.g. `world-map.png`, `network-diagram.png`) and add a caption noting the placeholder. Do not silently drop content into `multi-card` just because images are missing; the page rhythm matters.
