"""Ao publicar (ou apagar) conteúdo, o site do ginásio é revalidado em segundos."""

from django.db.models.signals import post_delete
from django.dispatch import receiver
from wagtail.signals import page_published, page_unpublished, published, unpublished

from apps.core.revalidation import revalidate

from .models import Aula, HomePage, Modalidade, PaginaGenerica, Pergunta, Plano, Testemunho, Treinador

TIPOS = {
    Modalidade: "modalidades",
    Treinador: "treinadores",
    Plano: "planos",
    Aula: "aulas",
    Testemunho: "testemunhos",
    Pergunta: "faq",
}


def _revalidar_pagina(sender, instance, **kwargs):
    ginasio = instance.specific.ginasio() if hasattr(instance.specific, "ginasio") else None
    if ginasio:
        revalidate(ginasio.pk, "paginas", "site")


for modelo in (HomePage, PaginaGenerica):
    page_published.connect(_revalidar_pagina, sender=modelo)
    page_unpublished.connect(_revalidar_pagina, sender=modelo)


def _revalidar_snippet(sender, instance, **kwargs):
    # As páginas incluem blocos com dados dos snippets, por isso também são revalidadas.
    revalidate(instance.ginasio_id, TIPOS[type(instance)], "paginas")


for modelo in TIPOS:
    published.connect(_revalidar_snippet, sender=modelo)
    unpublished.connect(_revalidar_snippet, sender=modelo)
    post_delete.connect(_revalidar_snippet, sender=modelo)


@receiver(post_delete, sender=PaginaGenerica)
def _pagina_apagada(sender, instance, **kwargs):
    _revalidar_pagina(sender, instance)
