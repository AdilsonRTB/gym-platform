"""Tarefa diária: gera as cobranças do período seguinte e envia os lembretes.

Idempotente: pode correr várias vezes por dia (ex.: de hora a hora) sem duplicar nada.
"""

from django.core.management.base import BaseCommand

from apps.gestao.services import enviar_lembretes, gerar_cobrancas
from apps.tenants.context import using_ginasio
from apps.tenants.models import Ginasio


class Command(BaseCommand):
    help = "Gera cobranças e envia lembretes de todos os ginásios ativos."

    def handle(self, *args, **options):
        for ginasio in Ginasio.objects.filter(estado=Ginasio.Estado.ATIVO).select_related("site"):
            if ginasio.site is None:
                continue
            with using_ginasio(ginasio):
                cobrancas = gerar_cobrancas(ginasio)
                lembretes = enviar_lembretes(ginasio)
            self.stdout.write(f"{ginasio.slug}: {cobrancas} cobranças, {lembretes} lembretes")
