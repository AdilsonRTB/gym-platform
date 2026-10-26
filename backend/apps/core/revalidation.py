"""Webhook para o Next.js revalidar só as páginas afetadas de um ginásio."""

import logging
import threading

import requests
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def tags_for(ginasio_id: int, *tipos: str) -> list[str]:
    """Tags usadas nos fetch do Next.js.

    - `g:<id>:<tipo>` para o conteúdo (páginas, planos, aulas…);
    - `d:<domínio>` para a configuração do site, que o Next.js lê antes de saber o id do ginásio.
    """
    tags = [f"g:{ginasio_id}:{tipo}" for tipo in tipos]
    if "site" in tipos:
        from apps.tenants.models import Dominio

        tags += [
            f"d:{host}"
            for host in Dominio.objects.filter(ginasio_id=ginasio_id).values_list("hostname", flat=True)
        ]
    return tags


def _post(tags: list[str]) -> None:
    try:
        requests.post(
            f"{settings.FRONTEND_INTERNAL_URL.rstrip('/')}/api/revalidate",
            json={"tags": tags},
            headers={"x-revalidate-secret": settings.REVALIDATE_SECRET},
            timeout=5,
        )
    except requests.RequestException as exc:  # o site volta a ler a API quando expirar a cache
        logger.warning("Falha ao revalidar %s: %s", tags, exc)


def revalidate(ginasio_id: int | None, *tipos: str) -> None:
    if not ginasio_id:
        return
    tags = tags_for(ginasio_id, *tipos)
    transaction.on_commit(lambda: threading.Thread(target=_post, args=(tags,), daemon=True).start())
