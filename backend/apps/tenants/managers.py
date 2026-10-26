from django.db import models

from .context import current_state


class TenantQuerySet(models.QuerySet):
    def for_ginasio(self, ginasio):
        return self.filter(ginasio=ginasio)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """Manager por omissão de todo o conteúdo: filtra sempre pelo ginásio atual."""

    def get_queryset(self):
        qs = super().get_queryset()
        state = current_state()
        if state is None:
            return qs
        if state.ginasio is None:
            return qs.none()
        return qs.filter(ginasio_id=state.ginasio.pk)
