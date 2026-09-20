# shapes/ — organic hero pipeline (curated)

```
shapes/
  paths/                      # source of truth (dense SVG paths)
  organic_layouts.json        # layout meta (built)
  figma-pack.svg              # pack for Figma calibration
  calibrate.html              # Figma instructions
  inbox/                      # local drops only (gitignored)
  approved/
    calibrated.svg            # last imported desktop snapshot
    figma-ref-raw.png         # design reference
    mobile_slots.json         # current mobile slot layout (v2)
    versions/                 # mobile_slots_v1.json, v2, …
  _build_figma_pack.py
  _import_calibrated.py
  _build_hero.py              # → templates/partials/hero_board.html
  _build_mobile_pack.py       # → hero_board_mobile.html from approved slots
  _serve_mobile_calibrate.py  # local UI: http://127.0.0.1:8767/
```

**Do not commit:** `inbox/*`, `qa-*`, generated `mobile-preview.html` / `mobile-calibrate.html` / `mobile-pack.svg`.

**Rebuild desktop hero:** `python themes/curated/shapes/_build_hero.py`  
**Rebuild mobile from slots:** `python themes/curated/shapes/_build_mobile_pack.py`  
**Calibrate mobile:** `python themes/curated/shapes/_serve_mobile_calibrate.py` → Save → copy/update `approved/mobile_slots.json` → rebuild.
