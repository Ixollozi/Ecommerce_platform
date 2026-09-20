"""Relabel django_migrations/contenttypes store→catalog for a single database.

Use before plain `migrate` on non-platform (single-site) DBs.
Platform mode: prefer `python manage.py platform_migrate`.
"""
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from catalog.management.commands.platform_migrate import relabel_store_to_catalog


class Command(BaseCommand):
    help = 'One-time-safe: rename app label store→catalog in migration/contenttype tables.'

    def add_arguments(self, parser):
        parser.add_argument('--database', default=DEFAULT_DB_ALIAS)

    def handle(self, *args, **options):
        alias = options['database']
        relabel_store_to_catalog(alias)
        self.stdout.write(self.style.SUCCESS(f'Relabeled store->catalog on database={alias}'))
