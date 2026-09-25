from __future__ import annotations

import os
from pathlib import Path


def apply_platform_settings(settings_dict: dict) -> None:
    """Mutate Django settings for multi-site platform mode."""
    base_dir: Path = settings_dict['BASE_DIR']
    sites_root = base_dir / 'sites'
    settings_dict['PLATFORM_MODE'] = True
    settings_dict['SITES_ROOT'] = sites_root

    from catalog.platform.registry import iter_sites, load_registry

    load_registry.cache_clear()
    themes, sites = load_registry()

    databases = {}
    for site in sites.values():
        site.root.mkdir(parents=True, exist_ok=True)
        site.media_dir.mkdir(parents=True, exist_ok=True)
        databases[site.database_alias] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': site.db_path,
        }

    if not databases:
        raise RuntimeError('Platform mode enabled but sites/registry.json has no sites')

    first_alias = next(iter(databases))
    databases['default'] = databases[first_alias]
    settings_dict['DATABASES'] = databases
    settings_dict['DATABASE_ROUTERS'] = ['catalog.platform.db_router.SiteDatabaseRouter']

    middleware = list(settings_dict['MIDDLEWARE'])
    site_mw = 'catalog.platform.middleware.SiteHostMiddleware'
    request_mw = 'catalog.platform.request_logging.RequestLogMiddleware'
    if site_mw not in middleware:
        security_index = middleware.index('django.middleware.security.SecurityMiddleware')
        middleware.insert(security_index + 1, site_mw)
    if request_mw not in middleware:
        site_index = middleware.index(site_mw)
        middleware.insert(site_index + 1, request_mw)
    settings_dict['MIDDLEWARE'] = middleware

    allowed_hosts = set(settings_dict.get('ALLOWED_HOSTS', []))
    if allowed_hosts == {'*'}:
        allowed_hosts = set()
    for site in sites.values():
        allowed_hosts.update(site.hosts)
    allowed_hosts.update({'localhost', '127.0.0.1', '[::1]'})
    settings_dict['ALLOWED_HOSTS'] = sorted(allowed_hosts)

    csrf_origins = set(settings_dict.get('CSRF_TRUSTED_ORIGINS', []))
    for site in sites.values():
        for host in site.hosts:
            csrf_origins.add(f'http://{host}')
            csrf_origins.add(f'https://{host}')
            if host.endswith('.localhost'):
                csrf_origins.add(f'http://{host}:8000')
                csrf_origins.add(f'http://{host}:8001')
    settings_dict['CSRF_TRUSTED_ORIGINS'] = sorted(csrf_origins)

    shared_templates = base_dir / 'templates'
    settings_dict['TEMPLATES'] = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [str(shared_templates)] if shared_templates.exists() else [],
            'APP_DIRS': False,
            'OPTIONS': {
                'context_processors': settings_dict['TEMPLATES'][0]['OPTIONS']['context_processors'],
                'loaders': [
                    'catalog.platform.loaders.SiteThemeLoader',
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ],
            },
        }
    ]

    locale_dirs = [str(base_dir / 'locale')]
    for theme in themes.values():
        locale_dirs.extend(str(path) for path in theme.locale_dirs if path.exists())
    settings_dict['LOCALE_PATHS'] = list(dict.fromkeys(locale_dirs))

    # Do NOT dump all theme static dirs into STATICFILES_DIRS — that mixes themes.
    # Theme assets: SiteThemeStaticFinder. Admin chrome: store/static via AppDirectories.
    shared_static = base_dir / 'static'
    settings_dict['STATICFILES_DIRS'] = [str(shared_static)] if shared_static.exists() else []
    settings_dict['STATICFILES_FINDERS'] = [
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'catalog.platform.finders.SiteThemeStaticFinder',
        'django.contrib.staticfiles.finders.FileSystemFinder',
    ]
    settings_dict['DEFAULT_FILE_STORAGE'] = 'catalog.platform.storage.SiteFileSystemStorage'
    settings_dict['STORAGES'] = {
        'default': {
            'BACKEND': 'catalog.platform.storage.SiteFileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

    settings_dict['PLATFORM_THEMES'] = {slug: theme.slug for slug, theme in themes.items()}

    _configure_celery(settings_dict)


def _configure_celery(settings_dict: dict) -> None:
    debug = settings_dict.get('DEBUG', True)
    eager_env = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '').strip().lower()
    if eager_env in ('true', '1', 'yes'):
        eager = True
    elif eager_env in ('false', '0', 'no'):
        eager = False
    else:
        eager = bool(debug)

    settings_dict['CELERY_ACCEPT_CONTENT'] = ['json']
    settings_dict['CELERY_TASK_SERIALIZER'] = 'json'
    settings_dict['CELERY_RESULT_SERIALIZER'] = 'json'
    settings_dict['CELERY_TIMEZONE'] = settings_dict.get('TIME_ZONE', 'Asia/Tashkent')
    settings_dict['CELERY_TASK_EAGER_PROPAGATES'] = True
    settings_dict['CELERY_TASK_ALWAYS_EAGER'] = eager

    if eager:
        settings_dict['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'memory://')
        settings_dict['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'cache+memory://')
    else:
        broker = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
        settings_dict['CELERY_BROKER_URL'] = broker
        settings_dict['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', broker)

    settings_dict['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN', '')
