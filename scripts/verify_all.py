"""Sanity checks: gitignore, sites layout, platform + admin."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

fails: list[str] = []
oks: list[str] = []


def ok(msg: str) -> None:
    oks.append(msg)
    print(f'OK  {msg}')


def fail(msg: str) -> None:
    fails.append(msg)
    print(f'FAIL  {msg}')


def ignored(path: str) -> bool:
    r = subprocess.run(
        ['git', 'check-ignore', '-q', path],
        cwd=ROOT,
        capture_output=True,
    )
    return r.returncode == 0


def check_ignore_rules() -> None:
    print('\n=== gitignore ===')
    must_ignore = [
        'sites/registry.json',
        'sites/demo-main/config.json',
        'sites/demo-main/db.sqlite3',
        '.env',
        'db.sqlite3',
        'venv/',
        'media/x.jpg',
        'staticfiles/',
    ]
    must_keep = [
        'sites.example/registry.json',
        'sites.example/demo-main/config.json',
        'catalog/platform/bootstrap.py',
        'themes/main/theme.json',
        'scripts/run_platform_local.ps1',
        '.env.example',
        'manage.py',
    ]
    for p in must_ignore:
        (ok if ignored(p) else fail)(f'ignore {p}')
    for p in must_keep:
        (ok if not ignored(p) else fail)(f'trackable {p}')


def check_sites_layout() -> None:
    print('\n=== sites layout ===')
    if (ROOT / 'sites' / 'registry.json').exists():
        ok('local sites/registry.json present (runtime)')
    else:
        fail('local sites/registry.json missing — run scripts/run_platform_local.ps1')

    example = ROOT / 'sites.example'
    if not (example / 'registry.json').exists():
        fail('sites.example/registry.json missing')
        return
    ok('sites.example/registry.json present')

    import json

    reg = json.loads((example / 'registry.json').read_text(encoding='utf-8'))
    site_slugs = sorted(reg.get('sites', {}))
    theme_slugs = sorted(reg.get('themes', {}))
    if theme_slugs != ['ceramics', 'eshop', 'front2', 'hero', 'main', 'meridian', 'national', 'wood']:
        fail(f'themes in example registry unexpected: {theme_slugs}')
    else:
        ok(f'example themes: {theme_slugs}')

    expected = ['demo-ceramics', 'demo-eshop', 'demo-front2', 'demo-hero', 'demo-main', 'demo-meridian', 'demo-national', 'demo-wood']

    if site_slugs != expected:
        fail(f'example sites unexpected: {site_slugs}')
    else:
        ok(f'example sites: {site_slugs}')

    for slug in expected:
        cfg = example / slug / 'config.json'
        (ok if cfg.exists() else fail)(f'sites.example/{slug}/config.json')

    # git status should not list sites/ as untracked files we care about
    st = subprocess.run(
        ['git', 'status', '--short', 'sites/'],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if st.stdout.strip():
        # Ignored dirs typically show nothing; if something appears, warn
        if any(line.startswith('??') for line in st.stdout.splitlines()):
            fail(f'sites/ still showing as untracked:\n{st.stdout}')
        else:
            ok('sites/ not untracked in git status')
    else:
        ok('sites/ invisible to git status (ignored)')


def check_platform() -> None:
    print('\n=== platform + admin ===')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_platform.settings')
    import django

    django.setup()
    from django.conf import settings
    from django.test import Client

    from catalog.platform.registry import load_registry

    if not settings.PLATFORM_MODE:
        fail('PLATFORM_MODE is off')
        return
    ok('PLATFORM_MODE on')

    themes, sites = load_registry()
    if set(themes) != {'main', 'front2', 'eshop', 'hero', 'meridian', 'wood', 'national', 'ceramics'}:
        fail(f'themes {sorted(themes)}')
    else:
        ok('8 themes loaded')

    client = Client()
    hosts = [
        ('demo-main.localhost', 'main'),
        ('demo-front2.localhost', 'front2'),
        ('demo-eshop.localhost', 'eshop'),
        ('demo-hero.localhost', 'hero'),
        ('demo-meridian.localhost', 'meridian'),
        ('demo-wood.localhost', 'wood'),
        ('demo-national.localhost', 'national'),
        ('demo-ceramics.localhost', 'ceramics'),
    ]
    for host, theme in hosts:
        resp = client.get('/', HTTP_HOST=host)
        if resp.status_code != 200:
            fail(f'{host} home {resp.status_code}')
            continue
        body = resp.content.decode('utf-8', errors='ignore')
        if f'<!-- theme:{theme} -->' not in body and theme != 'ceramics':
            # ceramics SPA may use different marker
            if theme == 'ceramics' and 'id="root"' in body:
                ok(f'{host} SPA')
            else:
                fail(f'{host} theme marker')
        else:
            if theme == 'ceramics' and 'id="root"' not in body and f'<!-- theme:{theme} -->' not in body:
                fail(f'{host} ceramics body')
            else:
                ok(f'{host} home 200')

        login = client.post(
            '/admin/login/',
            {'username': 'admin', 'password': 'admin', 'next': '/admin/'},
            HTTP_HOST=host,
        )
        if login.status_code not in (200, 302):
            fail(f'{host} admin login {login.status_code}')
            continue
        admin = client.get('/admin/', HTTP_HOST=host)
        if admin.status_code != 200:
            fail(f'{host} admin {admin.status_code}')
            continue
        html = admin.content.decode('utf-8', errors='ignore')
        if 'custom_admin.css' not in html:
            fail(f'{host} admin missing css link')
        elif 'fs-admin' not in html:
            fail(f'{host} admin missing fs-admin')
        else:
            ok(f'{host} admin OK')
        client.logout()

    from django.contrib.staticfiles import finders

    css = finders.find('admin/css/custom_admin.css')
    if css and 'store' in str(css).replace('\\', '/'):
        ok(f'admin CSS from store: {css}')
    else:
        fail(f'admin CSS finder: {css}')


def check_seed_script() -> None:
    print('\n=== run_platform_local seed logic ===')
    text = (ROOT / 'scripts' / 'run_platform_local.ps1').read_text(encoding='utf-8')
    if 'sites.example' in text and 'Seeding local sites' in text:
        ok('run_platform_local seeds from sites.example')
    else:
        fail('run_platform_local missing sites.example seed block')


if __name__ == '__main__':
    check_ignore_rules()
    check_sites_layout()
    check_seed_script()
    check_platform()
    print('\n=== SUMMARY ===')
    print(f'passed={len(oks)} failed={len(fails)}')
    if fails:
        print('FAILURES:')
        for f in fails:
            print(' -', f)
        sys.exit(1)
    print('ALL CHECKS PASSED')
