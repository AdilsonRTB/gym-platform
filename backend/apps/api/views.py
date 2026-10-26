from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page
from wagtail.rich_text import expand_db_html

from apps.billing.models import Adesao
from apps.billing.services import PagamentoIndisponivel, iniciar_adesao
from apps.branding.models import PrivacidadeSettings
from apps.content.models import Aula, Modalidade, Pergunta, Plano, Testemunho, Treinador
from apps.content.preview import ler_preview
from apps.leads.notifications import notificar_novo_lead
from apps.tenants.models import normalizar_host
from apps.tenants.resolver import resolver_ginasio

from . import serializers as s


def _paginas_publicas(ginasio):
    raiz = ginasio.site.root_page
    return Page.objects.live().public().descendant_of(raiz, inclusive=True).specific()


class SiteView(APIView):
    def get(self, request):
        return Response(s.serializar_site(request.ginasio, request))


class PaginaView(APIView):
    def get(self, request):
        caminho = "/" + request.query_params.get("caminho", "/").strip("/")
        raiz = request.ginasio.site.root_page
        url_path = raiz.url_path + (caminho.strip("/") + "/" if caminho != "/" else "")
        pagina = _paginas_publicas(request.ginasio).filter(url_path=url_path).first()
        if pagina is None:
            raise Http404
        return Response(s.serializar_pagina(pagina))


class PaginasListaView(APIView):
    """Todas as páginas publicadas, para o sitemap."""

    def get(self, request):
        return Response(
            [
                {
                    "caminho": p.caminho_site(),
                    "publicada_em": p.last_published_at.isoformat() if p.last_published_at else None,
                    "indexar": getattr(p, "indexar", True),
                }
                for p in _paginas_publicas(request.ginasio)
            ]
        )


class RedirecionamentoView(APIView):
    def get(self, request):
        caminho = Redirect.normalise_path(request.query_params.get("caminho", ""))
        redirect = Redirect.get_for_site(request.ginasio.site).filter(old_path=caminho).first()
        if redirect is None:
            raise Http404
        return Response({"destino": redirect.link, "permanente": redirect.is_permanent})


class PublicadosMixin:
    modelo = None

    def get_queryset(self):
        return self.modelo.objects.filter(live=True)


class ModalidadesView(PublicadosMixin, generics.ListAPIView):
    modelo = Modalidade
    serializer_class = s.ModalidadeResumoSerializer
    pagination_class = None


class ModalidadeView(PublicadosMixin, generics.RetrieveAPIView):
    modelo = Modalidade
    serializer_class = s.ModalidadeSerializer
    lookup_field = "slug"


class TreinadoresView(PublicadosMixin, generics.ListAPIView):
    modelo = Treinador
    serializer_class = s.TreinadorSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related("modalidades")


class PlanosView(PublicadosMixin, generics.ListAPIView):
    modelo = Plano
    serializer_class = s.PlanoSerializer


class AulasView(PublicadosMixin, generics.ListAPIView):
    modelo = Aula
    serializer_class = s.AulaSerializer

    def get_queryset(self):
        return super().get_queryset().filter(modalidade__live=True).select_related("modalidade", "treinador")


class TestemunhosView(PublicadosMixin, generics.ListAPIView):
    modelo = Testemunho
    serializer_class = s.TestemunhoSerializer


class PerguntasView(PublicadosMixin, generics.ListAPIView):
    modelo = Pergunta
    serializer_class = s.PerguntaSerializer


class PrivacidadeView(APIView):
    def get(self, request):
        p = PrivacidadeSettings.for_site(request.ginasio.site)
        return Response(
            {
                "responsavel": p.responsavel or request.ginasio.nome,
                "email": p.email_privacidade,
                "politica": expand_db_html(p.politica or ""),
                "atualizada_em": p.atualizada_em.isoformat() if p.atualizada_em else None,
                "texto_consentimento": p.texto_consentimento,
            }
        )


class PorVisitanteThrottle(ScopedRateThrottle):
    """Os pedidos chegam do servidor Next.js; o limite conta por visitante (IP reencaminhado)."""

    def get_ident(self, request):
        return request.headers.get("X-Visitor-Ip") or super().get_ident(request)


class FormularioView(APIView):
    throttle_classes = [PorVisitanteThrottle]
    throttle_scope = "formularios"


class LeadView(FormularioView):
    def post(self, request):
        serializer = s.LeadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("website"):  # bot
            return Response({"ok": True}, status=status.HTTP_201_CREATED)
        lead = serializer.save()
        notificar_novo_lead(lead)
        return Response({"ok": True}, status=status.HTTP_201_CREATED)


class PedidoDadosView(FormularioView):
    def post(self, request):
        serializer = s.PedidoDadosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"ok": True}, status=status.HTTP_201_CREATED)


class AdesaoView(FormularioView):
    def post(self, request):
        serializer = s.AdesaoSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        dados = dict(serializer.validated_data)
        plano = dados.pop("plano")
        dados.pop("consentimento")
        try:
            adesao, inicio = iniciar_adesao(request.ginasio, plano, dados, serializer.dados_consentimento())
        except PagamentoIndisponivel as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "ref": str(adesao.uuid),
                "pagamento": {"tipo": inicio.tipo, "url": inicio.url, "campos": inicio.campos},
            },
            status=status.HTTP_201_CREATED,
        )


class AdesaoEstadoView(APIView):
    def get(self, request, uuid):
        adesao = get_object_or_404(Adesao.objects.select_related("plano"), uuid=uuid)
        fatura = None
        pagamento = adesao.pagamentos.filter(estado="pago").select_related("fatura").first()
        if pagamento and hasattr(pagamento, "fatura"):
            fatura = {"numero": pagamento.fatura.numero, "estado": pagamento.fatura.estado}
        return Response(
            {
                "estado": adesao.estado,
                "plano": adesao.plano.nome,
                "valor_cve": adesao.valor_cve,
                "nome": adesao.nome.split(" ")[0],
                "fatura": fatura,
            }
        )


class PreviewView(APIView):
    def get(self, request, token):
        dados = ler_preview(token)
        if not dados or dados["ginasio_id"] != request.ginasio.pk:
            raise Http404
        return Response(dados["pagina"])


# --------------------------------------------------------------------------- Endpoints internos


def dominio_valido(request):
    """Chamado pelo Caddy (TLS on-demand) antes de emitir um certificado."""
    ginasio = resolver_ginasio(request.GET.get("domain", ""))
    if ginasio is None or not ginasio.publico:
        return JsonResponse({"ok": False}, status=404)
    return JsonResponse({"ok": True, "ginasio": ginasio.slug})


def health(request):
    return JsonResponse({"ok": True})


def resolver(request):
    """Usado pelo Next.js para saber se um domínio pertence a um ginásio (sem expor dados)."""
    host = normalizar_host(request.GET.get("host", ""))
    ginasio = resolver_ginasio(host)
    if ginasio is None or not ginasio.publico:
        return JsonResponse({"ok": False}, status=404)
    return JsonResponse({"ok": True, "id": ginasio.pk})
