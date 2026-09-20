"""Theme-aware frontend dispatch: classic Django templates vs ceramics SPA."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse

from catalog.views_frontend import (
    about as about_classic,
    cart as cart_classic,
    catalog as catalog_classic,
    contact as contact_classic,
    delivery as delivery_classic,
    faq as faq_classic,
    index as index_classic,
    product_detail as product_classic,
)


def _is_ceramics(request: HttpRequest) -> bool:
    site = getattr(request, 'site', None)
    return bool(site and site.theme == 'ceramics')


def _spa(request: HttpRequest) -> HttpResponse:
    from catalog.views_spa import spa

    return spa(request)


def index(request):
    return _spa(request) if _is_ceramics(request) else index_classic(request)


def catalog(request):
    return _spa(request) if _is_ceramics(request) else catalog_classic(request)


def product_detail(request, slug):
    return _spa(request) if _is_ceramics(request) else product_classic(request, slug)


def cart(request):
    return _spa(request) if _is_ceramics(request) else cart_classic(request)


def about(request):
    return _spa(request) if _is_ceramics(request) else about_classic(request)


def contact(request):
    return _spa(request) if _is_ceramics(request) else contact_classic(request)


def delivery(request):
    return _spa(request) if _is_ceramics(request) else delivery_classic(request)


def faq(request):
    return _spa(request) if _is_ceramics(request) else faq_classic(request)
