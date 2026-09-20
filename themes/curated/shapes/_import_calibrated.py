"""Parse Figma SVG export → approved paths + organic_layouts.json."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
STATIC = Path(r"d:\Cursor\clothing_shop\themes\curated\static\shapes")
INBOX = OUT / "inbox" / "calibrated.svg"
APPROVED = OUT / "approved"
PATHS = OUT / "paths"

# Map Figma layer names → layout ids
NAME_MAP = {
    "F-photo-left": "F-photo-left",
    "G-photo-top": "G-photo-top",
    "G-photo-bottom": "G-photo-bottom",  # new (was I-photo-bl)
    "H-photo-right": "H-photo-right",
    "нижняя": "C-dark-bottom",
    "верхняя": "C-dark-upper",  # upper lobe of bottom dark
    "нижняя часть": "A-header-lower",
    "верхняя часть": "A-dark-top-left",
}


# Fallback order for paths whose Cyrillic ids were mangled in the SVG export
ORDERED_FALLBACK = [
    "F-photo-left",
    "G-photo-bottom",
    "G-photo-top",
    "H-photo-right",
    "C-dark-bottom",  # нижняя
    "C-dark-upper",  # верхняя
    "A-header-lower",  # нижняя часть
    "A-dark-top-left",  # верхняя часть
]


def extract_paths(svg_text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    ordered: list[str] = []
    for m in re.finditer(r"<path\b([^>]*)/?>", svg_text, flags=re.I):
        attrs = m.group(1)
        id_m = re.search(r'\bid="([^"]+)"', attrs)
        d_m = re.search(r'\bd="([^"]+)"', attrs)
        if not d_m:
            continue
        d = " ".join(d_m.group(1).split())
        ordered.append(d)
        if not id_m:
            continue
        raw_id = html.unescape(id_m.group(1))
        if any(ord(c) > 127 for c in raw_id):
            try:
                raw_id = raw_id.encode("latin-1").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        sid = NAME_MAP.get(raw_id)
        if sid:
            found[sid] = d

    # Fill gaps from positional order (Figma export path order is stable)
    for i, d in enumerate(ordered):
        if i >= len(ORDERED_FALLBACK):
            break
        sid = ORDERED_FALLBACK[i]
        if sid not in found:
            found[sid] = d
    return found


ROLE = {
    "A-dark-top-left": ("background", "#2a2c2b"),
    "A-header-lower": ("background", "#2a2c2b"),
    "B-tan-left": ("background", "#c5b49f"),
    "C-dark-bottom": ("background", "#2a2c2b"),
    "C-dark-upper": ("background", "#2a2c2b"),
    "D-cream-center": ("background", "#f5f0e6"),
    "E-cream-right": ("background", "#efe8db"),
    "F-photo-left": ("photo-mask", "#b8a890"),
    "G-photo-top": ("photo-mask", "#b8a890"),
    "G-photo-bottom": ("photo-mask", "#b8a890"),
    "H-photo-right": ("photo-mask", "#b8a890"),
    "I-photo-bl": ("photo-mask", "#b8a890"),
    "J-thumb-a": ("ui", "#ddd"),
    "K-thumb-b": ("ui", "#ddd"),
    "L-cta": ("ui", "url(#ctaGrad)"),
}


def bbox_of(d: str) -> list[float]:
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    if not xs or not ys:
        return [0, 0, 0, 0]
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def main() -> None:
    APPROVED.mkdir(exist_ok=True)
    PATHS.mkdir(exist_ok=True)
    text = INBOX.read_text(encoding="utf-8")
    paths = extract_paths(text)
    print("extracted", [repr(k) for k in paths])

    # archive raw export
    shutil.copy2(INBOX, APPROVED / "calibrated.svg")
    (APPROVED / "README.txt").write_text(
        "Approved Figma sketch (figma-pack kol1lXyqGi5aQ0o8L2DC6f node 1:2).\n"
        "figma-sketch-1024.png — MCP screenshot\n"
        "calibrated.svg — SVG export with vector paths\n"
        "figma-pack-export.svg — same as calibrated\n",
        encoding="utf-8",
    )

    layouts = json.loads((OUT / "organic_layouts.json").read_text(encoding="utf-8"))
    hero = layouts.setdefault("hero", {})

    # Keep cream base if missing
    if "D-cream-center" not in hero:
        hero["D-cream-center"] = {
            "path": "M0 0H1024V625H0Z",
            "role": "background",
            "fill": "#f5f0e6",
            "cubics": 0,
            "bbox": [0, 0, 1024, 625],
        }

    updated = []
    for sid, d in paths.items():
        role, fill = ROLE.get(sid, ("photo-mask", "#b8a890"))
        entry = hero.get(sid, {})
        entry.update(
            {
                "path": d,
                "role": role,
                "fill": fill if not str(entry.get("fill", "")).startswith("url") else entry["fill"],
                "cubics": d.count("C") + d.count("c"),
                "bbox": bbox_of(d),
                "source": "figma-calibrated",
            }
        )
        if sid in ("F-photo-left", "G-photo-top", "G-photo-bottom", "H-photo-right"):
            entry["role"] = "photo-mask"
        hero[sid] = entry
        fill_out = entry["fill"] if not str(entry["fill"]).startswith("url") else "#c5b49f"
        (PATHS / f"{sid}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 625">'
            f'<path fill="{fill_out}" d="{d}"/></svg>\n',
            encoding="utf-8",
        )
        updated.append(sid)
        print(f"  {sid}: C={entry['cubics']} len={len(d)}")

    # Alias: G-photo-bottom replaces I-photo-bl for hero
    if "G-photo-bottom" in hero:
        hero["I-photo-bl"] = {
            **hero["G-photo-bottom"],
            "alias_of": "G-photo-bottom",
        }

    layouts["_meta"] = {
        **layouts.get("_meta", {}),
        "artboard": [1024, 625],
        "method": "figma calibrated vectors",
        "version": 6,
        "calibrated_from": "approved/calibrated.svg",
        "figma_file": "kol1lXyqGi5aQ0o8L2DC6f",
        "figma_node": "1:2",
    }
    layouts["hero"] = hero
    dump = json.dumps(layouts, indent=2, ensure_ascii=False)
    (OUT / "organic_layouts.json").write_text(dump, encoding="utf-8")
    STATIC.mkdir(parents=True, exist_ok=True)
    (STATIC / "organic_layouts.json").write_text(dump, encoding="utf-8")

    # Overlay QA
    stroke = {
        "background": ("#00e5ff", "1.3", "0.28"),
        "photo-mask": ("#ff1744", "2.2", None),
        "ui": ("#00e676", "1.5", None),
    }
    order = [
        "A-dark-top-left",
        "A-header-lower",
        "B-tan-left",
        "C-dark-upper",
        "C-dark-bottom",
        "E-cream-right",
        "F-photo-left",
        "G-photo-top",
        "G-photo-bottom",
        "H-photo-right",
        "J-thumb-a",
        "K-thumb-b",
        "L-cta",
    ]
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 625" width="1024" height="625">\n',
        '<image href="../static/img/_ref-hero.png" x="0" y="0" width="1024" height="625"/>\n',
    ]
    for sid in order:
        if sid not in hero:
            continue
        s = hero[sid]
        col, sw, opac = stroke[s["role"]]
        if opac:
            body.append(
                f'<path id="{sid}" fill="{s["fill"]}" fill-opacity="{opac}" '
                f'stroke="{col}" stroke-width="{sw}" d="{s["path"]}"/>\n'
            )
        else:
            body.append(
                f'<path id="{sid}" fill="none" stroke="{col}" stroke-width="{sw}" d="{s["path"]}"/>\n'
            )
    body.append("</svg>\n")
    (OUT / "04-overlay-qa.svg").write_text("".join(body), encoding="utf-8")
    (APPROVED / "04-overlay-qa.svg").write_text("".join(body), encoding="utf-8")

    # Standalone shapes SVG for site clip paths (no ref image)
    site = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 625">\n',
        "<defs>\n",
    ]
    for sid in [
        "F-photo-left",
        "G-photo-top",
        "G-photo-bottom",
        "H-photo-right",
    ]:
        if sid not in hero:
            continue
        site.append(f'<clipPath id="clip-{sid}"><path d="{hero[sid]["path"]}"/></clipPath>\n')
    site.append("</defs>\n")
    for sid in [
        "D-cream-center",
        "A-dark-top-left",
        "A-header-lower",
        "B-tan-left",
        "C-dark-upper",
        "C-dark-bottom",
        "E-cream-right",
    ]:
        if sid not in hero:
            continue
        site.append(f'<path id="{sid}" fill="{hero[sid]["fill"]}" d="{hero[sid]["path"]}"/>\n')
    site.append("</svg>\n")
    (APPROVED / "hero-shapes.svg").write_text("".join(site), encoding="utf-8")
    (OUT / "hero-shapes.svg").write_text("".join(site), encoding="utf-8")

    print("updated", len(updated), "shapes -> organic_layouts v6 + approved/")


if __name__ == "__main__":
    main()
