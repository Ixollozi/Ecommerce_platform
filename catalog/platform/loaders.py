from __future__ import annotations

from django.template.loaders.filesystem import Loader as FilesystemLoader

from .context import get_current_site
from .registry import get_theme


class SiteThemeLoader(FilesystemLoader):
    """Load templates from the active site's theme directories."""

    def get_dirs(self):
        site = get_current_site()
        if not site:
            return []
        theme = get_theme(site.theme)
        if not theme:
            return []
        return [str(path) for path in theme.template_dirs if path.exists()]

    def get_template_sources(self, template_name):
        # Shared admin UI lives in store/templates (app loader). Theme copies
        # must not shadow it — avoids broken extends and per-theme drift.
        if template_name.replace('\\', '/').startswith('admin/'):
            return
        yield from super().get_template_sources(template_name)
