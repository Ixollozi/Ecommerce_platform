"""Extract below-fold organic OUTER figures from below-ref.png.

Rules (anti-noise):
- Cream page = background.
- Morph open kills thin text so it cannot bridge figures.
- Tiny/sparse components (buttons, lines) discarded.
- Only OUTER contours of each blob — never internal photo edges.
- Back = solid low-variance tan/dark lobe if present; else slight offset dilate.
- Mask = full blob outer silhouette (photo container), not model outline.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
REF = OUT / "approved" / "below-ref.png"
PATHS = OUT / "paths" / "below"
QA = OUT / "approved" / "below-trace-qa.png"
ART_W, ART_H = 1200.0, 1100.0


def cream_mask(rgb: np.ndarray) -> np.ndarray:
    r = rgb[..., 0].astype(np.float32)
    g = rgb[..., 1].astype(np.float32)
    b = rgb[..., 2].astype(np.float32)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    chroma = mx - mn
    # Page cream + near-white product cards (weak delta vs cream → background)
    page = (r > 228) & (g > 222) & (b > 210) & (chroma < 32)
    near_white = (r > 242) & (g > 238) & (b > 232) & (chroma < 18)
    return page | near_white


def trim_card_tail(region: np.ndarray) -> np.ndarray:
    """Cut white-card lobe under NA figures at the waist (min width in lower half)."""
    ys, xs = np.where(region)
    if len(ys) == 0:
        return region
    y0, y1 = int(ys.min()), int(ys.max())
    h = y1 - y0 + 1
    if h < 40:
        return region
    # Search waist in lower 45–85% of blob height
    best_y = None
    best_w = 1e9
    for y in range(y0 + int(h * 0.45), y0 + int(h * 0.88)):
        row = region[y]
        if not row.any():
            continue
        xx = np.where(row)[0]
        w = int(xx.max() - xx.min() + 1)
        if w < best_w:
            best_w = w
            best_y = y
    if best_y is None:
        return region
    # Only trim if waist is clearly narrower than mid body
    mid = region[y0 + h // 3]
    if mid.any():
        mx = np.where(mid)[0]
        mid_w = int(mx.max() - mx.min() + 1)
        if best_w > mid_w * 0.72:
            return region
    out = region.copy()
    out[best_y + 1 :, :] = False
    # Keep only largest component after cut
    u8 = (out.astype(np.uint8) * 255)
    cnts, _ = cv2.findContours(u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return region
    c = max(cnts, key=cv2.contourArea)
    cleaned = np.zeros_like(out, dtype=np.uint8)
    cv2.drawContours(cleaned, [c], -1, 255, -1)
    return cleaned > 0


def blob_masks(rgb: np.ndarray) -> list[np.ndarray]:
    h, w = rgb.shape[:2]
    cream = cream_mask(rgb)
    raw = (~cream).astype(np.uint8) * 255
    raw = cv2.morphologyEx(
        raw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1
    )
    # Seal pinholes inside photos without merging neighboring cards
    raw = cv2.morphologyEx(
        raw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1
    )

    cnts, _ = cv2.findContours(raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    min_area = 5000
    blobs = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        if bw < 55 or bh < 90:
            continue
        fill = area / max(1.0, bw * bh)
        if fill < 0.45:
            continue
        # Skip wide short UI (text bands / buttons)
        if bw > bh * 1.6 and bh < 45:
            continue
        m = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(m, [c], -1, 255, -1)
        # Fill interior holes so contour is OUTER only
        m = cv2.morphologyEx(
            m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)), iterations=2
        )
        blobs.append(m > 0)
    return blobs


def classify(blobs: list[np.ndarray], h: int, w: int) -> dict[str, np.ndarray]:
    """Pick about (top) + 4 arrivals L→R (bottom)."""
    top, bot = [], []
    for m in blobs:
        cy = float(np.where(m)[0].mean())
        (bot if cy > h * 0.48 else top).append(m)

    out: dict[str, np.ndarray] = {}
    if top:
        # About = largest top blob (photo container)
        about = max(top, key=lambda m: m.sum())
        out["about"] = about
        # Optional: merge nearby smaller top blob if it's the offset back
        for m in top:
            if m is about:
                continue
            if m.sum() < about.sum() * 0.55:
                # If overlaps or sits left of about, union as about stack later via back extract
                pass

    bot.sort(key=lambda m: float(np.where(m)[1].mean()))
    for i, m in enumerate(bot[:4]):
        out[f"na-{i + 1}"] = trim_card_tail(m)
    return out


def solid_back(rgb: np.ndarray, region: np.ndarray) -> np.ndarray | None:
    """Offset shadow lobe — solid tan/dark on fringe only (never photo interior)."""
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean = cv2.blur(gray, (9, 9))
    mean2 = cv2.blur(gray * gray, (9, 9))
    std = np.sqrt(np.clip(mean2 - mean * mean, 0, None))
    r = rgb[..., 0].astype(np.float32)
    g = rgb[..., 1].astype(np.float32)
    b = rgb[..., 2].astype(np.float32)
    cream = cream_mask(rgb)

    k_out = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29))
    k_in = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    outer = cv2.dilate(region.astype(np.uint8), k_out) > 0
    interior = cv2.erode(region.astype(np.uint8), k_in) > 0
    band = outer & (~interior)

    tan = (r - b > 14) & (r > 115) & (r < 220) & (std < 10) & (~cream)
    dark = (r < 65) & (g < 65) & (b < 65) & (std < 10) & (~cream)
    solid = band & (tan | dark)

    solid_u8 = cv2.morphologyEx(
        (solid.astype(np.uint8) * 255),
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        iterations=2,
    )
    solid_u8 = cv2.morphologyEx(
        solid_u8, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    )
    cnts, _ = cv2.findContours(solid_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    min_a = max(100.0, region.sum() * 0.04)
    cnts = [c for c in cnts if cv2.contourArea(c) >= min_a]
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    out = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(out, [c], -1, 255, -1)
    return out > 0


def outer_contour(mask: np.ndarray) -> np.ndarray | None:
    m = (mask.astype(np.uint8) * 255)
    # Ensure filled
    m = cv2.morphologyEx(
        m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)), iterations=2
    )
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return None
    return max(cnts, key=cv2.contourArea)


def contour_to_path(cnt: np.ndarray, sx: float, sy: float, simplify: float = 1.35) -> str:
    approx = cv2.approxPolyDP(cnt, simplify, True)
    pts = approx.reshape(-1, 2).astype(np.float64)
    if len(pts) < 4:
        pts = cnt.reshape(-1, 2).astype(np.float64)
    if len(pts) > 140:
        pts = pts[:: max(1, len(pts) // 100)]
    pts = pts.copy()
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    if np.linalg.norm(pts[0] - pts[-1]) > 1e-3:
        pts = np.vstack([pts, pts[0]])
    n = len(pts) - 1
    cmds = [f"M {pts[0, 0]:.2f} {pts[0, 1]:.2f}"]
    for i in range(n):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 <= n else pts[i + 1]
        c1 = p1 + (p2 - p0) / 6.0
        c2 = p2 - (p3 - p1) / 6.0
        cmds.append(
            f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
        )
    cmds.append("Z")
    return " ".join(cmds)


def synthetic_back(mask: np.ndarray) -> np.ndarray:
    """Offset dilate left/down as fallback shadow layer."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    dil = cv2.dilate((mask.astype(np.uint8) * 255), k)
    # Shift left a few px
    M = np.float32([[1, 0, -6], [0, 1, 3]])
    shifted = cv2.warpAffine(dil, M, (mask.shape[1], mask.shape[0]))
    return shifted > 0


