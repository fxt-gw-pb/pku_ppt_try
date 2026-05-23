# Deck Template Sources

Production template assets live here. Preview-only imports can exist elsewhere,
but exporters should depend on this directory.

## Current templates

- `pku-red` is managed by the existing skill bundle at
  `pku-red-defense-ppt/assets/template/`. It remains the default backend
  template and is intentionally not duplicated here.
- `html-ppt/xhs-white-editorial/` is the first imported html-ppt template.
  It uses shared html-ppt assets from `html-ppt/shared/assets/`.

## Rules

- Keep template assets separate from generated outputs.
- Do not make the backend depend on `html-ppt-templates/`; that folder is a
  local preview copy of the original skill.
- Add a template entry in `src/templates/registry.py` before exposing it in
  the API or frontend.

