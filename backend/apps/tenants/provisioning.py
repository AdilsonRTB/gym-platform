"""Criação de um ginásio novo: árvore de páginas, Site do Wagtail, domínio, coleção de media e grupos."""

from django.conf import settings
from django.db import transaction
from wagtail.models import Collection, Page, Site

from .models import Dominio, Ginasio
from .permissions import sincronizar_grupos


@transaction.atomic
def provisionar_ginasio(ginasio: Ginasio, dominio_proprio: str | None = None) -> Ginasio:
    from apps.content.models import HomePage

    subdominio = f"{ginasio.slug}.{settings.PLATFORM_DOMAIN}"
    hostname_principal = dominio_proprio or subdominio

    if ginasio.site is None:
        raiz = Page.get_first_root_node()
        home = HomePage(title=ginasio.nome, slug=ginasio.slug, corpo=[])
        raiz.add_child(instance=home)
        home.save_revision().publish()
        ginasio.site = Site.objects.create(
            hostname=hostname_principal,
            port=80,
            root_page=home,
            site_name=ginasio.nome,
            is_default_site=False,
        )

    if ginasio.colecao is None:
        ginasio.colecao = Collection.get_first_root_node().add_child(name=ginasio.nome)

    ginasio.save(update_fields=["site", "colecao"])

    Dominio.objects.get_or_create(
        hostname=subdominio,
        defaults={"ginasio": ginasio, "principal": dominio_proprio is None, "verificado": True},
    )
    if dominio_proprio:
        Dominio.objects.update_or_create(
            hostname=dominio_proprio, defaults={"ginasio": ginasio, "principal": True}
        )

    sincronizar_grupos(ginasio)
    return ginasio
