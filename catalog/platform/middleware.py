from __future__ import annotations

import logging

from django.conf import settings
from django.http import Http404, HttpResponseBadRequest

from .context import set_current_host, set_current_site
from .registry import get_site_by_host

logger = logging.getLogger('catalog.platform')


class SiteHostMiddleware:
    """
    Resolve the current site from the HTTP Host header.
    Local PoC: demo-alpha.localhost / demo-beta.localhost
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        set_current_host(host)
        site = get_site_by_host(host)
        if site is None:
            logger.warning('Unknown site host=%r', host)
            set_current_site(None)
            try:
                if settings.DEBUG:
                    known = sorted({h for h in _all_hosts()})
                    return HttpResponseBadRequest(
                        'Unknown site host. '
                        f'Received: {host!r}. '
                        f'Known hosts: {", ".join(known) or "(none)"}'
                    )
                raise Http404('Site not found')
            finally:
                set_current_host(None)

        request.site = site
        set_current_site(site)
        try:
            return self.get_response(request)
        finally:
            set_current_site(None)
            set_current_host(None)


def _all_hosts():
    from .registry import iter_sites

    for site in iter_sites():
        for host in site.hosts:
            yield host
