from django.apps import AppConfig


class MarketAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market'

    def ready(self):
        from market import signals  # Инициализация сигналов
