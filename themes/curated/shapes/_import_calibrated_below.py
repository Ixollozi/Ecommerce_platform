"""Import inbox/calibrated-below.svg → paths/below/*.svg + lock meta."""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
INBOX = OUT / "inbox" / "calibrated-below.svg"
PATHS = OUT / "paths" / "below"
APPROVED = OUT / "approved"
ART_W, ART_H = 1200.0, 1100.0

# Figma paste order (ids added on save): about 2 + each NA fringe/body/waist
ORDER = [
    "about-back",
    "about-mask",
    "na-1-fringe",
    "na-1-body",
    "na-1-waist",
    "na-2-fringe",
    "na-2-body",
    "na-2-waist",
    "na-3-fringe",
    "na-3-body",
    "na-3-waist",
    "na-4-fringe",
    "na-4-body",
    "na-4-waist",
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
        if id_m:
            raw = html.unescape(id_m.group(1)).strip()
            for sid in ORDER:
                if raw == sid or raw.endswith(sid) or sid in raw:
                    found[sid] = d
                    break
    for i, d in enumerate(ordered):
        if i >= len(ORDER):
            break
        sid = ORDER[i]
        if sid not in found:
            found[sid] = d
    return found


def write_paths(paths: dict[str, str]) -> None:
    PATHS.mkdir(parents=True, exist_ok=True)
    for p in PATHS.glob("*.svg"):
        p.unlink()
    for sid, d in paths.items():
        (PATHS / f"{sid}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ART_W:g} {ART_H:g}">'
            f'<path id="{sid}" fill="#ccc" d="{d}"/></svg>\n',
            encoding="utf-8",
        )


def main() -> None:
    APPROVED.mkdir(exist_ok=True)
    if not INBOX.exists():
        raise SystemExit(f"missing {INBOX}")
    text = INBOX.read_text(encoding="utf-8")
    paths = extract_paths(text)
    missing = [s for s in ORDER if s not in paths]
    if missing:
        raise SystemExit(f"missing paths: {missing} (got {list(paths)})")
    write_paths(paths)
    shutil.copy2(INBOX, APPROVED / "below-shapes-locked.svg")
    (APPROVED / "below-LOCK.txt").write_text(
        "below shapes locked from inbox/calibrated-below.svg\n"
        "schema: about-back/mask + na-N-fringe/body/waist\n",
        encoding="utf-8",
    )
    meta = {
        "artboard": [ART_W, ART_H],
        "ids": ORDER,
        "source": "inbox/calibrated-below.svg",
    }
    (APPROVED / "below_paths_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print("imported", len(paths), "paths →", PATHS)


if __name__ == "__main__":
    main()
