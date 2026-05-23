# Image Rules

User-supplied images must never be stretched, distorted, or rendered illegibly. Choose `fit` deliberately.

## `fit` values

| `fit` | Behavior | Use for |
|---|---|---|
| `cover` (default) | Crop to fill the slot; aspect-ratio preserved | Photos, scene shots, campus / lab / portrait imagery |
| `contain` | Scale to fit without cropping; framed with light gray border | **Charts, plots, paper screenshots, figures with text** |
| `diagram` | Like `contain`, plus internal padding | Complex flow diagrams, schemas with fine detail |
| `logo` | `contain` for square / brand marks; framed | School / institution / lab logos |
| `fullBleed` | Fills the slot edge-to-edge with no frame | Background imagery only; use sparingly |

**Default decision tree:**

1. Does the image contain readable text or numbers? → `contain` (or `diagram` if it's a complex multi-node flowchart).
2. Is it a logo or institutional mark? → `logo`.
3. Is it a photo or scene? → `cover` (the default; you can omit `fit`).
4. Is it a background visual under no overlaid text? → `fullBleed`.

**Never use `cover` on a chart or paper screenshot.** Cropping numeric axes or paper figure captions makes the slide useless.

## JSON usage

```json
{
  "images": [
    {
      "src": "assets/media/co2-site.png",
      "alt": "CO₂ 吸附位点示意图",
      "fit": "diagram",
      "caption": "图 4.3 关键吸附位点 · 据 Smith et al. 2024 改绘"
    }
  ]
}
```

Fields:

- `src` (string, required): path relative to the deck root, typically `assets/media/<name>`.
- `alt` (string, optional): a11y text; defaults to empty.
- `fit` (string, optional): one of `cover` / `contain` / `diagram` / `logo` / `fullBleed`. Defaults to `cover`.
- `caption` (string, optional): rendered as a small line under the image. Use for `图 X.Y` figure captions.
- `focalPoint` ({ x, y } floats 0–1, optional): tunes the crop anchor for `cover`. `{ "x": 0.5, "y": 0.35 }` biases toward the upper-middle of the source image.

## Layouts that consume images

| Layout | Where it reads | How many |
|---|---|---|
| `image-analysis` | `images[0]` | One, left half |
| `chart-analysis` | `images[0]` (or legacy `chartImage`) | One, left half |
| All others (`cover`, `theory-cards`, …) | — | None — they are text-only |

If you want multiple images on one page, split into two `image-analysis` slides rather than overloading one.

## Source paths and the `media/` directory

- Put user images under the deck's `assets/media/` directory and reference them as `assets/media/<filename>`.
- Use lowercase-kebab filenames: `polymer-network.png`, not `Polymer Network (1).PNG`.
- Prefer `.png` for diagrams/charts and `.jpg`/`.jpeg` for photos.
- The validator (`scripts/validate_slides.py`) will flag any `src` that does not resolve to a file under the deck root.

## Captions

Every chart, schematic, and paper-figure image should carry a caption (`caption` field), formatted as `图 N.N <description> · <source-or-credit>`. Photos may go uncaptioned. Don't caption logos.

## Sample / placeholder media

The bundled `assets/template/assets/media/` ships with a few PKU-themed photos and generic diagrams. If a user provides no image but the chosen layout needs one, you may use:

- `world-map.png` — global / macro background
- `network-diagram.png` — generic network/graph for literature or collaboration figures
- `co2-site.png`, `reaction-coordinate.png` — generic chemistry diagrams (skip if domain mismatch)
- `pku-logo.png` — `logo` slot on cover

…and add a caption like `图 N.N 示意图占位 · 替换为您的实际数据图`. Do not ship a finished deck where placeholder images outnumber real ones — flag this to the user.
