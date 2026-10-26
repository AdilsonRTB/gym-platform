from datetime import timedelta

from django.contrib.auth import authenticate
from django.db.models import Count, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.api.views import PorVisitanteThrottle
from apps.billing.models import Pagamento
from apps.billing.services import PagamentoIndisponivel
from apps.content.models import Plano

from . import services
from .auth import (
    DoPainel,
    EhSocio,
    EquipaAuth,
    PodeFazerCheckIn,
    SocioAuth,
    SoGestao,
    encontrar_socio,
    gerar_codigo,
    papel_de,
    token_equipa,
    token_socio,
    verificar_codigo,
)
from .models import Assinatura, CheckIn, Cobranca, Socio
from .serializers import (
    AssinaturaSerializer,
    CheckInEntradaSerializer,
    CheckInSerializer,
    CobrancaListaSerializer,
    CobrancaSerializer,
    NovoSocioSerializer,
    SocioResumoSerializer,
    SocioSerializer,
)


def _cobrancas_com_pagamentos(qs):
    return qs.prefetch_related(Prefetch("pagamentos", queryset=Pagamento.objects.select_related("fatura")))


class LoginThrottle(PorVisitanteThrottle):
    scope = "login"


class OtpThrottle(PorVisitanteThrottle):
    scope = "otp"


# =========================================================================== Equipa (painel da receção)


class Painel(APIView):
    authentication_classes = [EquipaAuth]
    permission_classes = [DoPainel]


class LoginView(APIView):
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        identificador = (request.data.get("email") or "").strip()
        senha = request.data.get("password") or ""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        conta = User.objects.filter(
            Q(email__iexact=identificador) | Q(username__iexact=identificador)
        ).first()
        user = authenticate(request, username=conta.username, password=senha) if conta else None
        papel = papel_de(user, request.ginasio) if user else None
        if papel is None:
            return Response(
                {"detail": "Email ou palavra-passe incorretos."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                "token": token_equipa(user, request.ginasio),
                "utilizador": {"nome": user.get_full_name() or user.username, "papel": papel},
            }
        )


class EuView(APIView):
    authentication_classes = [EquipaAuth]
    permission_classes = [PodeFazerCheckIn]

    def get(self, request):
        return Response(
            {"nome": request.user.get_full_name() or request.user.username, "papel": request.papel}
        )


class ResumoView(Painel):
    def get(self, request):
        hoje = timezone.localdate()
        inicio_mes = hoje.replace(day=1)
        ativos = Socio.objects.filter(
            estado=Socio.Estado.ATIVO,
            assinaturas__estado=Assinatura.Estado.ATIVA,
            assinaturas__data_fim__gte=hoje,
        ).distinct()
        atraso = Cobranca.objects.filter(estado=Cobranca.Estado.PENDENTE, vencimento__lt=hoje)
        checkins_hoje = CheckIn.objects.filter(momento__date=hoje)
        receita = Cobranca.objects.filter(estado=Cobranca.Estado.PAGA, paga_em__date__gte=inicio_mes)
        a_vencer = Cobranca.objects.filter(
            estado=Cobranca.Estado.PENDENTE, vencimento__gte=hoje, vencimento__lte=hoje + timedelta(days=7)
        ).select_related("socio")
        por_hora = checkins_hoje.filter(permitido=True).values_list("momento", flat=True)
        horas = [0] * 24
        for m in por_hora:
            horas[timezone.localtime(m).hour] += 1
        return Response(
            {
                "socios_ativos": ativos.count(),
                "socios_total": Socio.objects.exclude(estado=Socio.Estado.INATIVO).count(),
                "checkins_hoje": checkins_hoje.filter(permitido=True).count(),
                "checkins_negados_hoje": checkins_hoje.filter(permitido=False).count(),
                "em_atraso": atraso.aggregate(n=Count("id"), total=Sum("valor_cve")),
                "receita_mes": receita.aggregate(total=Sum("valor_cve"))["total"] or 0,
                "checkins_por_hora": horas,
                "ultimos_checkins": CheckInSerializer(
                    CheckIn.objects.select_related("socio").order_by("-momento")[:8], many=True
                ).data,
                "a_vencer": CobrancaListaSerializer(
                    _cobrancas_com_pagamentos(a_vencer.order_by("vencimento")[:8]), many=True
                ).data,
            }
        )


