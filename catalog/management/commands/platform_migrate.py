from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from catalog.platform.registry import iter_sites


def relabel_store_to_catalog(database_alias: str) -> None:
    """Rewrite historical app label store→catalog before MigrationLoader runs.

    Physical tables stay store_*; only django_migrations / contenttypes change.
    Safe to run repeatedly.
    """
    conn = connections[database_alias]
    # Fresh / empty DBs have no these tables yet — migrate will create them.
    tables = set(conn.introspection.table_names())
    if 'django_migrations' not in tables:
        return
    with conn.cursor() as cursor:
        cursor.execute("UPDATE django_migrations SET app = %s WHERE app = %s", ['catalog', 'store'])
        if 'django_content_type' in tables:
            cursor.execute(
                "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
                ['catalog', 'store'],
            )


class Command(BaseCommand):
    help = 'Apply migrations to every site database in platform mode.'

    def handle(self, *args, **options):
        from django.conf import settings

        if not getattr(settings, 'PLATFORM_MODE', False):
            raise CommandError('Set PLATFORM_MODE=1 before running platform_migrate.')

        for site in iter_sites():
            site.root.mkdir(parents=True, exist_ok=True)
            site.media_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(f'Migrating {site.slug} ({site.database_alias})...')
            relabel_store_to_catalog(site.database_alias)
            call_command(
                'migrate',
                database=site.database_alias,
                interactive=False,
                verbosity=options.get('verbosity', 1),
            )
        self.stdout.write(self.style.SUCCESS('All site databases migrated.'))
