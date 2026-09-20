from __future__ import annotations

from django.contrib.staticfiles.handlers import StaticFilesHandler

from .context import set_current_site
from .registry import get_site_by_host


class SiteAwareStaticFilesHandler(StaticFilesHandler):
    """
    runserver serves /static/ before Django middleware.
    Resolve the site from HTTP_HOST so theme static finders work.
    """

    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', '')
        site = get_site_by_host(host)
        set_current_site(site)
        try:
            return super().__call__(environ, start_response)
        finally:
            set_current_site(None)
