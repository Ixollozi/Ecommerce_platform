"""v18 — full-bleed shapes + scroll bleed past artboard fold.

Artboard fold stays 1024×625 (nav/copy %). Paths that extend past y=625
(Figma bottom lobes) keep their geometry; SVG viewBox + CSS board height
include that bleed so shapes do not look cropped on scroll.

Photos live in an HTML layer (object-fit: cover + object-position) masked
to the organic paths. They must NOT sit inside the preserveAspectRatio=none
shapes SVG — that non-uniform scale stretches bitmaps.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from urllib.parse import quote

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
TPL = Path(r"d:\Cursor\clothing_shop\themes\curated\templates")
STATIC = Path(r"d:\Cursor\clothing_shop\themes\curated\static")

ART_W = 1024.0
ART_H = 625.0

FILLS = {
    "D-cream-center": "#f3efe7",
    "A-header-lower": "#baaa93",
    "A-dark-top-left": "#2a2c2b",
    # Tan rim above charcoal — Figma-sampled (~197,179,157), not header #baaa93.
    # Flat y≈625 closure is clipped in build.
    "C-dark-upper": "#c5b39d",
    "C-dark-bottom": "#2a2c2b",
}

# Image boxes from approved/hero-preview.svg (artboard space, slight pad)
# object_position: center subject in the mask without stretch (cover crop).
PHOTO_BOX = {
    "F-photo-left": ("img/hero-left.jpg", -7.33, 143.55, 302.08, 573.95, "50% 28%"),
    "G-photo-top": ("img/hero-top.jpg", 523.11, -6.74, 296.36, 207.74, "50% 48%"),
    "H-photo-right": ("img/hero-right.jpg", 738.0, -6.0, 292.05, 376.63, "48% 40%"),
    "G-photo-bottom": ("img/hero-bl.jpg", 179.4, 415.95, 258.86, 299.27, "50% 45%"),
}


def photo_mask_data_uri(path_d: str, x: float, y: float, w: float, h: float) -> str:
    """SVG mask that stretches with the photo box (matches shapes none-scale)."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x:g} {y:g} {w:g} {h:g}" preserveAspectRatio="none">'
        f'<path fill="#fff" d="{path_d}"/></svg>'
    )
    return "data:image/svg+xml," + quote(svg, safe="")

# Paths that participate in the live hero (bleed ymax is taken from these)
HERO_PATH_IDS = (
    "A-header-lower",
    "A-dark-top-left",
    "C-dark-upper",
    "C-dark-bottom",
    "F-photo-left",
    "G-photo-top",
    "H-photo-right",
    "G-photo-bottom",
)


def path_from_svg(name: str) -> str:
    text = (OUT / "paths" / f"{name}.svg").read_text(encoding="utf-8")
    m = re.search(r'\bd="([^"]+)"', text)
    if not m:
        raise SystemExit(f"no path in {name}.svg")
    return " ".join(m.group(1).split())


