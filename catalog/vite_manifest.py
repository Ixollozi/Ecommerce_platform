"""Чтение Vite manifest.json для подключения CSS/JS к SPA-шаблону."""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings


def _manifest_candidates() -> list[Path]:
    paths: list[Path] = []
    try:
        from catalog.platform.context import get_current_site
        from catalog.platform.registry import get_theme

        site = get_current_site()
        if site:
            theme = get_theme(site.theme)
            if theme:
                for static_dir in theme.static_dirs:
                    front = static_dir / 'frontend'
                    paths.append(front / '.vite' / 'manifest.json')
                    paths.append(front / 'manifest.json')
    except Exception:
        pass

    base = Path(settings.BASE_DIR) / 'static' / 'frontend'
    paths.append(base / '.vite' / 'manifest.json')
    paths.append(base / 'manifest.json')
    paths.append(Path(settings.STATIC_ROOT) / 'frontend' / '.vite' / 'manifest.json')
    paths.append(Path(settings.STATIC_ROOT) / 'frontend' / 'manifest.json')
    return paths


def get_spa_vite_assets() -> dict[str, list[str]] | None:
    """Return /static/frontend/... URLs for the Vite entry."""
    manifest_path = next((p for p in _manifest_candidates() if p.is_file()), None)
    if manifest_path is None:
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None

    entry = data.get('index.html')
    if not entry:
        return None

    static_root = settings.STATIC_URL.rstrip('/')
    if not static_root.startswith('/'):
        static_root = '/' + static_root

    def to_url(rel: str) -> str:
        rel = rel.lstrip('/')
        return f'{static_root}/frontend/{rel}'

    js_urls: list[str] = []
    if entry.get('file'):
        js_urls.append(to_url(entry['file']))
    for imp in entry.get('imports') or []:
        chunk = data.get(imp)
        if chunk and chunk.get('file'):
            u = to_url(chunk['file'])
            if u not in js_urls:
                js_urls.append(u)

    css_urls: list[str] = [to_url(href) for href in entry.get('css') or []]
    return {'js': js_urls, 'css': css_urls}
