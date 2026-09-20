"""Mobile pack — portrait FRAME (not letterbox meet, not full-bleed stretch).

Same approved path geometry, each shape placed with uniform scale into a
phone slot around a central copy-safe zone. Cream breathes; shapes frame.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
PATHS = OUT / "paths"
TPL = Path(r"d:\Cursor\clothing_shop\themes\curated\templates\partials")
STATIC = Path(r"d:\Cursor\clothing_shop\themes\curated\static")

MW, MH = 390.0, 844.0

# Desktop bboxes from organic_layouts (x, y, w, h)
BBOX = {
    "A-header-lower": (-1.0, -1.0, 471.0, 176.0),
    "A-dark-top-left": (0.0, 0.0, 422.0, 137.0),
    "C-dark-upper": (400.0, 327.5, 624.0, 297.09),
    "C-dark-bottom": (388.0, 389.0, 636.0, 236.0),
    "F-photo-left": (-1.33, 149.55, 290.08, 561.95),
    "G-photo-top": (551.64, -0.74, 284.36, 195.74),
    "H-photo-right": (744.0, 0.0, 280.05, 364.63),
    "G-photo-bottom": (185.4, 421.95, 246.86, 287.27),
}

# Photo boxes (slightly padded) — desktop art space
PHOTO_BOX = {
    "F-photo-left": ("img/hero-left.jpg", -7.33, 143.55, 302.08, 573.95, "50% 28%"),
    "G-photo-top": ("img/hero-top.jpg", 545.64, -6.74, 296.36, 207.74, "50% 48%"),
    "H-photo-right": ("img/hero-right.jpg", 738.0, -6.0, 292.05, 376.63, "48% 40%"),
    "G-photo-bottom": ("img/hero-bl.jpg", 179.4, 415.95, 258.86, 299.27, "50% 45%"),
}

FILLS = {
    "A-header-lower": "#baaa93",
    "A-dark-top-left": "#2a2c2b",
    "C-dark-upper": "#c5b39d",
    "C-dark-bottom": "#2a2c2b",
    "F-photo-left": "#c5b49f",
    "G-photo-top": "#d9c9b4",
    "H-photo-right": "#a8977f",
    "G-photo-bottom": "#8f7a60",
}

# Default slots (x, y, w, h). Overridden by inbox/mobile_slots.json after calibrate.
DEFAULT_SLOTS = {
    "A-dark-top-left": (-18, -12, 210, 100),
    "A-header-lower": (-55, 28, 240, 155),
    "G-photo-top": (168, -20, 250, 185),
    "F-photo-left": (-75, 150, 225, 420),
    "H-photo-right": (248, 195, 175, 290),
    "G-photo-bottom": (-28, 545, 185, 215),
    "C-dark-upper": (195, 555, 220, 130),
    "C-dark-bottom": (-40, 670, 470, 210),
}


ORDER = (
    "A-header-lower",
    "A-dark-top-left",
    "C-dark-upper",
    "C-dark-bottom",
    "F-photo-left",
    "G-photo-top",
    "H-photo-right",
    "G-photo-bottom",
)


def load_slots() -> dict[str, tuple[float, float, float, float]]:
    """Prefer inbox (WIP calibrate), else approved/mobile_slots.json."""
    slots = {k: tuple(v) for k, v in DEFAULT_SLOTS.items()}
    for path in (
        OUT / "inbox" / "mobile_slots.json",
        OUT / "approved" / "mobile_slots.json",
    ):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("slots") or data.get("placed") or {}
        for k, v in raw.items():
            if k in slots and isinstance(v, (list, tuple)) and len(v) >= 4:
                slots[k] = (float(v[0]), float(v[1]), float(v[2]), float(v[3]))
        print(f"using calibrated slots from {path}")
        return slots
    return slots


def load_order() -> tuple[str, ...]:
    """Paint order back→front from inbox/approved, else default."""
    base = list(ORDER)
    for path in (
        OUT / "inbox" / "mobile_slots.json",
        OUT / "approved" / "mobile_slots.json",
    ):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        raw = data.get("order")
        if not isinstance(raw, list) or not raw:
            continue
        seen: list[str] = []
        for sid in raw:
            if sid in BBOX and sid not in seen:
                seen.append(sid)
        for sid in base:
            if sid not in seen:
                seen.append(sid)
        print(f"using calibrated layer order from {path}")
        return tuple(seen)
    return tuple(base)


COPY_SAFE = (52.0, 300.0, 286.0, 210.0)  # x, y, w, h


def path_d(name: str) -> str:
    text = (PATHS / f"{name}.svg").read_text(encoding="utf-8")
    m = re.search(r'\bd="([^"]+)"', text)
    if not m:
        raise SystemExit(f"no path in {name}.svg")
    return " ".join(m.group(1).split())


def fit_slot(bbox: tuple[float, float, float, float], slot: tuple[float, float, float, float]):
    """Map desktop bbox into phone slot with uniform scale (contain) + center."""
    bx, by, bw, bh = bbox
    sx, sy, sw, sh = slot
    scale = min(sw / bw, sh / bh)
    tw, th = bw * scale, bh * scale
    tx = sx + (sw - tw) / 2 - bx * scale
    ty = sy + (sh - th) / 2 - by * scale
    # Resulting placed rect in phone space
    px, py = sx + (sw - tw) / 2, sy + (sh - th) / 2
    return scale, tx, ty, (px, py, tw, th)


def photo_mask_uri(path: str, x: float, y: float, w: float, h: float) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x:g} {y:g} {w:g} {h:g}" preserveAspectRatio="none">'
        f'<path fill="#fff" d="{path}"/></svg>'
    )
    return "data:image/svg+xml," + quote(svg, safe="")


def main() -> None:
    slots = load_slots()
    order = load_order()
    transforms: dict[str, dict] = {}
    parts: list[str] = []

    for sid in order:
        scale, tx, ty, placed = fit_slot(BBOX[sid], slots[sid])
        transforms[sid] = {
            "scale": scale,
            "tx": tx,
            "ty": ty,
            "placed": list(placed),
            "slot": list(slots[sid]),
            "bbox": list(BBOX[sid]),
        }
        fill = FILLS[sid]
        op = 0.92 if "photo" in sid else 1.0
        d = path_d(sid)
        parts.append(
            f'  <g id="slot-{sid}" transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f})">\n'
            f'    <path id="{sid}" fill="{fill}" fill-opacity="{op}" d="{d}"/>\n'
            f"  </g>"
        )

    # Labels for pack review
    labels = []
    label_map = {
        "A-dark-top-left": "A dark top",
        "A-header-lower": "A tan rim",
        "G-photo-top": "G photo top",
        "F-photo-left": "F photo L",
        "H-photo-right": "H photo R",
        "G-photo-bottom": "Q photo BL",
        "C-dark-upper": "C sm",
        "C-dark-bottom": "B dark bottom",
    }
    for sid, lab in label_map.items():
        px, py, tw, th = transforms[sid]["placed"]
        labels.append(
            f'  <text class="lab" x="{px + tw * 0.5:.1f}" y="{py + th * 0.55:.1f}" '
            f'text-anchor="middle">{lab}</text>'
        )

    cx, cy, cw, ch = COPY_SAFE
    nav = "  <g id=\"nav-mock\">"
    for i in range(6):
        nav += f'<circle cx="{28 + i * 28}" cy="36" r="10" fill="#c5b49f"/>'
    nav += "</g>"

    copy = f"""  <g id="copy-mock" fill="#1e1f1e" text-anchor="middle">
    <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="none"
          stroke="#c44" stroke-width="1.5" stroke-dasharray="6 5" opacity="0.85"/>
    <text x="{MW/2:g}" y="{cy + 28}" class="safe" fill="#c44">COPY SAFE ZONE</text>
    <text x="{MW/2:g}" y="{cy + 88}" font-family="Georgia,serif" font-size="22"
          letter-spacing="0.1em">CURATED FOR</text>
    <text x="{MW/2:g}" y="{cy + 118}" font-family="Georgia,serif" font-size="22"
          letter-spacing="0.1em">THE DISCERNING</text>
    <rect x="{MW/2 - 118:g}" y="{cy + 140}" width="236" height="36" rx="18" fill="#b9a58b"/>
    <text x="{MW/2:g}" y="{cy + 163}" font-family="system-ui,sans-serif" font-size="10"
          fill="#fff" letter-spacing="0.12em" font-weight="600">EXPLORE THE COLLECTION</text>
  </g>"""

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MW:g} {MH:g}" width="{MW:g}" height="{MH:g}">
  <title>Curated — mobile portrait frame</title>
  <desc>Same paths, per-shape uniform scale into phone slots. No stretch, no letterbox strip.</desc>
  <style>
    .lab {{ font-family: system-ui,sans-serif; font-size: 11px; font-weight: 600;
           fill: #5a554c; letter-spacing: 0.04em; pointer-events: none; }}
    .safe {{ font-family: system-ui,sans-serif; font-size: 9px; letter-spacing: 0.08em; }}
    .cap {{ font-family: system-ui,sans-serif; font-size: 10px; font-weight: 600;
           fill: #6a655c; letter-spacing: 0.05em; }}
  </style>
  <rect width="{MW:g}" height="{MH:g}" fill="#f3efe7"/>
{chr(10).join(parts)}
{nav}
{copy}
{chr(10).join(labels)}
  <text class="cap" x="{MW/2:g}" y="22" text-anchor="middle">FRAME · same paths · portrait slots</text>
</svg>
"""
    (OUT / "mobile-pack.svg").write_text(svg, encoding="utf-8")

    # Photo placements: map photo box through same transform as its shape
    photos_meta = {}
    for pid, (src, bx, by, bw, bh, pos) in PHOTO_BOX.items():
        t = transforms[pid]
        s, tx, ty = t["scale"], t["tx"], t["ty"]
        # phone-space rect
        px, py, pw, ph = bx * s + tx, by * s + ty, bw * s, bh * s
        photos_meta[pid] = {
            "src": src,
            "x": px,
            "y": py,
            "w": pw,
            "h": ph,
            "object_position": pos,
            "pct": {
                "left": round(100 * px / MW, 4),
                "top": round(100 * py / MH, 4),
                "width": round(100 * pw / MW, 4),
                "height": round(100 * ph / MH, 4),
            },
            "mask_viewBox": [bx, by, bw, bh],
        }

    meta = {
        "mode": "frame",
        "phone": [MW, MH],
        "copy_safe": list(COPY_SAFE),
        "order": list(order),
        "transforms": {
            k: {
                "scale": round(v["scale"], 6),
                "tx": round(v["tx"], 3),
                "ty": round(v["ty"], 3),
                "placed": [round(x, 2) for x in v["placed"]],
            }
            for k, v in transforms.items()
        },
        "photos": photos_meta,
        "nav": {"x": 28, "y": 26, "n": 6, "gap": 28, "r": 10},
    }
    (OUT / "mobile_layout.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    # Live mobile board — one stacking context; order mixes solids + photos
    cls = {
        "F-photo-left": "cu-photo--Fleft",
        "G-photo-top": "cu-photo--Gtop",
        "H-photo-right": "cu-photo--Hright",
        "G-photo-bottom": "cu-photo--Gbottom",
    }
    layer_chunks: list[str] = [
        f'  <div class="cu-hero__cream" aria-hidden="true"></div>',
    ]
    for z, sid in enumerate(order):
        zi = 10 + z
        if sid in photos_meta:
            pm = photos_meta[sid]
            d = path_d(sid)
            vb = pm["mask_viewBox"]
            uri = photo_mask_uri(d, *vb)
            pct = pm["pct"]
            layer_chunks.append(
                f'  <figure class="cu-photo {cls[sid]}" style="'
                f'left:{pct["left"]}%;top:{pct["top"]}%;'
                f'width:{pct["width"]}%;height:{pct["height"]}%;'
                f"z-index:{zi};"
                f'--cu-pos:{pm["object_position"]};'
                f"-webkit-mask-image:url('{uri}');mask-image:url('{uri}');\">\n"
                f'    <img src="{{% static \'{pm["src"]}\' %}}?v=38" alt="" '
                f'draggable="false" decoding="async">\n'
                f"  </figure>"
            )
        else:
            t = transforms[sid]
            d = path_d(sid)
            layer_chunks.append(
                f'  <svg class="cu-layer cu-layer--solid" style="z-index:{zi}" '
                f'viewBox="0 0 {MW:g} {MH:g}" preserveAspectRatio="xMidYMid meet" '
                f'aria-hidden="true">\n'
                f'    <g transform="translate({t["tx"]:.3f} {t["ty"]:.3f}) '
                f'scale({t["scale"]:.6f})">\n'
                f'      <path id="m-{sid}" fill="{FILLS[sid]}" d="{d}"/>\n'
                f"    </g>\n"
                f"  </svg>"
            )

    board = f"""{{# mobile portrait frame — interleaved layers by calibrate order #}}
{{% load static %}}
<div class="cu-hero__layers" aria-hidden="true">
{chr(10).join(layer_chunks)}
</div>
"""
    TPL.mkdir(parents=True, exist_ok=True)
    (TPL / "hero_board_mobile.html").write_text(board, encoding="utf-8")

    # Preview HTML
    inline = svg.split("?>", 1)[-1].strip()
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Curated — mobile frame pack</title>
<style>
body{{margin:0;min-height:100svh;display:grid;place-items:center;gap:1rem;padding:1.25rem;
background:#1a1b1a;color:#f3efe7;font-family:system-ui,sans-serif}}
h1{{margin:0;font-size:1rem;letter-spacing:.04em}}
p{{margin:0;max-width:26rem;font-size:.82rem;line-height:1.45;opacity:.85;text-align:center}}
.phone{{width:min(390px,92vw);border-radius:28px;overflow:hidden;border:3px solid #3a3b3a;
box-shadow:0 24px 64px rgba(0,0,0,.45);background:#f3efe7}}
.phone svg{{display:block;width:100%;height:auto}}
.note{{max-width:26rem;font-size:.75rem;opacity:.7;border-left:3px solid #c5b39d;padding-left:.75rem}}
code{{color:#c5b39d}}
</style>
</head>
<body>
<h1>MOBILE · portrait FRAME</h1>
<p>Те же калиброванные path’ы. Каждый — свой scale в слот вокруг copy-зоны.
Заполняет телефон без letterbox-полоски и без растягивания.</p>
<div class="phone">{inline}</div>
<div class="note">Слои: <code>{' > '.join(order)}</code></div>
</body>
</html>
"""
    (OUT / "mobile-preview.html").write_text(html, encoding="utf-8")

    # Sync static
    STATIC_SH = STATIC / "shapes"
    STATIC_SH.mkdir(parents=True, exist_ok=True)
    for name in ("mobile-pack.svg", "mobile-preview.html", "mobile_layout.json"):
        (STATIC_SH / name).write_text((OUT / name).read_text(encoding="utf-8"), encoding="utf-8")

    print("ok frame pack")
    print("order:", " > ".join(order))
    for sid in order:
        t = transforms[sid]
        print(f"  {sid:18} s={t['scale']:.3f} placed={tuple(round(x,1) for x in t['placed'])}")


if __name__ == "__main__":
    main()
