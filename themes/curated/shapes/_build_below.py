"""Build curated below-fold from Figma-calibrated paths.

Layers:
  SVG backs/fringes (solid taupe)
  Photos on about-mask + na-*-body
  SVG waist clouds (cream)
  Hit links on fringe+body → product
  Labels fixed inside waist clouds
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
TPL = Path(r"d:\Cursor\clothing_shop\themes\curated\templates")
PATHS = OUT / "paths" / "below"

ART_W, ART_H = 1200.0, 1100.0
CACHE = "v=below-photo5"

LOOKS = ("Oasis Dress", "Midnight Gown", "Terra Blouse", "Sandstone Skirt")
PHOTO_SLOTS = (
    ("about", "about-mask", "img/below-about.jpg"),
    ("na-1", "na-1-body", "img/below-na-1.jpg"),
    ("na-2", "na-2-body", "img/below-na-2.jpg"),
    ("na-3", "na-3-body", "img/below-na-3.jpg"),
    ("na-4", "na-4-body", "img/below-na-4.jpg"),
)

FILLS_BACK = {
    "about-back": "#c5b39d",
    "na-1-fringe": "#c5b39d",
    "na-2-fringe": "#c5b39d",
    "na-3-fringe": "#c5b39d",
    "na-4-fringe": "#c5b39d",
}
FILL_WAIST = "#f3efe7"
GLOW_WAIST = "#9a8874"  # fringe taupe, darker — soft rim


def path_from_svg(name: str) -> str:
    text = (PATHS / f"{name}.svg").read_text(encoding="utf-8")
    m = re.search(r'\bd="([^"]+)"', text)
    if not m:
        raise SystemExit(f"no path in {name}.svg")
    return " ".join(m.group(1).split())


def path_bbox(d: str) -> tuple[float, float, float, float]:
    nums = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    pad = 2.0
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def mask_uri(*path_ds: str, x: float, y: float, w: float, h: float) -> str:
    parts = "".join(f'<path fill="#fff" d="{d}"/>' for d in path_ds)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x:g} {y:g} {w:g} {h:g}" preserveAspectRatio="none">'
        f"{parts}</svg>"
    )
    return "data:image/svg+xml," + quote(svg, safe="")


def pct_box(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
    return (
        x0 / ART_W * 100.0,
        y0 / ART_H * 100.0,
        (x1 - x0) / ART_W * 100.0,
        (y1 - y0) / ART_H * 100.0,
    )


def main() -> None:
    ids = [
        "about-back",
        "about-mask",
        *[f"na-{i}-{k}" for i in range(1, 5) for k in ("fringe", "body", "waist")],
    ]
    paths = {sid: path_from_svg(sid) for sid in ids}

    # --- SVG backs + fringes ---
    back_lines = [
        f'<svg class="cu-below__shapes cu-below__shapes--back" viewBox="0 0 {ART_W:g} {ART_H:g}" '
        f'preserveAspectRatio="none" aria-hidden="true">',
        f'  <rect width="{ART_W:g}" height="{ART_H:g}" fill="#f3efe7"/>',
        f'  <path id="about-back" fill="{FILLS_BACK["about-back"]}" d="{paths["about-back"]}"/>',
    ]
    for i in range(1, 5):
        sid = f"na-{i}-fringe"
        back_lines.append(
            f'  <path id="{sid}" fill="{FILLS_BACK[sid]}" d="{paths[sid]}"/>'
        )
    back_lines.append("</svg>")

    # --- Photos on about-mask + na bodies ---
    photo_lines = ['<div class="cu-below__photos" aria-hidden="true">']
    for name, sid, src in PHOTO_SLOTS:
        d = paths[sid]
        x0, y0, x1, y1 = path_bbox(d)
        left, top, width, height = pct_box(x0, y0, x1, y1)
        mask = mask_uri(d, x=x0, y=y0, w=x1 - x0, h=y1 - y0)
        photo_lines += [
            f'  <figure class="cu-below__photo cu-below__photo--{name}" '
            f'style="left:{left:.4f}%;top:{top:.4f}%;'
            f"width:{width:.4f}%;height:{height:.4f}%;"
            f"-webkit-mask-image:url('{mask}');"
            f"mask-image:url('{mask}');\">",
            f'    <img src="{{% static \'{src}\' %}}?{CACHE}" alt="" '
            f'draggable="false" decoding="async">',
            "  </figure>",
        ]
        print("photo", name, sid, src)
    photo_lines.append("</div>")

    # --- Waist clouds: soft glow under + cream face + thin rim ---
    waist_lines = [
        f'<svg class="cu-below__shapes cu-below__shapes--waist" viewBox="0 0 {ART_W:g} {ART_H:g}" '
        f'preserveAspectRatio="none" aria-hidden="true">',
        "  <defs>",
        '    <filter id="cu-waist-glow" x="-40%" y="-40%" width="180%" height="180%" '
        'color-interpolation-filters="sRGB">',
        '      <feGaussianBlur in="SourceGraphic" stdDeviation="3.5"/>',
        "    </filter>",
        "  </defs>",
    ]
    waist_label_pos: list[tuple[float, float]] = []
    for i in range(1, 5):
        sid = f"na-{i}-waist"
        d = paths[sid]
        x0, y0, x1, y1 = path_bbox(d)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        avg = 0.5 * ((x1 - x0) + (y1 - y0))
        # Face slightly larger than source; glow a bit larger still
        s_face = 1.0 + (2.5 / max(avg, 1.0))
        s_glow = 1.0 + (7.0 / max(avg, 1.0))

        def xf(scale: float) -> str:
            return (
                f'transform="translate({cx:g} {cy:g}) scale({scale:.5f}) '
                f'translate({-cx:g} {-cy:g})"'
            )

        # Soft ray / feather (behind)
        waist_lines.append(
            f'  <path id="{sid}-glow" fill="{GLOW_WAIST}" opacity="0.7" '
            f'filter="url(#cu-waist-glow)" {xf(s_glow)} d="{d}"/>'
        )
        # Solid cloud + thin readable edge
        waist_lines.append(
            f'  <path id="{sid}" fill="{FILL_WAIST}" stroke="{GLOW_WAIST}" '
            f'stroke-width="1.35" stroke-linejoin="round" '
            f'vector-effect="non-scaling-stroke" '
            f'{xf(s_face)} d="{d}"/>'
        )
        lx = cx / ART_W * 100.0
        ly = (y0 + (y1 - y0) * 0.64) / ART_H * 100.0
        ly += (s_face - 1.0) * (y1 - y0) * 0.15 / ART_H * 100.0
        waist_label_pos.append((lx, ly))
        print("waist", sid, f"face={s_face:.4f}", f"glow={s_glow:.4f}")
    waist_lines.append("</svg>")

    # --- Hit links: fringe ∪ body ---
    hit_lines = ['<div class="cu-below__hits">']
    for i in range(1, 5):
        fringe = paths[f"na-{i}-fringe"]
        body = paths[f"na-{i}-body"]
        fx0, fy0, fx1, fy1 = path_bbox(fringe)
        bx0, by0, bx1, by1 = path_bbox(body)
        x0, y0 = min(fx0, bx0), min(fy0, by0)
        x1, y1 = max(fx1, bx1), max(fy1, by1)
        left, top, width, height = pct_box(x0, y0, x1, y1)
        mask = mask_uri(fringe, body, x=x0, y=y0, w=x1 - x0, h=y1 - y0)
        idx = i - 1
        look = LOOKS[idx]
        hit_lines.append(
            f'  {{% if featured_products.{idx} %}}\n'
            f'  <a class="cu-below__hit" href="{{% url \'product\' featured_products.{idx}.slug %}}" '
            f'style="left:{left:.4f}%;top:{top:.4f}%;width:{width:.4f}%;height:{height:.4f}%;'
            f"-webkit-mask-image:url('{mask}');mask-image:url('{mask}');\" "
            f'aria-label="{look}"></a>\n'
            f"  {{% else %}}\n"
            f'  <a class="cu-below__hit" href="{{% url \'catalog\' %}}" '
            f'style="left:{left:.4f}%;top:{top:.4f}%;width:{width:.4f}%;height:{height:.4f}%;'
            f"-webkit-mask-image:url('{mask}');mask-image:url('{mask}');\" "
            f'aria-label="{look}"></a>\n'
            f"  {{% endif %}}"
        )
        print("hit", f"na-{i}")
    hit_lines.append("</div>")

    # --- Labels inside waist clouds ---
    label_lines = ['<ul class="cu-below__cards">']
    for i in range(1, 5):
        lx, ly = waist_label_pos[i - 1]
        look = LOOKS[i - 1]
        label_lines.append(
            f'  <li class="cu-below__card" style="left:{lx:.3f}%;top:{ly:.3f}%;" '
            f'data-slot="{i}">\n'
            f'    <span class="cu-below__card-name">{look}</span>\n'
            f'    <span class="cu-below__card-cta">SHOP NOW</span>\n'
            f"  </li>"
        )
    label_lines.append("</ul>")

    def union_bbox(*ds: str) -> tuple[float, float, float, float]:
        boxes = [path_bbox(d) for d in ds]
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    def local_pct(
        box: tuple[float, float, float, float],
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> tuple[float, float, float, float]:
        bx0, by0, bx1, by1 = box
        bw, bh = bx1 - bx0, by1 - by0
        return (
            (x0 - bx0) / bw * 100.0,
            (y0 - by0) / bh * 100.0,
            (x1 - x0) / bw * 100.0,
            (y1 - y0) / bh * 100.0,
        )

    # --- Mobile: same Figma paths, stacked about + NA rail ---
    about_back_d = paths["about-back"]
    about_mask_d = paths["about-mask"]
    ab = union_bbox(about_back_d, about_mask_d)
    am_box = path_bbox(about_mask_d)
    am_left, am_top, am_w, am_h = local_pct(ab, *am_box)
    about_mask_uri = mask_uri(
        about_mask_d, x=am_box[0], y=am_box[1], w=am_box[2] - am_box[0], h=am_box[3] - am_box[1]
    )
    ab_w, ab_h = ab[2] - ab[0], ab[3] - ab[1]

    m_about = [
        '<div class="cu-below__mobile">',
        '  <div class="cu-below__m-about">',
        f'    <div class="cu-below__m-about-fig" style="aspect-ratio:{ab_w:g}/{ab_h:g};">',
        f'      <svg class="cu-below__m-svg" viewBox="{ab[0]:g} {ab[1]:g} {ab_w:g} {ab_h:g}" '
        f'preserveAspectRatio="xMidYMid meet" aria-hidden="true">',
        f'        <path fill="{FILLS_BACK["about-back"]}" d="{about_back_d}"/>',
        "      </svg>",
        f'      <figure class="cu-below__m-photo" style="left:{am_left:.3f}%;top:{am_top:.3f}%;'
        f"width:{am_w:.3f}%;height:{am_h:.3f}%;"
        f"-webkit-mask-image:url('{about_mask_uri}');"
        f"mask-image:url('{about_mask_uri}');\">",
        f'        <img src="{{% static \'{PHOTO_SLOTS[0][2]}\' %}}?{CACHE}" alt="" '
        f'draggable="false" decoding="async">',
        "      </figure>",
        "    </div>",
        '    <div class="cu-below__m-about-copy">',
        '      <h2 class="cu-below__about-title">ABOUT US</h2>',
        '      <p class="cu-below__about-copy">',
        "        We curate quiet luxury — pieces with lasting fabric, clean lines,",
        "        and a calm silhouette for everyday wear.",
        "      </p>",
        '      <p class="cu-below__about-copy">',
        "        Each drop is limited. Discover the season's edit in the shop.",
        "      </p>",
        '      <a class="cu-below__about-cta" href="{% url \'catalog\' %}">SHOP NOW</a>',
        "    </div>",
        "  </div>",
        '  <h2 class="cu-below__m-arrivals">NEW ARRIVALS</h2>',
        '  <div class="cu-below__m-rail">',
        '    <div class="cu-below__m-track">',
    ]

    m_cards: list[str] = []
    for i in range(1, 5):
        idx = i - 1
        look = LOOKS[idx]
        src = PHOTO_SLOTS[i][2]
        fringe_d = paths[f"na-{i}-fringe"]
        body_d = paths[f"na-{i}-body"]
        waist_d = paths[f"na-{i}-waist"]
        box = union_bbox(fringe_d, body_d, waist_d)
        bw, bh = box[2] - box[0], box[3] - box[1]
        body_box = path_bbox(body_d)
        waist_box = path_bbox(waist_d)
        bl, bt, bww, bhh = local_pct(box, *body_box)
        body_mask = mask_uri(
            body_d,
            x=body_box[0],
            y=body_box[1],
            w=body_box[2] - body_box[0],
            h=body_box[3] - body_box[1],
        )
        # label in visual mass of waist (same as desktop)
        wcx = (waist_box[0] + waist_box[2]) / 2
        wcy = waist_box[1] + (waist_box[3] - waist_box[1]) * 0.64
        ll = (wcx - box[0]) / bw * 100.0
        lt = (wcy - box[1]) / bh * 100.0
        cx = (waist_box[0] + waist_box[2]) / 2
        cy = (waist_box[1] + waist_box[3]) / 2
        avg = 0.5 * ((waist_box[2] - waist_box[0]) + (waist_box[3] - waist_box[1]))
        s_face = 1.0 + (2.5 / max(avg, 1.0))
        s_glow = 1.0 + (7.0 / max(avg, 1.0))
        xf_face = (
            f'transform="translate({cx:g} {cy:g}) scale({s_face:.5f}) '
            f'translate({-cx:g} {-cy:g})"'
        )
        xf_glow = (
            f'transform="translate({cx:g} {cy:g}) scale({s_glow:.5f}) '
            f'translate({-cx:g} {-cy:g})"'
        )
        fid = f"cu-m-waist-glow-{i}"
        fringe_fill = FILLS_BACK[f"na-{i}-fringe"]
        m_cards.append(
            f"      {{% if featured_products.{idx} %}}\n"
            f'      <a class="cu-below__m-card" href="{{% url \'product\' featured_products.{idx}.slug %}}" '
            f'aria-label="{look}">\n'
            f"      {{% else %}}\n"
            f'      <a class="cu-below__m-card" href="{{% url \'catalog\' %}}" aria-label="{look}">\n'
            f"      {{% endif %}}\n"
            f'        <div class="cu-below__m-card-fig" style="aspect-ratio:{bw:g}/{bh:g};">\n'
            f'          <svg class="cu-below__m-svg cu-below__m-svg--back" '
            f'viewBox="{box[0]:g} {box[1]:g} {bw:g} {bh:g}" '
            f'preserveAspectRatio="xMidYMid meet" aria-hidden="true">\n'
            f'            <path fill="{fringe_fill}" d="{fringe_d}"/>\n'
            f"          </svg>\n"
            f'          <figure class="cu-below__m-photo" style="left:{bl:.3f}%;top:{bt:.3f}%;'
            f"width:{bww:.3f}%;height:{bhh:.3f}%;"
            f"-webkit-mask-image:url('{body_mask}');"
            f"mask-image:url('{body_mask}');\">\n"
            f'            <img src="{{% static \'{src}\' %}}?{CACHE}" alt="" '
            f'draggable="false" decoding="async">\n'
            f"          </figure>\n"
            f'          <svg class="cu-below__m-svg cu-below__m-svg--waist" '
            f'viewBox="{box[0]:g} {box[1]:g} {bw:g} {bh:g}" '
            f'preserveAspectRatio="xMidYMid meet" aria-hidden="true">\n'
            f"            <defs>\n"
            f'              <filter id="{fid}" x="-40%" y="-40%" width="180%" height="180%" '
            f'color-interpolation-filters="sRGB">\n'
            f'                <feGaussianBlur in="SourceGraphic" stdDeviation="3.5"/>\n'
            f"              </filter>\n"
            f"            </defs>\n"
            f'            <path fill="{GLOW_WAIST}" opacity="0.7" filter="url(#{fid})" '
            f'{xf_glow} d="{waist_d}"/>\n'
            f'            <path fill="{FILL_WAIST}" stroke="{GLOW_WAIST}" stroke-width="1.35" '
            f'stroke-linejoin="round" vector-effect="non-scaling-stroke" '
            f'{xf_face} d="{waist_d}"/>\n'
            f"          </svg>\n"
            f'          <div class="cu-below__m-cloud" style="left:{ll:.3f}%;top:{lt:.3f}%;">\n'
            f'            <span class="cu-below__card-name">{look}</span>\n'
            f'            <span class="cu-below__card-cta">SHOP NOW</span>\n'
            f"          </div>\n"
            f"        </div>\n"
            f"      </a>"
        )

    mobile = "\n".join(
        [
            *m_about,
            *m_cards,
            "    </div>",
            "  </div>",
            "</div>",
        ]
    )

    board = "\n".join(
        [
            "{# Below-fold — Figma paths: photos on mask/body, labels in waist #}",
            "{% load static i18n %}",
            '<div class="cu-below__stage">',
            *back_lines,
            *photo_lines,
            *waist_lines,
            *hit_lines,
            '  <div class="cu-below__about">',
            '    <h2 class="cu-below__about-title">ABOUT US</h2>',
            '    <p class="cu-below__about-copy">',
            "      We curate quiet luxury — pieces with lasting fabric, clean lines,",
            "      and a calm silhouette for everyday wear.",
            "    </p>",
            '    <p class="cu-below__about-copy">',
            "      Each drop is limited. Discover the season's edit in the shop.",
            "    </p>",
            '    <a class="cu-below__about-cta" href="{% url \'catalog\' %}">SHOP NOW</a>',
            "  </div>",
            '  <h2 class="cu-below__arrivals-title">NEW ARRIVALS</h2>',
            *label_lines,
            "</div>",
            mobile,
            "",
        ]
    )

    out = TPL / "partials" / "below_board.html"
    out.write_text(board, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
