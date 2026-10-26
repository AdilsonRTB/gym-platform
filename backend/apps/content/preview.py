"""Pré-visualização headless: o Wagtail guarda a página em rascunho e o Next.js mostra-a por token.

Não depende de cookies (funciona dentro do iframe de pré-visualização do Wagtail).
"""

import secrets

from django.core.cache import cache

from apps.tenants.context import using_ginasio

TTL = 60 * 60


def guardar_preview(pagina, ginasio) -> str:
    from apps.api.serializers import serializar_pagina

    token = secrets.token_urlsafe(24)
    with using_ginasio(ginasio):
        dados = serializar_pagina(pagina)
    cache.set(f"preview:{token}", {"ginasio_id": ginasio.pk if ginasio else None, "pagina": dados}, TTL)
    return token


def ler_preview(token: str) -> dict | None:
    return cache.get(f"preview:{token}")
