from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticfilesRunserverCommand,
)

from catalog.platform.static_handler import SiteAwareStaticFilesHandler


class Command(StaticfilesRunserverCommand):
    help = 'Like runserver, but /static/ is resolved per site Host/theme.'

    def get_handler(self, *args, **options):
        """Use site-aware static handler instead of the default one."""
        handler = super(StaticfilesRunserverCommand, self).get_handler(*args, **options)
        use_static = options.get('use_static_handler', True) and (options['insecure_serving'] or options['use_static_handler'])
        # Mirror parent logic, but with SiteAwareStaticFilesHandler
        from django.conf import settings

        if use_static and (settings.DEBUG or options.get('insecure_serving')):
            return SiteAwareStaticFilesHandler(handler)
        return handler
