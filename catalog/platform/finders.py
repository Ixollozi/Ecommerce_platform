from __future__ import annotations

import os
from pathlib import Path

from django.contrib.staticfiles.finders import BaseFinder
from django.core.files.storage import FileSystemStorage

from .context import get_current_site
from .registry import get_theme


class SiteThemeStaticFinder(BaseFinder):
    """Serve /static/ from the active site's theme only (avoids CSS clashes)."""

    def __init__(self, app_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storages = {}

    def _storages_for_site(self):
        site = get_current_site()
        if not site:
            return []
        theme = get_theme(site.theme)
        if not theme:
            return []
        storages = []
        for directory in theme.static_dirs:
            if not directory.exists():
                continue
            key = str(directory)
            if key not in self.storages:
                self.storages[key] = FileSystemStorage(location=key)
            storages.append(self.storages[key])
        return storages

    def find(self, path, all=False, find_all=None):
        # Django 5.1+ uses find_all=; older used all=
        if find_all is not None:
            all = find_all
        # Shared admin chrome lives in store/static (AppDirectoriesFinder).
        # Do not let per-theme copies shadow or break it.
        if path.replace('\\', '/').startswith('admin/'):
            return [] if all else None
        matches = []
        for storage in self._storages_for_site():
            if storage.exists(path):
                matched = storage.path(path)
                if not all:
                    return matched
                matches.append(matched)
        return matches

    def list(self, ignore_patterns):
        for storage in self._storages_for_site():
            for root, _dirs, files in os.walk(storage.location):
                for name in files:
                    full = Path(root) / name
                    relative = full.relative_to(storage.location).as_posix()
                    if relative.startswith('admin/'):
                        continue
                    yield relative, storage
