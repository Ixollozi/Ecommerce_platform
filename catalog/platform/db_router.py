from __future__ import annotations

from .context import get_current_db_alias


class SiteDatabaseRouter:
    """Route ORM operations to the current site's SQLite database."""

    def db_for_read(self, model, **hints):
        return get_current_db_alias() or 'default'

    def db_for_write(self, model, **hints):
        return get_current_db_alias() or 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        from django.conf import settings

        if getattr(settings, 'PLATFORM_MODE', False):
            return db.startswith('site_')
        return db == 'default'
