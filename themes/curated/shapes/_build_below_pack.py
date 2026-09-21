"""Build Figma pack for curated below-fold: About + New Arrivals organic figures.

Artboard 1200×1100. Starter paths are placeholders — user calibrates in Figma
against approved/below-ref.png, then drops inbox/calibrated-below.svg → «готово».
"""
from __future__ import annotations

import base64
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
REF = OUT / "approved" / "below-ref.png"
ART_W, ART_H = 1200.0, 1100.0

# Rough starter blobs (cyan = shadow/back layer, red = photo mask). User redraws.
# Coordinates approximate the mockup layout on 1200×1100.
STARTERS = {
    # About — large left figure + offset back
    "about-back": (
        "#00e5ff",
        "M 95 120 C 40 200 35 420 90 520 C 140 610 280 640 380 580 C 470 520 500 380 470 260 "
        "C 440 150 280 70 160 90 C 120 100 110 110 95 120 Z",
    ),
    "about-mask": (
        "#ff1744",
        "M 80 105 C 25 185 20 405 75 505 C 125 595 265 625 365 565 C 455 505 485 365 455 245 "
        "C 425 135 265 55 145 75 C 105 85 95 95 80 105 Z",
    ),
    # New Arrivals — 4 vertical pebbles
    "na-1-back": (
        "#00e5ff",
        "M 95 720 C 55 760 50 860 85 920 C 120 980 200 995 250 960 C 300 925 310 820 275 760 "
        "C 240 700 150 685 95 720 Z",
    ),
    "na-1-mask": (
        "#ff1744",
        "M 85 710 C 45 750 40 850 75 910 C 110 970 190 985 240 950 C 290 915 300 810 265 750 "
        "C 230 690 140 675 85 710 Z",
    ),
    "na-2-back": (
        "#00e5ff",
        "M 370 715 C 330 755 325 860 365 925 C 405 990 490 1000 540 960 C 590 920 595 810 555 750 "
        "C 515 690 425 680 370 715 Z",
    ),
    "na-2-mask": (
        "#ff1744",
        "M 360 705 C 320 745 315 850 355 915 C 395 980 480 990 530 950 C 580 910 585 800 545 740 "
        "C 505 680 415 670 360 705 Z",
    ),
    "na-3-back": (
        "#00e5ff",
        "M 655 710 C 610 750 605 865 650 930 C 695 995 785 1005 860 960 C 910 915 915 800 870 740 "
        "C 825 680 715 670 655 710 Z",
    ),
    "na-3-mask": (
        "#ff1744",
        "M 645 700 C 600 740 595 855 640 920 C 685 985 790 995 850 950 C 900 905 905 790 860 730 "
        "C 815 670 705 660 645 700 Z",
    ),
    "na-4-back": (
        "#00e5ff",
        "M 940 720 C 895 760 890 870 940 935 C 990 1000 1090 1005 1140 955 C 1190 905 1185 790 "
        "1135 735 C 1085 680 1000 680 940 720 Z",
    ),
    "na-4-mask": (
        "#ff1744",
        "M 930 710 C 885 750 880 860 930 925 C 980 990 1080 995 1130 945 C 1180 895 1175 780 "
        "1125 725 C 1075 670 990 670 930 710 Z",
    ),
}


def main() -> None:
    if not REF.exists():
        raise SystemExit(f"missing ref: {REF}")
    b64 = base64.b64encode(REF.read_bytes()).decode("ascii")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {ART_W:g} {ART_H:g}" width="{ART_W:g}" height="{ART_H:g}">',
        f'  <image id="REF" width="{ART_W:g}" height="{ART_H:g}" opacity="0.45" '
        f'href="data:image/png;base64,{b64}"/>',
        '  <g id="SHAPES">',
    ]
    for sid, (col, d) in STARTERS.items():
        lines.append(
            f'    <path id="{sid}" fill="none" stroke="{col}" stroke-width="2.5" d="{d}"/>'
        )
    lines += ["  </g>", "</svg>", ""]

    pack = OUT / "figma-pack-below.svg"
    pack.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {pack} ({pack.stat().st_size // 1024} KB)")

    html = OUT / "calibrate-below.html"
    html.write_text(
        """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8"/>
  <title>Curated — калибровка низа (About + New Arrivals)</title>
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; background: #111; color: #eee; }
    header { padding: 1.1rem 1.25rem; border-bottom: 1px solid #333; max-width: 52rem; }
    h1 { margin: 0 0 0.4rem; font-size: 1.05rem; }
    p, li { font-size: 0.88rem; line-height: 1.5; color: #b8b8b8; }
    code { color: #c5b39d; }
    ol { margin: 0.75rem 0 0; padding-left: 1.2rem; display: grid; gap: 0.35rem; }
    .box { margin: 1rem 1.25rem; padding: 0.9rem 1rem; background: #1a1a1a;
           border: 1px solid #333; border-radius: 10px; max-width: 52rem; }
  </style>
</head>
<body>
  <header>
    <h1>Новый низ: About + New Arrivals — только фигуры</h1>
    <p>Hero не трогаем. Калибруешь маски фото (красные) и задние слои (голубые).</p>
    <ol>
      <li>Открой <code>themes/curated/shapes/figma-pack-below.svg</code> в Figma (Place).</li>
      <li>Подгони path к краям контейнеров на референсе (не к силуэту модели).</li>
      <li>Сохрани id: <code>about-back</code>, <code>about-mask</code>,
          <code>na-1-back</code>…<code>na-4-mask</code>.</li>
      <li>Export SVG → <code>themes/curated/shapes/inbox/calibrated-below.svg</code></li>
      <li>В чат: <strong>готово</strong></li>
    </ol>
  </header>
  <div class="box">
    Красные = photo-mask · Голубые = shadow/back layer · UI (заголовки, кнопки) — CSS, не path.
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    print(f"wrote {html}")

    inbox = OUT / "inbox"
    inbox.mkdir(exist_ok=True)
    (inbox / "DROP_CALIBRATED_BELOW_HERE.txt").write_text(
        "Export Figma as calibrated-below.svg into this folder, then say: готово\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
