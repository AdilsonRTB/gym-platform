from django.urls import path, reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.ui.components import Component

from . import views
from .admin_viewsets import PlataformaGroup


@hooks.register("register_admin_viewset")
def registar_plataforma():
    return PlataformaGroup()


@hooks.register("register_admin_urls")
def urls():
    return [
        path("ginasio/", views.trocar_ginasio, name="tenants_trocar"),
        path("equipa/", views.equipa, name="tenants_equipa"),
        path("equipa/<int:pk>/remover/", views.remover_membro, name="tenants_remover_membro"),
        path("dominios/<int:pk>/verificar/", views.verificar_dominio, name="tenants_verificar_dominio"),
    ]


class GinasioMenuItem(MenuItem):
    """Mostra no menu o nome do ginásio atual."""

    def render_component(self, request):
        component = super().render_component(request)
        ginasio = getattr(request, "ginasio", None)
        if ginasio:
            component.label = ginasio.nome
        return component


@hooks.register("register_admin_menu_item")
def menu_ginasio():
    return GinasioMenuItem("Ginásio", reverse("tenants_trocar"), icon_name="home", order=1)


class EquipaMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.is_superuser or request.user.has_perm("tenants.gerir_equipa")


@hooks.register("register_admin_menu_item")
def menu_equipa():
    return EquipaMenuItem("Equipa", reverse("tenants_equipa"), icon_name="group", order=850)


@hooks.register("register_log_actions")
def acoes_auditoria(actions):
    actions.register_action("plataforma.trocar_ginasio", "Trocar de ginásio", "Trocou para este ginásio")
    actions.register_action("plataforma.exportar_dados", "Exportar dados (CNPD)", "Exportou dados pessoais")
    actions.register_action("plataforma.eliminar_dados", "Eliminar dados (CNPD)", "Eliminou dados pessoais")


class PainelGinasio(Component):
    order = 50
    template_name = "tenants/painel.html"

    def __init__(self, request):
        self.request = request

    def get_context_data(self, parent_context):
        from datetime import timedelta

        from django.utils import timezone

        from apps.billing.models import Adesao
        from apps.content.models import Aula
        from apps.leads.models import Lead

        ginasio = self.request.ginasio
        if ginasio is None:
            return {"ginasio": None}
        desde = timezone.now() - timedelta(days=30)
        hoje = timezone.localdate().weekday()
        return {
            "ginasio": ginasio,
            "url_site": ginasio.url_publico("/"),
            "leads_novos": Lead.objects.filter(estado=Lead.Estado.NOVO).count(),
            "adesoes_30d": Adesao.objects.filter(estado=Adesao.Estado.PAGA, paga_em__gte=desde).count(),
            "aulas_hoje": Aula.objects.filter(live=True, dia_semana=hoje).count(),
            "estado": ginasio.get_estado_display(),
        }


@hooks.register("construct_homepage_panels")
def painel(request, panels):
    panels.insert(0, PainelGinasio(request))


@hooks.register("insert_global_admin_css")
def css():
    return mark_safe('<link rel="stylesheet" href="/static/admin/plataforma.css">')
