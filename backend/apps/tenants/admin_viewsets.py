from django.urls import reverse
from django.utils.html import format_html
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from .models import Dominio, Ginasio


class GinasioViewSet(ModelViewSet):
    model = Ginasio
    icon = "home"
    menu_label = "Ginásios"
    form_fields = ["nome", "slug", "nif", "estado", "plano_plataforma", "pais"]
    list_display = ["nome", "estado", "plano_plataforma", "dominio_principal", "criado_em"]
    list_filter = ["estado", "plano_plataforma"]
    search_fields = ["nome", "slug", "nif"]
    search_backend_name = None


class DominioViewSet(ModelViewSet):
    model = Dominio
    icon = "site"
    menu_label = "Domínios"
    form_fields = ["ginasio", "hostname", "principal"]
    list_display = ["hostname", "ginasio", "principal", "verificado", "acao_verificar"]
    list_filter = ["principal", "verificado"]
    search_fields = ["hostname"]
    search_backend_name = None


def acao_verificar(dominio):
    url = reverse("tenants_verificar_dominio", args=[dominio.pk])
    return format_html('<a class="button button-small button-secondary" href="{}">Verificar DNS</a>', url)


Dominio.acao_verificar = acao_verificar
Dominio.acao_verificar.short_description = "DNS"


class PlataformaGroup(ViewSetGroup):
    menu_label = "Plataforma"
    menu_icon = "cogs"
    menu_order = 900
    items = (GinasioViewSet("tenants_ginasio"), DominioViewSet("tenants_dominio"))
