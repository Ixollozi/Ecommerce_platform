from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from catalog.platform.context import site_context
from catalog.platform.registry import iter_sites


class Command(BaseCommand):
    help = 'Migrate all platform sites and create admin/admin superusers if missing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--load-sample-data',
            action='store_true',
            help='Run load_sample_data for each site after bootstrap.',
        )

    def handle(self, *args, **options):
        from django.conf import settings

        if not getattr(settings, 'PLATFORM_MODE', False):
            raise CommandError('Set PLATFORM_MODE=1 before running platform_bootstrap.')

        call_command('platform_migrate', verbosity=options.get('verbosity', 1))
        User = get_user_model()

        for site in iter_sites():
            with site_context(site):
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                    self.stdout.write(self.style.SUCCESS(f'{site.slug}: created admin/admin'))
                else:
                    self.stdout.write(f'{site.slug}: admin already exists')

                if options['load_sample_data']:
                    call_command('load_sample_data')

        self.stdout.write('')
        self.stdout.write('Local PoC URLs:')
        for site in iter_sites():
            host = site.hosts[0]
            self.stdout.write(f'  http://{host}:8000/  (admin: /admin, login admin/admin)')
