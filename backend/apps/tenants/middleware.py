import re

from django.http import JsonResponse
from django.shortcuts import redirect

from .context import reset, set_current
from .models import Ginasio
from .resolver import resolver_ginasio

SESSION_KEY = "ginasio_id"
SETTINGS_URL = re.compile(r"^/admin/settings/(?P<app>\w+)/(?P<model>\w+)/(?:(?P<site>\d+)/)?$")


def ginasios_do_utilizador(user):
    if user.is_superuser:
        return Ginasio.objects.all()
    return Ginasio.objects.filter(membros__user=user).distinct()


def ginasio_admin(request) -> Ginasio | None:
    ginasios = ginasios_do_utilizador(request.user).select_related("site")
    ginasio_id = request.session.get(SESSION_KEY)
    ginasio = ginasios.filter(pk=ginasio_id).first() if ginasio_id else None
    if ginasio is None:
        ginasio = ginasios.order_by("nome").first()
        if ginasio:
            request.session[SESSION_KEY] = ginasio.pk
    return ginasio


class TenantMiddleware:
    """Define o ginásio atual de cada pedido.

    - API pública (`/api/v1/`): pelo domínio do visitante, enviado pelo Next.js em `X-Gym-Host`.
    - Admin (`/admin/`): pelo ginásio selecionado na sessão, entre os ginásios do utilizador.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ginasio = None
        token = None
        path = request.path

        if path.startswith("/api/v1/"):
            host = request.headers.get("X-Gym-Host") or request.get_host()
            ginasio = resolver_ginasio(host)
            if ginasio is None or not ginasio.publico:
                return JsonResponse({"detail": "Ginásio não encontrado."}, status=404)
            request.ginasio = ginasio
            token = set_current(ginasio)

        elif path.startswith("/admin/") and request.user.is_authenticated:
            ginasio = ginasio_admin(request)
            request.ginasio = ginasio
            token = set_current(ginasio)
            resposta = self._proteger_configuracoes(request, ginasio)
            if resposta is not None:
                reset(token)
                return resposta

        try:
            return self.get_response(request)
        finally:
            if token is not None:
                reset(token)

    @staticmethod
    def _proteger_configuracoes(request, ginasio):
        """As configurações por site do Wagtail só podem ser editadas para o ginásio atual."""
        match = SETTINGS_URL.match(request.path)
        if not match or ginasio is None or ginasio.site_id is None:
            return None
        site_pk = match.group("site")
        if site_pk is None or int(site_pk) != ginasio.site_id:
            return redirect(f"/admin/settings/{match.group('app')}/{match.group('model')}/{ginasio.site_id}/")
        return None
