from django.urls import include, path

from . import views

app_name = "api"

urlpatterns = [
    path("site/", views.SiteView.as_view()),
    path("paginas/", views.PaginaView.as_view()),
    path("paginas/lista/", views.PaginasListaView.as_view()),
    path("redirecionamento/", views.RedirecionamentoView.as_view()),
    path("modalidades/", views.ModalidadesView.as_view()),
    path("modalidades/<slug:slug>/", views.ModalidadeView.as_view()),
    path("treinadores/", views.TreinadoresView.as_view()),
    path("planos/", views.PlanosView.as_view()),
    path("aulas/", views.AulasView.as_view()),
    path("testemunhos/", views.TestemunhosView.as_view()),
    path("perguntas/", views.PerguntasView.as_view()),
    path("privacidade/", views.PrivacidadeView.as_view()),
    path("leads/", views.LeadView.as_view()),
    path("pedidos-dados/", views.PedidoDadosView.as_view()),
    path("adesoes/", views.AdesaoView.as_view()),
    path("adesoes/<uuid:uuid>/", views.AdesaoEstadoView.as_view()),
    path("preview/<str:token>/", views.PreviewView.as_view()),
    path("", include("apps.gestao.urls")),
]
