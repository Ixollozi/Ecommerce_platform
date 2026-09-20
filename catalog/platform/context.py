from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from .registry import SiteConfig

_current_site: ContextVar[SiteConfig | None] = ContextVar('current_site', default=None)


def get_current_site() -> SiteConfig | None:
    return _current_site.get()


def get_current_db_alias() -> str | None:
    site = get_current_site()
    return site.database_alias if site else None


def set_current_site(site: SiteConfig | None) -> None:
    _current_site.set(site)


@contextmanager
def site_context(site: SiteConfig | None):
    token = _current_site.set(site)
    try:
        yield site
    finally:
        _current_site.reset(token)
