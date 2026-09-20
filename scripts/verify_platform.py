import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_platform.settings')

import django

django.setup()

from django.conf import settings
from django.test import Client

from catalog.platform.context import site_context
from catalog.platform.finders import SiteThemeStaticFinder
from catalog.platform.registry import get_site, load_registry

assert settings.PLATFORM_MODE
themes, sites = load_registry()
print('themes:', sorted(themes))
assert set(themes) == {'main', 'front2', 'eshop', 'hero', 'meridian', 'wood', 'national', 'ceramics'}

expected = {
    'demo-main': 'main',
    'demo-front2': 'front2',
    'demo-eshop': 'eshop',
    'demo-hero': 'hero',
    'demo-meridian': 'meridian',
    'demo-wood': 'wood',
    'demo-national': 'national',
    'demo-ceramics': 'ceramics',
}

for slug, theme in expected.items():
    assert sites[slug].theme == theme, (slug, sites[slug].theme, theme)
print('sites themes OK')

client = Client()
checks = [
    ('demo-main.localhost', 'main', 'Demo Main Shop', False),
    ('demo-front2.localhost', 'front2', 'Demo Front2 Shop', False),
    ('demo-eshop.localhost', 'eshop', 'Apex Goods', False),
    ('demo-hero.localhost', 'hero', 'HERO', False),

    ('demo-meridian.localhost', 'meridian', 'Meridian', False),
    ('demo-wood.localhost', 'wood', 'Demo Wood Shop', False),
    ('demo-national.localhost', 'national', 'Demo National Shop', False),
    ('demo-ceramics.localhost', 'ceramics', 'Demo Ceramics Shop', True),
]

finder = SiteThemeStaticFinder()
for host, theme, shop, is_spa in checks:
    resp = client.get('/', HTTP_HOST=host)
    assert resp.status_code == 200, (host, resp.status_code)
    body = resp.content.decode('utf-8', errors='ignore')
    assert f'<!-- theme:{theme} -->' in body, f'{host} missing marker'
    if is_spa:
        assert 'id="root"' in body, f'{host} missing SPA root'
        assert 'django-bootstrap' in body, f'{host} missing bootstrap'
        assert '/static/frontend/' in body or 'frontend/assets' in body, f'{host} missing SPA assets'
    else:
        assert shop in body, f'{host} missing shop name'
    site = get_site(next(s for s, t in expected.items() if t == theme))
    with site_context(site):
        found = finder.find('styles.css') if not is_spa else finder.find('frontend/index.html')
        assert found, f'no static for {theme}: {found}'
    print(f'OK {host} theme={theme} spa={is_spa}')

# Admin: shared chrome must resolve without theme, and load on every host
from django.contrib.staticfiles import finders as static_finders

admin_css = static_finders.find('admin/css/custom_admin.css')
assert admin_css and 'store' in str(admin_css).replace('\\', '/'), admin_css
print('admin CSS finder:', admin_css)

django_admin_css = static_finders.find('admin/css/base.css')
assert django_admin_css, 'django admin base.css missing'
print('django admin CSS:', django_admin_css)

for host, theme, shop, is_spa in checks:
    login = client.post(
        '/admin/login/',
        {'username': 'admin', 'password': 'admin', 'next': '/admin/'},
        HTTP_HOST=host,
    )
    # follow redirect after login
    assert login.status_code in (200, 302), (host, login.status_code)
    admin_resp = client.get('/admin/', HTTP_HOST=host)
    assert admin_resp.status_code == 200, (host, admin_resp.status_code)
    html = admin_resp.content.decode('utf-8', errors='ignore')
    assert 'admin/css/custom_admin.css' in html, f'{host} missing custom_admin.css link'
    assert 'admin/css/base.css' in html or 'admin/css/dark_mode.css' in html or 'dashboard' in html, (
        f'{host} admin shell looks broken'
    )
    assert 'Сводка магазина' in html or 'dash-hero' in html, f'{host} missing dashboard'
    css = client.get('/static/admin/css/custom_admin.css', HTTP_HOST=host)
    assert css.status_code == 200, (host, 'custom_admin.css', css.status_code)
    css_body = b''.join(css.streaming_content) if hasattr(css, 'streaming_content') else css.content
    assert b'--teal' in css_body or b'dash-hero' in css_body
    base = client.get('/static/admin/css/base.css', HTTP_HOST=host)
    assert base.status_code == 200, (host, 'base.css', base.status_code)
    print(f'OK admin {host}')
    client.logout()

print('\nALL THEMES + ADMIN PASSED')
