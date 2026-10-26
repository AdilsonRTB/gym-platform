from django.dispatch import receiver

from apps.billing.signals import pagamento_confirmado


@receiver(pagamento_confirmado)
def atualizar_socio(sender, pagamento, **kwargs):
    from .services import ao_confirmar_pagamento

    ao_confirmar_pagamento(pagamento)
