from django.apps import AppConfig


class GestaoConfig(AppConfig):
    name = "apps.gestao"
    label = "gestao"
    verbose_name = "Gestão de sócios"

    def ready(self):
        from . import signals  # noqa: F401
