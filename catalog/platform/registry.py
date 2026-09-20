from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from django.conf import settings


@dataclass(frozen=True)
class ThemeConfig:
    slug: str
    template_dirs: tuple[Path, ...]
    static_dirs: tuple[Path, ...]
    locale_dirs: tuple[Path, ...]


def site_database_alias(slug: str) -> str:
    """Safe Django DB alias (no hyphens — breaks connection handler)."""
    return f"site_{slug.replace('-', '_')}"


@dataclass(frozen=True)
class SiteConfig:
    slug: str
    hosts: tuple[str, ...]
    theme: str
    root: Path
    database_alias: str
    title: str = ''

    @property
    def config_path(self) -> Path:
        return self.root / 'config.json'

    @property
    def db_path(self) -> Path:
        return self.root / 'db.sqlite3'

    @property
    def media_dir(self) -> Path:
        return self.root / 'media'

    @property
    def static_dir(self) -> Path:
        return self.root / 'static'


def _resolve_paths(base: Path, entries: Iterable[str]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    for entry in entries:
        path = Path(entry)
        if not path.is_absolute():
            path = base / path
        resolved.append(path.resolve())
    return tuple(resolved)


def _normalize_host(host: str) -> str:
    host = (host or '').strip().lower()
    if ':' in host:
        host = host.split(':', 1)[0]
    return host


@lru_cache(maxsize=1)
def load_registry() -> tuple[dict[str, ThemeConfig], dict[str, SiteConfig]]:
    sites_root = Path(getattr(settings, 'SITES_ROOT', settings.BASE_DIR / 'sites'))
    registry_path = sites_root / 'registry.json'
    if not registry_path.exists():
        raise FileNotFoundError(f'Site registry not found: {registry_path}')

    with registry_path.open(encoding='utf-8') as handle:
        raw = json.load(handle)

    themes_root = settings.BASE_DIR / 'themes'
    themes: dict[str, ThemeConfig] = {}
    for slug, theme_data in raw.get('themes', {}).items():
        theme_base = themes_root / slug
        template_dirs = _resolve_paths(
            settings.BASE_DIR,
            theme_data.get('template_dirs', [f'themes/{slug}/templates']),
        )
        static_dirs = _resolve_paths(
            settings.BASE_DIR,
            theme_data.get('static_dirs', [f'themes/{slug}/static', 'static']),
        )
        locale_dirs = _resolve_paths(
            settings.BASE_DIR,
            theme_data.get('locale_dirs', [f'themes/{slug}/locale', 'locale']),
        )
        themes[slug] = ThemeConfig(
            slug=slug,
            template_dirs=template_dirs,
            static_dirs=static_dirs,
            locale_dirs=locale_dirs,
        )

    host_map: dict[str, str] = {}
    sites: dict[str, SiteConfig] = {}
    for slug, site_data in raw.get('sites', {}).items():
        site_root = sites_root / slug
        hosts = tuple(_normalize_host(item) for item in site_data.get('hosts', []))
        theme = site_data.get('theme', 'main')
        if theme not in themes:
            raise KeyError(f"Site '{slug}' references unknown theme '{theme}'")
        site = SiteConfig(
            slug=slug,
            hosts=hosts,
            theme=theme,
            root=site_root.resolve(),
            database_alias=site_database_alias(slug),
            title=site_data.get('title', slug),
        )
        sites[slug] = site
        for host in hosts:
            host_map[host] = slug

    setattr(load_registry, 'host_map', host_map)
    return themes, sites


def get_site(slug: str) -> SiteConfig | None:
    _, sites = load_registry()
    return sites.get(slug)


def get_site_by_host(host: str) -> SiteConfig | None:
    _, sites = load_registry()
    host_map = getattr(load_registry, 'host_map', {})
    slug = host_map.get(_normalize_host(host))
    if not slug:
        return None
    return sites.get(slug)


def get_theme(slug: str) -> ThemeConfig | None:
    themes, _ = load_registry()
    return themes.get(slug)


def iter_sites() -> Iterable[SiteConfig]:
    _, sites = load_registry()
    return sites.values()
