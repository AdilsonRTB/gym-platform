from django.apps import AppConfig


class BillingConfig(AppConfig):
    name = "apps.billing"
    label = "billing"
    verbose_name = "Adesões e faturação"

    def ready(self):
        from . import signals  # noqa: F401
