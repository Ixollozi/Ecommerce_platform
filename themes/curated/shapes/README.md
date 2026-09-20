# shapes/ — organic hero pipeline (curated)

Clean layout for Figma-calibrated paths → Django hero.

```
shapes/
  paths/                 # source of truth (dense SVG paths)
  organic_layouts.json   # layout meta + path copies (built)
  figma-pack.svg         # pack for user calibration in Figma
  calibrate.html         # short instructions
  inbox/                 # drop calibrated.svg here (gitignored)
  approved/
    figma-ref-raw.png    # design reference
    calibrated.svg       # last imported snapshot
  _build_figma_pack.py
  _import_calibrated.py
  _build_hero.py         # writes templates/partials/hero_board.html
```

**Do not commit:** `inbox/calibrated.svg`, `approved/qa-*`, debug `_*.py`, masks, WIP `01-*.svg`.

**Rebuild hero:** `python themes/curated/shapes/_build_hero.py`
