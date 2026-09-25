"""Logging filters that inject current platform site/host into LogRecord."""

from __future__ import annotations

import logging


class SiteContextFilter(logging.Filter):
    """Add ``site`` and ``host`` attributes from platform contextvars."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from catalog.platform.context import get_current_host, get_current_site

            site = get_current_site()
            host = get_current_host()
            record.site = site.slug if site is not None else '-'
            record.host = host or '-'
        except Exception:
            if not hasattr(record, 'site'):
                record.site = '-'
            if not hasattr(record, 'host'):
                record.host = '-'
        return True