class Paginacao(PageNumberPagination):
    page_size = 30


class SociosView(Painel, generics.ListCreateAPIView):
    pagination_class = Paginacao

    def get_serializer_class(self):
        return NovoSocioSerializer if self.request.method == "POST" else SocioResumoSerializer

    def get_queryset(self):
        qs = Socio.objects.prefetch_related(
            Prefetch("assinaturas", queryset=Assinatura.objects.select_related("plano")), "cobrancas"
        )
        q = self.request.query_params.get("q", "").strip()
        if q:
            filtro = Q(nome__icontains=q) | Q(email__icontains=q) | Q(telefone__icontains=q)
            if q.isdigit():
                filtro |= Q(numero=int(q)) | Q(telefone_digitos__endswith=q)
            qs = qs.filter(filtro)
        estado = self.request.query_params.get("estado")
        hoje = timezone.localdate()
        if estado == "atraso":
            qs = qs.filter(
                cobrancas__estado=Cobranca.Estado.PENDENTE, cobrancas__vencimento__lt=hoje
            ).distinct()
        elif estado in Socio.Estado.values:
            qs = qs.filter(estado=estado)
        return qs.order_by("-numero")

    def create(self, request, *args, **kwargs):
        serializer = NovoSocioSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        dados = dict(serializer.validated_data)
        plano = dados.pop("plano", None)
        dados.pop("consentimento")
        socio = Socio(
            **dados,
            consentimento=True,
            consentimento_texto=f"Consentimento recolhido na receção por {request.user.get_username()}.",
            consentimento_em=timezone.now(),
        )
        socio.save()
        cobranca = services.iniciar_assinatura(socio, plano) if plano else None
        return Response(
            {
                "socio": SocioSerializer(socio).data,
                "cobranca": CobrancaSerializer(cobranca).data if cobranca else None,
            },
            status=status.HTTP_201_CREATED,
        )


class SocioView(Painel, generics.RetrieveUpdateAPIView):
    serializer_class = SocioSerializer

    def get_queryset(self):
        return Socio.objects.prefetch_related("assinaturas__plano", "cobrancas")

    def retrieve(self, request, *args, **kwargs):
        socio = self.get_object()
        cobrancas = _cobrancas_com_pagamentos(socio.cobrancas.exclude(estado=Cobranca.Estado.ANULADA))[:24]
        return Response(
            {
                **SocioSerializer(socio).data,
                "cobrancas": CobrancaSerializer(cobrancas, many=True).data,
                "checkins": CheckInSerializer(socio.checkins.order_by("-momento")[:20], many=True).data,
                "historico_assinaturas": AssinaturaSerializer(
                    socio.assinaturas.select_related("plano"), many=True
                ).data,
            }
        )


class AssinaturaView(Painel):
    """Muda o plano do sócio: cancela a assinatura atual e cria a primeira cobrança do novo plano."""

    def post(self, request, pk):
        socio = get_object_or_404(Socio, pk=pk)
        plano = get_object_or_404(Plano.objects.filter(live=True), pk=request.data.get("plano"))
        cobranca = services.iniciar_assinatura(socio, plano, com_inscricao=not socio.assinaturas.exists())
        return Response(CobrancaSerializer(cobranca).data, status=status.HTTP_201_CREATED)


class NovoCodigoView(Painel):
    """Cartão perdido: gera um QR novo (o antigo deixa de entrar e as sessões da app terminam)."""

    def post(self, request, pk):
        import uuid

        socio = get_object_or_404(Socio, pk=pk)
        socio.codigo = uuid.uuid4()
        socio.save(update_fields=["codigo"])
        return Response({"codigo": str(socio.codigo)})