def main() -> None:
    im = Image.open(REF).convert("RGB")
    rgb = np.asarray(im)
    h, w = rgb.shape[:2]
    sx, sy = ART_W / w, ART_H / h

    blobs = blob_masks(rgb)
    print("blobs", len(blobs))
    for i, m in enumerate(blobs):
        ys, xs = np.where(m)
        print(f"  {i}: area={m.sum()} cx={xs.mean():.0f} cy={ys.mean():.0f}")

    named = classify(blobs, h, w)
    print("named", list(named.keys()))

    paths: dict[str, str] = {}
    qa = rgb.copy()

    for name, region in named.items():
        mask_cnt = outer_contour(region)
        if mask_cnt is None:
            continue
        mask_m = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(mask_m, [mask_cnt], -1, 255, -1)
        mask_bin = mask_m > 0

        back = solid_back(rgb, mask_bin)
        if back is None:
            back = synthetic_back(mask_bin)
        back_cnt = outer_contour(back)

        sid_mask = f"{name}-mask"
        paths[sid_mask] = contour_to_path(mask_cnt, sx, sy)
        cv2.drawContours(qa, [mask_cnt], -1, (255, 23, 68), 2)

        if back_cnt is not None:
            sid_back = f"{name}-back"
            paths[sid_back] = contour_to_path(back_cnt, sx, sy)
            cv2.drawContours(qa, [back_cnt], -1, (0, 229, 255), 2)

        print(name, "mask", cv2.contourArea(mask_cnt), "back", cv2.contourArea(back_cnt) if back_cnt is not None else 0)

    PATHS.mkdir(parents=True, exist_ok=True)
    for p in PATHS.glob("*.svg"):
        p.unlink()
    for sid, d in paths.items():
        (PATHS / f"{sid}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ART_W:g} {ART_H:g}">'
            f'<path id="{sid}" fill="#ccc" d="{d}"/></svg>\n',
            encoding="utf-8",
        )

    Image.fromarray(qa).save(QA)
    print("qa", QA)

    b64 = base64.b64encode(REF.read_bytes()).decode("ascii")
    # Stable draw order: backs then masks
    order = []
    for name in ["about", "na-1", "na-2", "na-3", "na-4"]:
        for kind in ("back", "mask"):
            sid = f"{name}-{kind}"
            if sid in paths:
                order.append(sid)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {ART_W:g} {ART_H:g}" width="{ART_W:g}" height="{ART_H:g}">',
        f'  <image id="REF" width="{ART_W:g}" height="{ART_H:g}" opacity="0.45" '
        f'href="data:image/png;base64,{b64}"/>',
        '  <g id="SHAPES">',
    ]
    for sid in order:
        # Solid fills only (no photos) — back = cyan, mask = red
        col = "#00e5ff" if sid.endswith("-back") else "#ff1744"
        lines.append(
            f'    <path id="{sid}" fill="{col}" fill-opacity="0.55" '
            f'stroke="{col}" stroke-width="1.5" d="{paths[sid]}"/>'
        )
    lines += ["  </g>", "</svg>", ""]
    pack = OUT / "figma-pack-below.svg"
    pack.write_text("\n".join(lines), encoding="utf-8")
    print("pack", pack)
    print("ids", order)

    (OUT / "approved" / "below_paths_meta.json").write_text(
        json.dumps(
            {
                "artboard": [ART_W, ART_H],
                "ids": order,
                "ref": "approved/below-ref.png",
                "method": "cream-delta + open-text + outer-only + solid-back",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
