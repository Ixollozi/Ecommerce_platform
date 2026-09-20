"""Build self-contained Figma pack SVG (ref embedded + editable named paths)."""
from __future__ import annotations

import base64
import json
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
REF = Path(r"d:\Cursor\clothing_shop\themes\curated\static\img\_ref-hero.png")

data = json.loads((OUT / "organic_layouts.json").read_text(encoding="utf-8"))
hero = data["hero"]
b64 = base64.b64encode(REF.read_bytes()).decode("ascii")

EDIT = [
    "A-dark-top-left",
    "B-tan-left",
    "C-dark-bottom",
    "E-cream-right",
    "F-photo-left",
    "G-photo-top",
    "H-photo-right",
    "I-photo-bl",
]
stroke = {
    "A-dark-top-left": "#00e5ff",
    "B-tan-left": "#00e5ff",
    "C-dark-bottom": "#00e5ff",
    "E-cream-right": "#00e5ff",
    "F-photo-left": "#ff1744",
    "G-photo-top": "#ff1744",
    "H-photo-right": "#ff1744",
    "I-photo-bl": "#ff1744",
}

lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    'viewBox="0 0 1024 625" width="1024" height="625">',
    f'  <image id="REF" width="1024" height="625" href="data:image/png;base64,{b64}"/>',
    '  <g id="SHAPES">',
]
for sid in EDIT:
    s = hero[sid]
    col = stroke[sid]
    lines.append(
        f'    <path id="{sid}" fill="none" stroke="{col}" stroke-width="2" d="{s["path"]}"/>'
    )
lines += ["  </g>", "</svg>", ""]

pack = OUT / "figma-pack.svg"
pack.write_text("\n".join(lines), encoding="utf-8")
print("wrote", pack, "MB", round(pack.stat().st_size / 1e6, 2))

inbox = OUT / "inbox"
inbox.mkdir(exist_ok=True)
(inbox / "DROP_CALIBRATED_SVG_HERE.txt").write_text(
    "Save from Figma as calibrated.svg into this folder, then tell agent: готово\n",
    encoding="utf-8",
)
print("inbox", inbox)
