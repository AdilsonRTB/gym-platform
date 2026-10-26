from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = "apps.content"
    label = "content"
    verbose_name = "Conteúdo"

    def ready(self):
        from . import signals  # noqa: F401
