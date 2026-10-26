from wagtail import hooks
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from apps.tenants.models import Papel
from apps.tenants.utils import papel_atual

from .models import Aula, Modalidade, Pergunta, Plano, Testemunho, Treinador


class ConteudoViewSet(SnippetViewSet):
    search_backend_name = None  # pesquisa via ORM, já filtrada pelo ginásio

    def get_queryset(self, request):
        return self.model.objects.all()


class ModalidadeViewSet(ConteudoViewSet):
    model = Modalidade
    icon = "list-ul"
    menu_label = "Modalidades"
    list_display = ["nome", "nivel", "duracao_min", "ordem", UpdatedAtColumn()]
    search_fields = ["nome"]


class TreinadorViewSet(ConteudoViewSet):
    model = Treinador
    icon = "user"
    menu_label = "Treinadores"
    list_display = ["nome", "cargo", "ordem", UpdatedAtColumn()]
    search_fields = ["nome"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if papel_atual(request) == Papel.TREINADOR:
            return qs.filter(user=request.user)
        return qs


class PlanoViewSet(ConteudoViewSet):
    model = Plano
    icon = "tag"
    menu_label = "Planos"
    list_display = ["nome", "preco_cve", "periodicidade", "destaque", "ordem", UpdatedAtColumn()]
    search_fields = ["nome"]


class AulaViewSet(ConteudoViewSet):
    model = Aula
    icon = "time"
    menu_label = "Horário"
    list_display = ["modalidade", "dia_semana", "hora_inicio", "hora_fim", "treinador", "sala"]
    list_filter = ["dia_semana"]
    list_per_page = 100

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("modalidade", "treinador")
        if papel_atual(request) == Papel.TREINADOR:
            return qs.filter(treinador__user=request.user)
        return qs


class TestemunhoViewSet(ConteudoViewSet):
    model = Testemunho
    icon = "openquote"
    menu_label = "Testemunhos"
    list_display = ["autor", "detalhe", "ordem", UpdatedAtColumn()]
    search_fields = ["autor", "texto"]


class PerguntaViewSet(ConteudoViewSet):
    model = Pergunta
    icon = "help"
    menu_label = "Perguntas frequentes"
    list_display = ["pergunta", "ordem", UpdatedAtColumn()]
    search_fields = ["pergunta"]


class ConteudoGroup(SnippetViewSetGroup):
    menu_label = "Conteúdo"
    menu_icon = "folder-open-inverse"
    menu_order = 200
    items = (
        ModalidadeViewSet,
        AulaViewSet,
        PlanoViewSet,
        TreinadorViewSet,
        TestemunhoViewSet,
        PerguntaViewSet,
    )


register_snippet(ConteudoGroup)


@hooks.register("construct_main_menu")
def esconder_itens(request, menu_items):
    """Snippets genéricos e relatórios globais não fazem sentido para a equipa dos ginásios."""
    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name not in {"snippets", "reports"}]
