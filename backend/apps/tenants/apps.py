from django.apps import AppConfig


class TenantsConfig(AppConfig):
    name = "apps.tenants"
    label = "tenants"
    verbose_name = "Ginásios"

    def ready(self):
        from . import signals  # noqa: F401
