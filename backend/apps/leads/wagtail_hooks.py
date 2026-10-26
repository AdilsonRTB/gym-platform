import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from wagtail import hooks
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.log_actions import log

from .models import Lead, PedidoDados
from .services import concluir_pedido


class LeadViewSet(ModelViewSet):
    model = Lead
    icon = "mail"
    menu_label = "Leads"
    form_fields = [
        "estado",
        "tipo",
        "nome",
        "email",
        "telefone",
        "modalidade",
        "data_preferida",
        "mensagem",
        "notas",
    ]
    list_display = ["nome", "tipo", "estado", "telefone", "email", "criado_em"]
    list_filter = ["tipo", "estado"]
    list_export = ["nome", "tipo", "estado", "email", "telefone", "mensagem", "criado_em", "consentimento_em"]
    export_filename = "leads"
    search_fields = ["nome", "email", "telefone"]
    search_backend_name = None
    inspect_view_enabled = True
    inspect_view_fields = [
        "tipo",
        "estado",
        "nome",
        "email",
        "telefone",
        "modalidade",
        "data_preferida",
        "mensagem",
        "origem",
        "consentimento",
        "consentimento_texto",
        "consentimento_em",
        "criado_em",
    ]


def acao_pedido(pedido):
    if pedido.estado != PedidoDados.Estado.PENDENTE:
        return "—"
    url = reverse("leads_concluir_pedido", args=[pedido.pk])
    return format_html('<a class="button button-small" href="{}">Tratar</a>', url)


PedidoDados.acao = acao_pedido
PedidoDados.acao.short_description = "Ação"


class PedidoDadosViewSet(ModelViewSet):
    model = PedidoDados
    icon = "lock"
    menu_label = "Pedidos de dados"
    form_fields = ["tipo", "nome", "email", "telefone", "notas"]
    list_display = ["email", "tipo", "estado", "pedido_em", "acao"]
    list_filter = ["tipo", "estado"]
    search_fields = ["email", "nome"]
    search_backend_name = None


class LeadsGroup(ViewSetGroup):
    menu_label = "Leads"
    menu_icon = "mail"
    menu_order = 300
    items = (LeadViewSet("leads_lead"), PedidoDadosViewSet("leads_pedidodados"))


@hooks.register("register_admin_viewset")
def registar():
    return LeadsGroup()


def concluir(request, pk):
    if not request.user.has_perm("leads.change_pedidodados"):
        raise PermissionDenied
    pedido = get_object_or_404(PedidoDados, pk=pk, estado=PedidoDados.Estado.PENDENTE)
    if request.method == "POST":
        resultado = concluir_pedido(pedido)
        if pedido.tipo == PedidoDados.Tipo.EXPORTACAO:
            log(instance=pedido, action="plataforma.exportar_dados", user=request.user)
            resposta = HttpResponse(
                json.dumps(resultado, ensure_ascii=False, indent=2), content_type="application/json"
            )
            resposta["Content-Disposition"] = f'attachment; filename="dados-{pedido.uuid}.json"'
            return resposta
        log(instance=pedido, action="plataforma.eliminar_dados", user=request.user)
        messages.success(
            request, f"Dados anonimizados: {resultado['leads']} leads e {resultado['adesoes']} adesões."
        )
        return redirect("leads_pedidodados:index")
    return render(request, "leads/concluir.html", {"pedido": pedido})


@hooks.register("register_admin_urls")
def urls():
    return [path("privacidade/pedidos/<int:pk>/tratar/", concluir, name="leads_concluir_pedido")]
