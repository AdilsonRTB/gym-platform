from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.api.serializers import PkDoGinasio
from apps.billing.models import Pagamento
from apps.content.models import Plano

from .models import Assinatura, CheckIn, Cobranca, Socio


class AssinaturaSerializer(serializers.ModelSerializer):
    plano = serializers.CharField(source="plano.nome")
    plano_id = serializers.IntegerField()
    periodicidade = serializers.CharField(source="plano.periodicidade")
    valida = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Assinatura
        fields = [
            "id",
            "plano",
            "plano_id",
            "periodicidade",
            "preco_cve",
            "data_inicio",
            "data_fim",
            "estado",
            "valida",
            "dias_restantes",
        ]

    def get_valida(self, obj):
        return obj.valida()

    def get_dias_restantes(self, obj):
        return (obj.data_fim - timezone.localdate()).days


class CobrancaSerializer(serializers.ModelSerializer):
    atrasada = serializers.BooleanField(read_only=True)
    fatura = serializers.SerializerMethodField()
    metodo = serializers.SerializerMethodField()

    class Meta:
        model = Cobranca
        fields = [
            "id",
            "uuid",
            "descricao",
            "periodo_inicio",
            "periodo_fim",
            "valor_cve",
            "vencimento",
            "estado",
            "atrasada",
            "paga_em",
            "fatura",
            "metodo",
        ]

    def _pago(self, obj):
        return next((p for p in obj.pagamentos.all() if p.estado == Pagamento.Estado.PAGO), None)

    def get_fatura(self, obj):
        pagamento = self._pago(obj)
        fatura = getattr(pagamento, "fatura", None) if pagamento else None
        return {"numero": fatura.numero, "estado": fatura.estado} if fatura else None

    def get_metodo(self, obj):
        pagamento = self._pago(obj)
        return pagamento.get_metodo_display() if pagamento else None


class CobrancaListaSerializer(CobrancaSerializer):
    socio = serializers.SerializerMethodField()

    class Meta(CobrancaSerializer.Meta):
        fields = [*CobrancaSerializer.Meta.fields, "socio"]

    def get_socio(self, obj):
        return {
            "id": obj.socio_id,
            "numero": obj.socio.numero,
            "nome": obj.socio.nome,
            "telefone": obj.socio.telefone,
        }


class CheckInSerializer(serializers.ModelSerializer):
    socio = serializers.SerializerMethodField()

    class Meta:
        model = CheckIn
        fields = ["id", "momento", "permitido", "motivo", "origem", "offline", "socio"]

    def get_socio(self, obj):
        return {"id": obj.socio_id, "numero": obj.socio.numero, "nome": obj.socio.nome} if obj.socio else None


class SocioResumoSerializer(serializers.ModelSerializer):
    assinatura = serializers.SerializerMethodField()
    em_atraso = serializers.SerializerMethodField()

    class Meta:
        model = Socio
        fields = [
            "id",
            "numero",
            "nome",
            "email",
            "telefone",
            "estado",
            "assinatura",
            "em_atraso",
            "criado_em",
        ]

    def get_assinatura(self, obj):
        a = obj.assinatura_atual
        return AssinaturaSerializer(a).data if a else None

    def get_em_atraso(self, obj):
        hoje = timezone.localdate()
        return any(c.estado == Cobranca.Estado.PENDENTE and c.vencimento < hoje for c in obj.cobrancas.all())


class SocioSerializer(SocioResumoSerializer):
    codigo = serializers.UUIDField(read_only=True)

    class Meta(SocioResumoSerializer.Meta):
        fields = [
            *SocioResumoSerializer.Meta.fields,
            "codigo",
            "nif",
            "data_nascimento",
            "morada",
            "contacto_emergencia",
            "lembretes",
            "notas",
        ]
        read_only_fields = ["numero", "codigo", "criado_em"]


class NovoSocioSerializer(serializers.ModelSerializer):
    plano = PkDoGinasio(Plano, {"live": True}, required=False, allow_null=True, write_only=True)
    consentimento = serializers.BooleanField(write_only=True)

    class Meta:
        model = Socio
        fields = [
            "nome",
            "email",
            "telefone",
            "nif",
            "data_nascimento",
            "morada",
            "contacto_emergencia",
            "lembretes",
            "notas",
            "plano",
            "consentimento",
        ]

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("telefone"):
            raise serializers.ValidationError({"telefone": "Indique um telefone ou um email."})
        if not attrs.get("consentimento"):
            raise serializers.ValidationError({"consentimento": "Confirme o consentimento do sócio."})
        return attrs


class CheckInEntradaSerializer(serializers.Serializer):
    codigo = serializers.CharField(required=False, allow_blank=True)
    socio_id = serializers.IntegerField(required=False)
    client_id = serializers.UUIDField(required=False)
    momento = serializers.DateTimeField(required=False)
    offline = serializers.BooleanField(default=False)
    dispositivo = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("codigo") and not attrs.get("socio_id"):
            raise serializers.ValidationError("Indique o código do cartão ou o sócio.")
        momento = attrs.get("momento")
        # Um dispositivo com a hora errada não pode registar entradas no futuro.
        if momento and momento > timezone.now() + timedelta(minutes=5):
            attrs["momento"] = timezone.now()
        return attrs
