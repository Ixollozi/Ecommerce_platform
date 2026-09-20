from __future__ import annotations

from django.views.static import serve

from catalog.platform.context import get_current_site


def site_media_serve(request, path, document_root=None):
    from django.conf import settings

    site = get_current_site()
    if site:
        root = site.media_dir
        root.mkdir(parents=True, exist_ok=True)
    else:
        root = document_root or settings.MEDIA_ROOT
    return serve(request, path, document_root=str(root))