class CobrancasView(Painel, generics.ListAPIView):
    serializer_class = CobrancaListaSerializer
    pagination_class = Paginacao

    def get_queryset(self):
        hoje = timezone.localdate()
        qs = _cobrancas_com_pagamentos(Cobranca.objects.select_related("socio"))
        estado = self.request.query_params.get("estado", "atraso")
        if estado == "atraso":
            return qs.filter(estado=Cobranca.Estado.PENDENTE, vencimento__lt=hoje).order_by("vencimento")
        if estado == "pendente":
            return qs.filter(estado=Cobranca.Estado.PENDENTE, vencimento__gte=hoje).order_by("vencimento")
        if estado == "paga":
            return qs.filter(estado=Cobranca.Estado.PAGA).order_by("-paga_em")
        return qs.order_by("-vencimento")


class PagarCobrancaView(Painel):
    def post(self, request, pk):
        cobranca = get_object_or_404(Cobranca, pk=pk)
        try:
            services.pagar_na_rececao(cobranca, request.data.get("metodo", ""))
        except services.CobrancaInvalida as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        cobranca = _cobrancas_com_pagamentos(Cobranca.objects.filter(pk=pk)).get()
        return Response(CobrancaSerializer(cobranca).data)


class AnularCobrancaView(Painel):
    permission_classes = [SoGestao]

    def post(self, request, pk):
        cobranca = get_object_or_404(Cobranca, pk=pk, estado=Cobranca.Estado.PENDENTE)
        cobranca.estado = Cobranca.Estado.ANULADA
        cobranca.save(update_fields=["estado"])
        return Response(CobrancaSerializer(cobranca).data)


class LembreteView(Painel):
    def post(self, request, pk):
        cobranca = get_object_or_404(Cobranca, pk=pk, estado=Cobranca.Estado.PENDENTE)
        lembrete = services.lembrete_manual(cobranca)
        return Response({"canais": lembrete.canais.split(",")})


# --------------------------------------------------------------------------- Check-in


class CheckInBase(APIView):
    authentication_classes = [EquipaAuth]
    permission_classes = [PodeFazerCheckIn]

    def _registar(self, request, dados: dict) -> dict:
        resultado = services.registar_checkin(
            request.ginasio,
            codigo=dados.get("codigo") or None,
            socio_id=dados.get("socio_id"),
            momento=dados.get("momento"),
            client_id=dados.get("client_id"),
            origem=CheckIn.Origem.MANUAL if dados.get("socio_id") else CheckIn.Origem.QR,
            offline=dados.get("offline", False),
            dispositivo=dados.get("dispositivo", ""),
            user=request.user,
        )
        socio = resultado.checkin.socio if resultado.checkin else None
        assinatura = socio.assinatura_atual if socio else None
        return {
            "client_id": str(dados.get("client_id") or ""),
            "permitido": resultado.permitido,
            "motivo": resultado.motivo,
            "duplicado": resultado.duplicado,
            "socio": {
                "id": socio.pk,
                "numero": socio.numero,
                "nome": socio.nome,
                "plano": assinatura.plano.nome if assinatura else None,
                "valido_ate": assinatura.data_fim if assinatura else None,
            }
            if socio
            else None,
        }


class CheckInView(CheckInBase):
    def get(self, request):
        dia = request.query_params.get("data") or timezone.localdate().isoformat()
        qs = CheckIn.objects.filter(momento__date=dia).select_related("socio").order_by("-momento")
        return Response(CheckInSerializer(qs[:300], many=True).data)

    def post(self, request):
        entrada = CheckInEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        return Response(self._registar(request, entrada.validated_data), status=status.HTTP_201_CREATED)


class CheckInLoteView(CheckInBase):
    """Sincronização das entradas registadas sem rede (idempotente por client_id)."""

    def post(self, request):
        itens = request.data if isinstance(request.data, list) else request.data.get("itens", [])
        resultados = []
        for item in itens[:500]:
            entrada = CheckInEntradaSerializer(data={**item, "offline": True})
            if entrada.is_valid():
                resultados.append(self._registar(request, entrada.validated_data))
            else:
                resultados.append({"client_id": str(item.get("client_id", "")), "erro": entrada.errors})
        return Response({"resultados": resultados})


