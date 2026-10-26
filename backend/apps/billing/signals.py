from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from .models import Pagamento

# Enviado dentro da transação que confirma o pagamento (argumento: `pagamento`).
pagamento_confirmado = Signal()


@receiver(post_save, sender=Pagamento)
def faturar_pagamento_presencial(sender, instance: Pagamento, created, **kwargs):
    """Pagamentos registados no Admin (numerário, TPA, transferência) são faturados de imediato."""
    if (
        created
        and instance.metodo != Pagamento.Metodo.VINTI4
        and instance.estado == Pagamento.Estado.INICIADO
    ):
        from .services import confirmar_pagamento

        confirmar_pagamento(instance)
