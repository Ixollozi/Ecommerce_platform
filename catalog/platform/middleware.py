from __future__ import annotations

from django.conf import settings
from django.http import Http404, HttpResponseBadRequest

from .context import set_current_site
from .registry import get_site_by_host


class SiteHostMiddleware:
    """
    Resolve the current site from the HTTP Host header.
    Local PoC: demo-alpha.localhost / demo-beta.localhost
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        site = get_site_by_host(host)
        if site is None:
            if settings.DEBUG:
                known = sorted({host for site_cfg in _all_hosts()})
                return HttpResponseBadRequest(
                    'Unknown site host. '
                    f'Received: {host!r}. '
                    f'Known hosts: {", ".join(known) or "(none)"}'
                )
            raise Http404('Site not found')

        request.site = site
        set_current_site(site)
        try:
            return self.get_response(request)
        finally:
            set_current_site(None)


def _all_hosts():
    from .registry import iter_sites

    for site in iter_sites():
        for host in site.hosts:
            yield host
