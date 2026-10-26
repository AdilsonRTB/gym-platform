from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from .models import Adesao, Fatura, Pagamento
from .services import emitir_fatura


class AdesaoViewSet(ModelViewSet):
    model = Adesao
    icon = "user"
    menu_label = "Adesões"
    form_fields = ["estado", "nome", "email", "telefone", "nif", "morada"]
    list_display = ["nome", "plano", "valor_cve", "estado", "criado_em"]
    list_filter = ["estado"]
    list_export = ["nome", "email", "telefone", "nif", "plano", "valor_cve", "estado", "criado_em", "paga_em"]
    export_filename = "adesoes"
    search_fields = ["nome", "email", "telefone"]
    search_backend_name = None
    add_to_admin_menu = False
    inspect_view_enabled = True


class PagamentoViewSet(ModelViewSet):
    model = Pagamento
    icon = "credit-card"
    menu_label = "Pagamentos"
    form_fields = [
        "metodo",
        "valor_cve",
        "descricao",
        "nome_cliente",
        "nif_cliente",
        "email_cliente",
        "adesao",
    ]
    list_display = ["nome_cliente", "descricao", "valor_cve", "metodo", "estado", "criado_em"]
    list_filter = ["metodo", "estado"]
    list_export = ["nome_cliente", "nif_cliente", "descricao", "valor_cve", "metodo", "estado", "criado_em"]
    export_filename = "pagamentos"
    search_fields = ["nome_cliente", "referencia"]
    search_backend_name = None
    inspect_view_enabled = True


def acao_fatura(fatura):
    if fatura.estado == Fatura.Estado.EMITIDA:
        return fatura.iud or "—"
    url = reverse("billing_reemitir_fatura", args=[fatura.pk])
    return format_html('<a class="button button-small" href="{}">Emitir de novo</a>', url)


Fatura.acao = acao_fatura
Fatura.acao.short_description = "IUD / ação"


class FaturaViewSet(ModelViewSet):
    model = Fatura
    icon = "doc-full-inverse"
    menu_label = "Faturas"
    form_fields = []
    list_display = ["numero", "nome_cliente", "valor_cve", "estado", "criada_em", "acao"]
    list_filter = ["estado"]
    list_export = ["numero", "nome_cliente", "nif_cliente", "valor_cve", "estado", "iud", "emitida_em"]
    export_filename = "faturas"
    search_fields = ["nome_cliente", "iud"]
    search_backend_name = None
    inspect_view_enabled = True
    inspect_view_fields = [
        "serie",
        "ano",
        "sequencia",
        "estado",
        "iud",
        "nome_cliente",
        "nif_cliente",
        "valor_cve",
        "emitida_em",
        "erro",
        "xml",
    ]


class FaturacaoGroup(ViewSetGroup):
    menu_label = "Adesões e pagamentos"
    menu_icon = "credit-card"
    menu_order = 400
    items = (
        AdesaoViewSet("billing_adesao"),
        PagamentoViewSet("billing_pagamento"),
        FaturaViewSet("billing_fatura"),
    )


@hooks.register("register_admin_viewset")
def registar():
    return FaturacaoGroup()


def reemitir(request, pk):
    if not request.user.has_perm("billing.add_pagamento"):
        raise PermissionDenied
    fatura = get_object_or_404(Fatura, pk=pk)
    if request.method != "POST":
        return render(request, "billing/reemitir.html", {"fatura": fatura})
    fatura = emitir_fatura(fatura.pagamento)
    if fatura and fatura.estado == Fatura.Estado.EMITIDA:
        messages.success(request, f"Fatura {fatura.numero} emitida.")
    else:
        messages.error(
            request, f"Não foi possível emitir a fatura: {fatura.erro if fatura else 'sem fornecedor'}"
        )
    return redirect("billing_fatura:index")


@hooks.register("register_admin_urls")
def urls():
    return [path("faturas/<int:pk>/reemitir/", reemitir, name="billing_reemitir_fatura")]