def path_ymax(d: str) -> float:
    """Max Y from path — tolerant tokenizer (numbers may glue to commands)."""
    tokens = re.findall(
        r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d
    )
    x = y = 0.0
    cmd = None
    i = 0
    ymax = ART_H

    def take() -> float:
        nonlocal i
        while i < len(tokens) and re.match(r"[A-Za-z]", tokens[i]):
            # glued / unexpected command — stop this take
            raise ValueError("cmd")
        if i >= len(tokens):
            raise ValueError("eof")
        v = float(tokens[i])
        i += 1
        return v

    while i < len(tokens):
        t = tokens[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t
            i += 1
            continue
        if cmd is None:
            i += 1
            continue
        abs_cmd = cmd.isupper()
        c = cmd.upper()
        try:
            if c == "H":
                n = take()
                x = n if abs_cmd else x + n
            elif c == "V":
                n = take()
                y = n if abs_cmd else y + n
                ymax = max(ymax, y)
            elif c in "MLT":
                nx, ny = take(), take()
                x = nx if abs_cmd else x + nx
                y = ny if abs_cmd else y + ny
                ymax = max(ymax, y)
            elif c == "C":
                nums = [take() for _ in range(6)]
                for j in range(0, 6, 2):
                    px, py = nums[j], nums[j + 1]
                    if not abs_cmd:
                        px, py = x + px, y + py
                    x, y = px, py
                    ymax = max(ymax, y)
            elif c == "S":
                nums = [take() for _ in range(4)]
                for j in range(0, 4, 2):
                    px, py = nums[j], nums[j + 1]
                    if not abs_cmd:
                        px, py = x + px, y + py
                    x, y = px, py
                    ymax = max(ymax, y)
            elif c == "Q":
                nums = [take() for _ in range(4)]
                for j in range(0, 4, 2):
                    px, py = nums[j], nums[j + 1]
                    if not abs_cmd:
                        px, py = x + px, y + py
                    x, y = px, py
                    ymax = max(ymax, y)
            elif c == "A":
                _rx, _ry, _rot, _la, _sw, nx, ny = (take() for _ in range(7))
                x = nx if abs_cmd else x + nx
                y = ny if abs_cmd else y + ny
                ymax = max(ymax, y)
            else:
                i += 1
        except ValueError:
            # Malformed segment — skip to next command letter
            while i < len(tokens) and not re.match(r"[A-Za-z]", tokens[i]):
                i += 1
    return ymax


def main() -> None:
    paths = {
        "A-header-lower": path_from_svg("A-header-lower"),
        "A-dark-top-left": path_from_svg("A-dark-top-left"),
        "C-dark-upper": path_from_svg("C-dark-upper"),
        "C-dark-bottom": path_from_svg("C-dark-bottom"),
        "F-photo-left": path_from_svg("F-photo-left"),
        "G-photo-top": path_from_svg("G-photo-top"),
        "H-photo-right": path_from_svg("H-photo-right"),
        "G-photo-bottom": path_from_svg("G-photo-bottom"),
    }

    ymax = max(path_ymax(paths[sid]) for sid in HERO_PATH_IDS)
    # Small pad so stroke/AA never clips the lobe tip
    vb_h = max(ART_H, math.ceil(ymax + 2.0))
    # Full bleed height so cream does not hard-cut shapes that straddle y=625
    paths["D-cream-center"] = f"M0 0H{ART_W:g}V{vb_h:g}H0Z"

    layouts = json.loads((OUT / "organic_layouts.json").read_text(encoding="utf-8"))
    hero = layouts["hero"]
    for sid, d in paths.items():
        if sid not in hero:
            hero[sid] = {}
        hero[sid]["path"] = d
        if sid in FILLS:
            hero[sid]["fill"] = FILLS[sid]
        hero[sid].pop("stripe_lift", None)
        hero[sid].pop("stripe_drop", None)

    for sid, (src, x, y, w, h, pos) in PHOTO_BOX.items():
        if sid not in hero:
            hero[sid] = {}
        hero[sid]["photo"] = {
            "src": src,
            "box": [x, y, w, h],
            "object_position": pos,
        }

    layouts["hero"] = hero
    layouts["_meta"]["version"] = 18
    layouts["_meta"]["artboard"] = [0, 0, ART_W, ART_H]
    layouts["_meta"]["board"] = [ART_W, float(vb_h)]
    layouts["_meta"]["viewBox"] = [0, 0, ART_W, float(vb_h)]
    layouts["_meta"]["note"] = (
        "full-bleed none shapes; HTML photos cover+mask; "
        f"scroll bleed viewBox H={vb_h:g} (artboard {ART_H:g})"
    )

    cache = "v=38"
    # Hide flat artboard closure of upper (path ends with H at y≈624.6).
    # Stripe = natural peek of C-dark-upper under C-dark-bottom (thick right → thin left).
    upper_clip_h = 612
    lines = [
        "{# v18 — full-bleed shapes + HTML photo masks (no SVG image stretch) #}",
        "{% load static %}",
        f'<svg class="cu-hero__shapes" viewBox="0 0 {ART_W:g} {vb_h:g}" '
        f'preserveAspectRatio="none" aria-hidden="true">',
        "  <defs>",
        f'    <clipPath id="clip-C-dark-upper">'
        f'<rect x="-40" y="-40" width="{ART_W + 80:g}" height="{upper_clip_h + 40}"/>'
        f"</clipPath>",
        "  </defs>",
        '  <g id="bg-cream">',
        f'    <path id="D-cream-center" fill="{FILLS["D-cream-center"]}" '
        f'd="{paths["D-cream-center"]}"/>',
        "  </g>",
        '  <g id="group-header" data-figma="хедер меню">',
        f'    <path id="A-header-lower" fill="{FILLS["A-header-lower"]}" '
        f'd="{paths["A-header-lower"]}"/>',
        f'    <path id="A-dark-top-left" fill="{FILLS["A-dark-top-left"]}" '
        f'd="{paths["A-dark-top-left"]}"/>',
        "  </g>",
        '  <g id="group-bottom" data-figma="Низ главного экрана">',
        f'    <path id="C-dark-upper" fill="{FILLS["C-dark-upper"]}" '
        f'clip-path="url(#clip-C-dark-upper)" '
        f'd="{paths["C-dark-upper"]}"/>',
        f'    <path id="C-dark-bottom" fill="{FILLS["C-dark-bottom"]}" '
        f'd="{paths["C-dark-bottom"]}"/>',
        "  </g>",
        "</svg>",
        "",
        '<div class="cu-hero__photos" aria-hidden="true">',
    ]
    for sid, (src, x, y, w, h, pos) in PHOTO_BOX.items():
        mask = photo_mask_data_uri(paths[sid], x, y, w, h)
        left = x / ART_W * 100.0
        top = y / vb_h * 100.0
        width = w / ART_W * 100.0
        height = h / vb_h * 100.0
        short = sid.replace("photo-", "").replace("-", "")
        lines += [
            f'  <figure class="cu-photo cu-photo--{short}" '
            f'style="left:{left:.4f}%;top:{top:.4f}%;'
            f"width:{width:.4f}%;height:{height:.4f}%;"
            f"--cu-pos:{pos};"
            f"-webkit-mask-image:url('{mask}');"
            f"mask-image:url('{mask}');\">",
            f'    <img src="{{% static \'{src}\' %}}?{cache}" alt="" '
            f'draggable="false" decoding="async">',
            "  </figure>",
        ]
    lines += ["</div>"]
    (TPL / "partials" / "hero_board.html").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    dump = json.dumps(layouts, indent=2, ensure_ascii=False)
    (OUT / "organic_layouts.json").write_text(dump, encoding="utf-8")
    (STATIC / "shapes" / "organic_layouts.json").write_text(dump, encoding="utf-8")

    # Keep CSS --cu-vb-h in sync with computed bleed (once-and-for-all)
    css_path = STATIC / "styles.css"
    css = css_path.read_text(encoding="utf-8")
    css2, n = re.subn(
        r"(--cu-vb-h:\s*)\d+(\s*;)",
        rf"\g<1>{int(vb_h)}\2",
        css,
        count=1,
    )
    if n:
        css_path.write_text(css2, encoding="utf-8")
    else:
        print("warn: --cu-vb-h not patched in styles.css")

    print(f"ok v18 artboard={ART_W:g}x{ART_H:g} viewBoxH={vb_h:g} ymax={ymax:.2f}")


if __name__ == "__main__":
    main()
