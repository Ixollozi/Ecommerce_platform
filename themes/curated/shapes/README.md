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
    mobile_slots.json         # current mobile frame slots
    shop_slots.json           # desk+mob product tiles + catalog CTA
    versions/                 # archived mobile layouts
  _build_figma_pack.py
  _import_calibrated.py
  _build_hero.py              # → templates/partials/hero_board.html
  _build_mobile_pack.py       # → hero_board_mobile.html from approved slots
  _serve_mobile_calibrate.py  # http://127.0.0.1:8767/
  _serve_shop_calibrate.py    # http://127.0.0.1:8768/
  _build_shop_overlay.py      # → templates/partials/hero_shop.html
```

**Do not commit:** `inbox/*` (except `*.txt`), `qa-*`, generated
`mobile-preview.html` / `mobile-calibrate.html` / `mobile-pack.svg` /
`shop-calibrate.html`.

**Rebuild desktop hero:** `python themes/curated/shapes/_build_hero.py`  
**Rebuild mobile from slots:** `python themes/curated/shapes/_build_mobile_pack.py`  
**Calibrate mobile:** `python themes/curated/shapes/_serve_mobile_calibrate.py` → Save → rebuild.  
**Shop overlay:** `python themes/curated/shapes/_serve_shop_calibrate.py` → Save →
`python themes/curated/shapes/_build_shop_overlay.py` (or say «готово»).
