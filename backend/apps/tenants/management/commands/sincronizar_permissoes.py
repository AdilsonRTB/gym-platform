from django.core.management.base import BaseCommand

from apps.tenants.models import Ginasio
from apps.tenants.permissions import sincronizar_grupos


class Command(BaseCommand):
    help = "Atualiza os grupos e permissões de todos os ginásios (correr depois de novas migrações)."

    def handle(self, *args, **options):
        for ginasio in Ginasio.objects.select_related("site", "colecao"):
            sincronizar_grupos(ginasio)
            self.stdout.write(f"✓ {ginasio.nome}")
