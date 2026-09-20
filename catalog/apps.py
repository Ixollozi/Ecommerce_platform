from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    
    def ready(self):
        import catalog.translation  # Импортируем переводы
        import catalog.signals  # Импортируем сигналы для уведомлений


