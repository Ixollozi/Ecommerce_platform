# shapes/ — organic hero + below pipeline (curated)

```
shapes/
  paths/                      # locked dense SVG paths (source of truth)
  paths/below/                # About + New Arrivals figures
  organic_layouts.json        # hero layout meta (built)
  figma-pack.svg              # hero pack for Figma
  figma-pack-below.svg        # below pack for Figma
  calibrate.html
  calibrate-below.html
  inbox/                      # local drops only (gitignored except *.txt)
  approved/
    calibrated.svg            # last hero import snapshot
    figma-ref-raw.png         # hero design ref
    below-ref.png             # below design ref
    below-shapes-locked.svg   # below lock snapshot
    below_paths_meta.json
    mobile_slots.json
    shop_slots.json
    versions/
  _build_*.py / _import_*.py / _serve_*.py / _trace_*.py / _watch_*.py
```

**Do not commit:** `inbox/*` (except `*.txt`), `qa-*`, `*-debug*`, `*-trace-qa*`,
generated `mobile-preview.html` / `mobile-calibrate.html` / `mobile-pack.svg` /
`shop-calibrate.html`, one-off helpers.

**Hero**
- Desktop: `python themes/curated/shapes/_build_hero.py`
- Mobile slots: `python themes/curated/shapes/_serve_mobile_calibrate.py` → Save → `_build_mobile_pack.py`
- Shop overlay: `_serve_shop_calibrate.py` → `_build_shop_overlay.py`

**Below-fold (About + New Arrivals)**
1. Draft/pack: `python themes/curated/shapes/_build_below_pack.py`
2. Open `figma-pack-below.svg` / `calibrate-below.html` → light Figma fix
3. Export → `inbox/calibrated-below.svg` → «готово»
4. Import + build: `_import_calibrated_below.py` then `_build_below.py`
5. Optional watch: `_watch_below_calibrate.py`
