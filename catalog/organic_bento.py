"""Pack categories into organic bento boards (eshop).

Fill order (round-robin across boards so all figure packs appear early):
  life TL → tech TL → row3 L → life TR → tech TR → row3 M → …
Empty shapes are omitted — only occupied slots render.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.templatetags.static import static

# Round-robin across life / tech / row3 so a third board shows with few categories
CYCLE_ORDER: list[tuple[str, str]] = [
    ("life", "TL"),
    ("tech", "TL"),
    ("row3", "L"),
    ("life", "TR"),
    ("tech", "TR"),
    ("row3", "M"),
    ("life", "BL"),
    ("tech", "BL"),
    ("row3", "R"),
    ("life", "BR"),
    ("tech", "BR"),
]

CYCLE_LEN = len(CYCLE_ORDER)
MAX_CATEGORIES = CYCLE_LEN * 2  # 22

BOARD_KIND_ORDER = ("life", "tech", "row3")

DEFAULT_VIEWBOX = {
    "life": "0 0 1000 1000",
    "tech": "0 0 1000 1000",
    "row3": "0 0 1000 352",
}


def _layouts_path() -> Path:
    base = Path(settings.BASE_DIR)
    return base / "themes" / "eshop" / "static" / "frontend" / "organic_layouts.json"


def load_layouts() -> dict[str, Any]:
    path = _layouts_path()
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _viewbox(layouts: dict[str, Any], kind: str) -> str:
    meta = (layouts.get("_meta") or {}).get(kind) or {}
    if meta.get("viewBox"):
        return str(meta["viewBox"])
    return DEFAULT_VIEWBOX.get(kind, "0 0 1000 1000")


def _cat_name(cat: Any) -> str:
    return str(getattr(cat, "name", None) or cat.get("name") or "Category")


def _cat_slug(cat: Any) -> str:
    return str(getattr(cat, "slug", None) or cat.get("slug") or "")


def _cat_image(cat: Any, fallback_static: str) -> str:
    image = getattr(cat, "image", None)
    if image:
        try:
            url = image.url
            if url:
                return url
        except (ValueError, AttributeError):
            pass
    if isinstance(cat, dict):
        if cat.get("image") and hasattr(cat["image"], "url"):
            try:
                return cat["image"].url
            except (ValueError, AttributeError):
                pass
        if cat.get("image_url"):
            return cat["image_url"]
    url = getattr(cat, "image_url", None)
    if url:
        return url
    return static(fallback_static)


def build_organic_boards(categories: list[Any]) -> list[dict[str, Any]]:
    """Return boards for the homepage organic section."""
    layouts = load_layouts()
    if not layouts or not categories:
        return []

    cats = list(categories)[:MAX_CATEGORIES]
    boards_map: dict[str, dict[str, Any]] = {}

    for i, cat in enumerate(cats):
        cycle_idx = i // CYCLE_LEN
        slot_idx = i % CYCLE_LEN
        kind, key = CYCLE_ORDER[slot_idx]
        if kind not in layouts:
            continue
        board_id = f"{kind}-{cycle_idx}"
        geom = layouts[kind][key]
        if board_id not in boards_map:
            boards_map[board_id] = {
                "id": board_id,
                "kind": kind,
                "pair": cycle_idx,
                "viewBox": _viewbox(layouts, kind),
                "slots": [],
            }
        boards_map[board_id]["slots"].append(
            {
                "key": key.lower(),
                "path": geom["path"],
                "x": f'{geom["x"]:.2f}',
                "y": f'{geom["y"]:.2f}',
                "w": f'{geom["w"]:.2f}',
                "h": f'{geom["h"]:.2f}',
                "pill_mod": geom["pill"],
                "label": _cat_name(cat),
                "slug": _cat_slug(cat),
                "image_url": _cat_image(cat, geom["fallback"]),
                "clip_id": f"og-{board_id}-{key.lower()}",
            }
        )

    ordered: list[dict[str, Any]] = []
    max_pair = max((b["pair"] for b in boards_map.values()), default=0)
    for pair in range(max_pair + 1):
        for kind in BOARD_KIND_ORDER:
            bid = f"{kind}-{pair}"
            if bid in boards_map:
                ordered.append(boards_map[bid])
    return ordered
