from django.urls import path

from . import views

urlpatterns = [
    # Painel da receção
    path("gestao/auth/login/", views.LoginView.as_view()),
    path("gestao/auth/eu/", views.EuView.as_view()),
    path("gestao/resumo/", views.ResumoView.as_view()),
    path("gestao/socios/", views.SociosView.as_view()),
    path("gestao/socios/<int:pk>/", views.SocioView.as_view()),
    path("gestao/socios/<int:pk>/assinatura/", views.AssinaturaView.as_view()),
    path("gestao/socios/<int:pk>/novo-codigo/", views.NovoCodigoView.as_view()),
    path("gestao/cobrancas/", views.CobrancasView.as_view()),
    path("gestao/cobrancas/<int:pk>/pagar/", views.PagarCobrancaView.as_view()),
    path("gestao/cobrancas/<int:pk>/anular/", views.AnularCobrancaView.as_view()),
    path("gestao/cobrancas/<int:pk>/lembrete/", views.LembreteView.as_view()),
    path("gestao/checkins/", views.CheckInView.as_view()),
    path("gestao/checkins/lote/", views.CheckInLoteView.as_view()),
    path("gestao/checkins/snapshot/", views.SnapshotView.as_view()),
    # App do sócio
    path("socio/auth/codigo/", views.PedirCodigoView.as_view()),
    path("socio/auth/entrar/", views.EntrarView.as_view()),
    path("socio/eu/", views.AppEuView.as_view()),
    path("socio/cobrancas/<uuid:uuid>/pagar/", views.AppPagarView.as_view()),
]