class SnapshotView(CheckInBase):
    """Lista mínima de sócios para validar entradas quando não há internet."""

    def get(self, request):
        from .services import config

        socios = Socio.objects.exclude(estado=Socio.Estado.INATIVO).prefetch_related(
            Prefetch(
                "assinaturas",
                queryset=Assinatura.objects.filter(estado=Assinatura.Estado.ATIVA).select_related("plano"),
                to_attr="ativas",
            )
        )
        dados = []
        for s in socios:
            a = max(s.ativas, key=lambda x: x.data_fim, default=None)
            dados.append(
                {
                    "c": str(s.codigo),
                    "id": s.pk,
                    "n": s.numero,
                    "nome": s.nome,
                    "e": s.estado,
                    "ate": a.data_fim.isoformat() if a else None,
                    "plano": a.plano.nome if a else None,
                }
            )
        return Response(
            {
                "gerado_em": timezone.now().isoformat(),
                "tolerancia": config(request.ginasio).tolerancia_dias,
                "socios": dados,
            }
        )


# =========================================================================== App do sócio


class PedirCodigoView(APIView):
    authentication_classes = []
    throttle_classes = [OtpThrottle]

    def post(self, request):
        socio = encontrar_socio(request.ginasio, request.data.get("contacto", ""))
        if socio:
            codigo = gerar_codigo(socio)
            mensagem = (
                f"{codigo} é o seu código de acesso à app do {request.ginasio.nome}. Válido 10 minutos."
            )
            canal = "email" if "@" in request.data.get("contacto", "") else "whatsapp"
            services.enviar(socio, mensagem, canal, f"Código de acesso · {request.ginasio.nome}")
        # A resposta é sempre igual, para não revelar quem é sócio.
        return Response({"ok": True})


class EntrarView(APIView):
    authentication_classes = []
    throttle_classes = [OtpThrottle]

    def post(self, request):
        socio = encontrar_socio(request.ginasio, request.data.get("contacto", ""))
        if socio is None or not verificar_codigo(socio, str(request.data.get("codigo", ""))):
            return Response({"detail": "Código inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"token": token_socio(socio)})


class AppView(APIView):
    authentication_classes = [SocioAuth]
    permission_classes = [EhSocio]


class AppEuView(AppView):
    def get(self, request):
        socio = request.socio
        assinatura = socio.assinatura_atual
        cobrancas = _cobrancas_com_pagamentos(socio.cobrancas.exclude(estado=Cobranca.Estado.ANULADA))
        return Response(
            {
                "socio": {
                    "numero": socio.numero,
                    "nome": socio.nome,
                    "email": socio.email,
                    "telefone": socio.telefone,
                    "codigo": str(socio.codigo),
                    "estado": socio.estado,
                    "desde": socio.criado_em.date(),
                },
                "assinatura": AssinaturaSerializer(assinatura).data if assinatura else None,
                "por_pagar": CobrancaSerializer(
                    cobrancas.filter(estado=Cobranca.Estado.PENDENTE), many=True
                ).data,
                "pagamentos": CobrancaSerializer(
                    cobrancas.filter(estado=Cobranca.Estado.PAGA)[:12], many=True
                ).data,
                "checkins": CheckInSerializer(
                    socio.checkins.filter(permitido=True).order_by("-momento")[:10], many=True
                ).data,
                "checkins_mes": socio.checkins.filter(
                    permitido=True, momento__date__gte=timezone.localdate().replace(day=1)
                ).count(),
            }
        )


class AppPagarView(AppView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "formularios"

    def post(self, request, uuid):
        cobranca = get_object_or_404(Cobranca, uuid=uuid, socio=request.socio)
        try:
            inicio = services.pagar_online(cobranca)
        except services.CobrancaInvalida as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PagamentoIndisponivel as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"pagamento": {"tipo": inicio.tipo, "url": inicio.url, "campos": inicio.campos}})
