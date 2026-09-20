"""Display URL helpers for products and categories (upload > URL > gallery)."""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

_HASH_CACHE: dict[str, str] = {}


def _file_fingerprint(file_field) -> str | None:
    """Generate a content/stem fingerprint for deduplicating uploaded images."""
    if not file_field:
        return None
    name = getattr(file_field, "name", None)
    if not name:
        return None
    name_str = str(name).strip()
    if not name_str:
        return None

    if name_str in _HASH_CACHE:
        return _HASH_CACHE[name_str]

    # Try fast storage-based content hash
    try:
        storage = getattr(file_field, "storage", None)
        if storage and storage.exists(name_str):
            size = getattr(file_field, "size", None)
            if size is None:
                try:
                    size = storage.size(name_str)
                except Exception:
                    size = None

            h = hashlib.md5()
            if size is not None:
                h.update(str(size).encode("ascii"))
            with storage.open(name_str, "rb") as f:
                chunk = f.read(65536)
                h.update(chunk)
                if size and size > 131072:
                    f.seek(-65536, os.SEEK_END)
                    h.update(f.read(65536))
                else:
                    while rest := f.read(65536):
                        h.update(rest)
            digest = f"md5:{h.hexdigest()}"
            _HASH_CACHE[name_str] = digest
            return digest
    except Exception:
        pass

    # Fallback to normalized stem (strip django unique suffix) + size
    try:
        size = getattr(file_field, "size", 0)
    except Exception:
        size = 0
    clean_stem = re.sub(r'(_[a-zA-Z0-9]{7}|_\d+)$', '', Path(name_str).stem)
    ext = Path(name_str).suffix.lower()
    fp = f"stem:{clean_stem}{ext}:{size}"
    _HASH_CACHE[name_str] = fp
    return fp


def _safe_file_url(file_field) -> str:
    if not file_field:
        return ""
    try:
        name = getattr(file_field, "name", None)
        if not name:
            return ""
        return file_field.url or ""
    except Exception:
        return ""


def product_display_image_url(product) -> str:
    """
    Best card/primary image URL for a product.
    Priority: uploaded primary → first ProductImage → external URL.
    (External URL is last so demo Unsplash links don't hide real uploads.)
    """
    if product is None:
        return ""

    url = _safe_file_url(getattr(product, "image", None))
    if url:
        return url

    images = getattr(product, "images", None)
    if images is not None:
        try:
            iterable = images.all() if hasattr(images, "all") else images
            for img in iterable:
                url = _safe_file_url(getattr(img, "image", None))
                if url:
                    return url
        except Exception:
            pass

    return (getattr(product, "image_url", None) or "").strip()


def category_display_image_url(category) -> str:
    if category is None:
        return ""
    if isinstance(category, dict):
        return (category.get("image_url") or category.get("image") or "") or ""
    url = _safe_file_url(getattr(category, "image", None))
    if url:
        return url
    return (getattr(category, "image_url", None) or "").strip()


def product_gallery_urls(product) -> list[str]:
    """
    Ordered unique gallery URLs: primary file + extras + external URL last.
    Intelligently deduplicates identical images even if saved with Django random suffixes.
    """
    seen_urls: set[str] = set()
    seen_fingerprints: set[str] = set()
    out: list[str] = []

    def add(file_field=None, raw_url=None) -> None:
        url = _safe_file_url(file_field) if file_field is not None else (raw_url or "").strip()
        if not url:
            return

        # URL-level deduplication
        clean_url = url.split("?")[0].rstrip("/").lower()
        if clean_url in seen_urls:
            return

        # Content/fingerprint deduplication
        fp = _file_fingerprint(file_field) if file_field is not None else clean_url
        if fp and fp in seen_fingerprints:
            return

        seen_urls.add(clean_url)
        if fp:
            seen_fingerprints.add(fp)
        out.append(url)

    if product is None:
        return out

    add(file_field=getattr(product, "image", None))

    images = getattr(product, "images", None)
    if images is not None:
        try:
            iterable = images.all() if hasattr(images, "all") else images
            for img in iterable:
                add(file_field=getattr(img, "image", None))
        except Exception:
            pass

    if not out:
        add(raw_url=getattr(product, "image_url", None) or "")
    return out

