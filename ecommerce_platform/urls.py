"""
URL configuration for ecommerce_platform project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalog.admin_context import get_admin_index_context
from catalog.platform.theme_views import (
    about,
    cart,
    catalog,
    contact,
    delivery,
    faq,
    index,
    product_detail,
)
from catalog.admin_config import unified_config_view


# Кастомный индекс админки - сохраняем оригинальный метод
_original_admin_index = admin.site.index

def admin_index_view(request, extra_context=None):
    extra_context = extra_context or {}
    try:
        extra_context.update(get_admin_index_context())
    except Exception:
        # Migrations / empty DB must not blank the admin shell
        pass
    return _original_admin_index(request, extra_context)

admin.site.index = admin_index_view

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/config/', admin.site.admin_view(unified_config_view), name='admin_unified_config'),
    path('admin/', admin.site.urls),
    path('api/', include('catalog.urls')),
    # Frontend (classic theme OR ceramics SPA depending on site.theme)
    path('', index, name='index'),
    path('catalog/', catalog, name='catalog'),
    path('catalog/<slug:slug>/', product_detail, name='product'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('cart/', cart, name='cart'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('delivery/', delivery, name='delivery'),
    path('faq/', faq, name='faq'),
]


if getattr(settings, 'PLATFORM_MODE', False):
    from django.urls import re_path
    from catalog.platform.media_views import site_media_serve

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', site_media_serve),
    ]
elif settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    from django.urls import re_path
    from django.contrib.staticfiles.views import serve as staticfiles_serve

    # Serve via finders (store/static + theme) — not empty STATIC_ROOT.
    # runserver also uses SiteAwareStaticFilesHandler; this covers Test Client / WSGI DEBUG.
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', staticfiles_serve, kwargs={'insecure': True}),
    ]

