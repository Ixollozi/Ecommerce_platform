"""Пути к собранной Vite-витрине (theme static / staticfiles)."""
from __future__ import annotations

from pathlib import Path

from django.conf import settings


def _theme_frontend_root() -> Path | None:
    try:
        from catalog.platform.context import get_current_site
        from catalog.platform.registry import get_theme

        site = get_current_site()
        if not site:
            return None
        theme = get_theme(site.theme)
        if not theme:
            return None
        for static_dir in theme.static_dirs:
            candidate = static_dir / 'frontend'
            if (candidate / 'index.html').is_file():
                return candidate
    except Exception:
        return None
    return None


def spa_index_path() -> Path | None:
    """
    Absolute path to frontend/index.html after Vite build.
    Prefers active theme static, then project static/, then STATIC_ROOT.
    """
    theme_root = _theme_frontend_root()
    if theme_root is not None:
        return theme_root / 'index.html'

    if settings.DEBUG:
        from django.contrib.staticfiles import finders

        found = finders.find('frontend/index.html')
        if found:
            return Path(found)
        dev = Path(settings.BASE_DIR) / 'static' / 'frontend' / 'index.html'
        if dev.is_file():
            return dev

    prod = Path(settings.STATIC_ROOT) / 'frontend' / 'index.html'
    return prod if prod.is_file() else None
