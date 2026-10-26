from wagtail import hooks
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.admin.viewsets.model import ModelViewSet

from .models import CheckIn, Cobranca, Lembrete, Socio


class SocioViewSet(ModelViewSet):
    model = Socio
    icon = "user"
    menu_label = "Sócios"
    list_display = ["numero", "nome", "telefone", "email", "estado", "criado_em"]
    list_filter = ["estado"]
    list_export = ["numero", "nome", "email", "telefone", "nif", "estado", "criado_em"]
    export_filename = "socios"
    search_fields = ["nome", "email", "telefone"]
    search_backend_name = None
    inspect_view_enabled = True


class CobrancaViewSet(ModelViewSet):
    model = Cobranca
    icon = "tag"
    menu_label = "Cobranças"
    form_fields = ["estado"]
    add_to_admin_menu = False
    list_display = ["socio", "descricao", "valor_cve", "vencimento", "estado"]
    list_filter = ["estado"]
    list_export = ["socio", "descricao", "valor_cve", "vencimento", "estado", "paga_em"]
    export_filename = "cobrancas"
    search_backend_name = None
    inspect_view_enabled = True


class CheckInViewSet(ModelViewSet):
    model = CheckIn
    icon = "tick-inverse"
    menu_label = "Check-ins"
    form_fields = []
    list_display = ["socio", "momento", "permitido", "motivo", "offline"]
    list_filter = ["permitido", "offline", "origem"]
    list_export = ["socio", "momento", "permitido", "motivo", "origem", "offline"]
    export_filename = "checkins"
    search_backend_name = None
    inspect_view_enabled = True


class LembreteViewSet(ModelViewSet):
    model = Lembrete
    icon = "mail"
    menu_label = "Lembretes"
    form_fields = []
    list_display = ["socio", "tipo", "canais", "enviado_em"]
    list_filter = ["tipo"]
    search_backend_name = None
    inspect_view_enabled = True


class GestaoGroup(ViewSetGroup):
    menu_label = "Sócios"
    menu_icon = "group"
    menu_order = 250
    items = (
        SocioViewSet("gestao_socio"),
        CobrancaViewSet("gestao_cobranca"),
        CheckInViewSet("gestao_checkin"),
        LembreteViewSet("gestao_lembrete"),
    )


@hooks.register("register_admin_viewset")
def registar():
    return GestaoGroup()
