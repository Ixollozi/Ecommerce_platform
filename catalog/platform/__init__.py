"""Multi-site platform: one Django process, many site folders (SQLite + config + theme)."""

from .context import get_current_site, site_context
from .registry import get_site, get_site_by_host, load_registry

__all__ = [
    'get_current_site',
    'get_site',
    'get_site_by_host',
    'load_registry',
    'site_context',
]
