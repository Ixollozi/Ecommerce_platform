"""HTTP request logging with site/host context (after SiteHostMiddleware)."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger('catalog.platform.request')

_SKIP_PREFIXES = ('/static/', '/media/')
_SKIP_EXACT = frozenset({'/favicon.ico', '/favicon.png', '/health', '/healthz'})


def _should_skip(path: str) -> bool:
    if path in _SKIP_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in _SKIP_PREFIXES)


class RequestLogMiddleware:
    """Log method, path, status, duration for non-static requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _should_skip(request.path):
            return self.get_response(request)

        started = time.perf_counter()
        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                '%s %s status=500 duration_ms=%s',
                request.method,
                request.path,
                duration_ms,
            )
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            '%s %s status=%s duration_ms=%s',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
