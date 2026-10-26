"""Perfis por ginásio → permissões.

As permissões de modelo do Django são globais; o isolamento entre ginásios vem do filtro de tenant
(managers) e das permissões de página/coleção do Wagtail, que são dadas só sobre a árvore e a coleção
de cada ginásio.
"""

from fnmatch import fnmatch

from django.contrib.auth.models import Group, Permission

from .models import Ginasio, Papel

PERMISSOES_MODELO: dict[str, list[str]] = {
    Papel.DONO: [
        "wagtailadmin.access_admin",
        "content.*",
        "leads.*",
        "billing.*",
        "branding.*",
        "gestao.*",
        "wagtailredirects.*",
        "tenants.gerir_equipa",
    ],
    Papel.GESTOR: [
        "wagtailadmin.access_admin",
        "content.*",
        "leads.*",
        "branding.*",
        "gestao.*",
        "wagtailredirects.*",
        "billing.view_adesao",
        "billing.view_pagamento",
        "billing.add_pagamento",
        "billing.view_fatura",
    ],
    Papel.RECECIONISTA: [
        "wagtailadmin.access_admin",
        "leads.view_lead",
        "leads.change_lead",
        "content.*_aula",
        "content.view_*",
        "gestao.view_*",
        "gestao.add_socio",
        "gestao.change_socio",
        "gestao.add_checkin",
        "billing.view_adesao",
        "billing.view_pagamento",
        "billing.add_pagamento",
        "billing.view_fatura",
    ],
    Papel.TREINADOR: [
        "wagtailadmin.access_admin",
        "content.change_treinador",
        "content.view_treinador",
        "content.view_modalidade",
        "content.add_aula",
        "content.change_aula",
        "content.view_aula",
        "gestao.add_checkin",
    ],
}

PERMISSOES_PAGINA = {
    Papel.DONO: ["add_page", "change_page", "publish_page", "bulk_delete_page", "lock_page", "unlock_page"],
    Papel.GESTOR: ["add_page", "change_page", "publish_page", "lock_page", "unlock_page"],
}

PERMISSOES_COLECAO = {
    Papel.DONO: ["wagtailimages.*_image", "wagtaildocs.*_document"],
    Papel.GESTOR: ["wagtailimages.*_image", "wagtaildocs.*_document"],
    Papel.RECECIONISTA: ["wagtailimages.choose_image"],
    Papel.TREINADOR: ["wagtailimages.add_image", "wagtailimages.choose_image"],
}

# Estas permissões não fazem sentido como permissões globais de modelo.
EXCLUIR_GLOBAIS = {"billing.change_configuracaopagamentos", "billing.change_configuracaofiscal"}


def _todas_permissoes() -> list[tuple[str, Permission]]:
    return [
        (f"{p.content_type.app_label}.{p.codename}", p)
        for p in Permission.objects.select_related("content_type").all()
    ]


def _filtrar(padroes: list[str], todas, excluir=frozenset()) -> list[Permission]:
    return [perm for nome, perm in todas if nome not in excluir and any(fnmatch(nome, p) for p in padroes)]


def nome_grupo(ginasio: Ginasio, papel: str) -> str:
    return f"{ginasio.slug} · {Papel(papel).label}"


def grupo_do_papel(ginasio: Ginasio, papel: str) -> Group:
    group, _ = Group.objects.get_or_create(name=nome_grupo(ginasio, papel))
    return group


def sincronizar_grupos(ginasio: Ginasio) -> None:
    """Cria/atualiza os quatro grupos do ginásio. Idempotente."""
    from wagtail.models import GroupCollectionPermission, GroupPagePermission

    todas = _todas_permissoes()
    excluir_gestor = EXCLUIR_GLOBAIS
    raiz = ginasio.site.root_page if ginasio.site else None

    for papel in Papel:
        group = grupo_do_papel(ginasio, papel)
        excluir = frozenset() if papel == Papel.DONO else excluir_gestor
        group.permissions.set(_filtrar(PERMISSOES_MODELO[papel], todas, excluir))

        GroupPagePermission.objects.filter(group=group).delete()
        if raiz is not None:
            for codename in PERMISSOES_PAGINA.get(papel, []):
                perm = Permission.objects.get(content_type__app_label="wagtailcore", codename=codename)
                GroupPagePermission.objects.create(group=group, page=raiz, permission=perm)

        GroupCollectionPermission.objects.filter(group=group).delete()
        if ginasio.colecao is not None:
            for perm in _filtrar(PERMISSOES_COLECAO.get(papel, []), todas):
                GroupCollectionPermission.objects.create(
                    group=group, collection=ginasio.colecao, permission=perm
                )
