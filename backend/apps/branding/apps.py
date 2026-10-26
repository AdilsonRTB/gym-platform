from django.apps import AppConfig


class BrandingConfig(AppConfig):
    name = "apps.branding"
    label = "branding"
    verbose_name = "Marca"

    def ready(self):
        from . import signals  # noqa: F401
