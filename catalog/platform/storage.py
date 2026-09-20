"""Per-site media storage that resolves location on every I/O (not once at import)."""
from __future__ import annotations

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .context import get_current_site


class SiteFileSystemStorage(FileSystemStorage):
    """Store uploaded media inside the active site folder."""

    def __init__(self, location=None, base_url=None, **kwargs):
        # Never bake a site-specific path into the process singleton.
        super().__init__(
            location=location or settings.MEDIA_ROOT,
            base_url=base_url or settings.MEDIA_URL,
            **kwargs,
        )

    def _resolve_location(self) -> str:
        site = get_current_site()
        if site:
            site.media_dir.mkdir(parents=True, exist_ok=True)
            return str(site.media_dir)
        return str(settings.MEDIA_ROOT)

    @property
    def base_location(self):
        return self._resolve_location()

    @base_location.setter
    def base_location(self, value):
        # FileSystemStorage.__init__ assigns base_location; ignore sticky value.
        self._base_location_init = value

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @location.setter
    def location(self, value):
        self._location_init = value

    def deconstruct(self):
        name, obj, args, kwargs = super().deconstruct()
        kwargs.pop('location', None)
        return name, obj, args, kwargs
