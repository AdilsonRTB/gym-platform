from django.utils import timezone
from rest_framework import serializers
from wagtail.rich_text import expand_db_html

from apps.branding.models import MarcaSettings, PrivacidadeSettings, SeoSettings
from apps.content.images import imagem_api
from apps.content.models import Aula, Modalidade, Pergunta, Plano, Testemunho, Treinador
from apps.leads.models import Lead, PedidoDados


class ImagemField(serializers.Field):
    def __init__(self, quadrado=False, **kwargs):
        self.quadrado = quadrado
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        return imagem_api(value, quadrado=self.quadrado)

    def get_attribute(self, instance):
        return getattr(instance, self.source or self.field_name, None)


class DoGinasio:
    """Avalia o queryset em cada pedido, para aplicar o filtro do ginásio atual.

    Um `queryset=Modelo.objects...` na definição da classe seria criado no import, sem tenant.
    """

    def __init__(self, model, filtros=None, **kwargs):
        self.model, self.filtros = model, filtros or {}
        super().__init__(**kwargs)

    def get_queryset(self):
        return self.model.objects.filter(**self.filtros)


class SlugDoGinasio(DoGinasio, serializers.SlugRelatedField):
    pass


class PkDoGinasio(DoGinasio, serializers.PrimaryKeyRelatedField):
    pass


class RichTextField(serializers.CharField):
    def to_representation(self, value):
        return expand_db_html(value or "")


# --------------------------------------------------------------------------- Snippets


class ModalidadeResumoSerializer(serializers.ModelSerializer):
    imagem = ImagemField()

    class Meta:
        model = Modalidade
        fields = ["id", "slug", "nome", "resumo", "imagem", "nivel", "duracao_min"]


class TreinadorSerializer(serializers.ModelSerializer):
    foto = ImagemField(quadrado=True)
    especialidades = serializers.ListField(source="lista_especialidades", read_only=True)
    modalidades = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")

    class Meta:
        model = Treinador
        fields = [
            "id",
            "slug",
            "nome",
            "cargo",
            "foto",
            "especialidades",
            "biografia",
            "instagram",
            "modalidades",
        ]


class ModalidadeSerializer(ModalidadeResumoSerializer):
    descricao = RichTextField()
    treinadores = serializers.SerializerMethodField()

    class Meta(ModalidadeResumoSerializer.Meta):
        fields = [*ModalidadeResumoSerializer.Meta.fields, "descricao", "treinadores"]

    def get_treinadores(self, obj):
        return TreinadorSerializer(obj.treinadores.filter(live=True), many=True).data


class PlanoSerializer(serializers.ModelSerializer):
    beneficios = serializers.ListField(source="lista_beneficios", read_only=True)

    class Meta:
        model = Plano
        fields = [
            "id",
            "nome",
            "descricao",
            "preco_cve",
            "periodicidade",
            "taxa_inscricao_cve",
            "beneficios",
            "destaque",
            "adesao_online",
        ]


class AulaSerializer(serializers.ModelSerializer):
    modalidade = serializers.SerializerMethodField()
    treinador = serializers.SerializerMethodField()
    hora_inicio = serializers.TimeField(format="%H:%M")
    hora_fim = serializers.TimeField(format="%H:%M")

    class Meta:
        model = Aula
        fields = ["id", "dia_semana", "hora_inicio", "hora_fim", "sala", "lotacao", "modalidade", "treinador"]

    def get_modalidade(self, obj):
        return {"slug": obj.modalidade.slug, "nome": obj.modalidade.nome}

    def get_treinador(self, obj):
        if obj.treinador and obj.treinador.live:
            return {"slug": obj.treinador.slug, "nome": obj.treinador.nome}
        return None


class TestemunhoSerializer(serializers.ModelSerializer):
    foto = ImagemField(quadrado=True)

    class Meta:
        model = Testemunho
        fields = ["id", "texto", "autor", "detalhe", "foto"]


class PerguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = ["id", "pergunta", "resposta"]


# --------------------------------------------------------------------------- Site e páginas


def serializar_pagina(pagina) -> dict:
    pagina = pagina.specific
    return {
        "id": pagina.pk,
        "tipo": pagina._meta.model_name,
        "titulo": pagina.title,
        "caminho": pagina.caminho_site(),
        "seo": {
            "titulo": pagina.seo_title or pagina.title,
            "descricao": pagina.search_description,
            "imagem": imagem_api(pagina.imagem_partilha),
            "indexar": pagina.indexar,
        },
        "corpo": pagina.corpo.stream_block.get_api_representation(pagina.corpo, context={}),
        "publicada_em": pagina.last_published_at.isoformat() if pagina.last_published_at else None,
    }


def serializar_site(ginasio, request=None) -> dict:
    site = ginasio.site
    marca = MarcaSettings.for_site(site)
    seo = SeoSettings.for_site(site)
    privacidade = PrivacidadeSettings.for_site(site)
    raiz = site.root_page.specific
    menu = [
        {"titulo": p.title, "caminho": p.specific.caminho_site()}
        for p in raiz.get_children().live().in_menu().specific()
    ]
    horario = [bloco.value for bloco in marca.horario_funcionamento]
    return {
        "id": ginasio.pk,
        "nome": ginasio.nome,
        "slug": ginasio.slug,
        "dominio": ginasio.dominio_principal,
        "url": ginasio.url_publico("").rstrip("/"),
        "pais": ginasio.pais,
        "moeda": "CVE",
        "idioma": "pt",
        "marca": {
            "modelo": marca.modelo,
            "slogan": marca.slogan,
            "logotipo": imagem_api(marca.logotipo),
            "logotipo_claro": imagem_api(marca.logotipo_claro),
            "favicon": imagem_api(marca.favicon, quadrado=True),
            "cores": {
                "primaria": marca.cor_primaria,
                "destaque": marca.cor_destaque,
                "fundo": marca.cor_fundo,
                "texto": marca.cor_texto,
            },
            "fontes": {"titulos": marca.fonte_titulos, "texto": marca.fonte_texto},
        },
        "contactos": {
            "telefone": marca.telefone,
            "whatsapp": marca.whatsapp,
            "email": marca.email,
            "morada": marca.morada,
            "cidade": marca.cidade,
            "mapa_url": marca.mapa_url,
            "horario": [{"dias": h["dias"], "horas": h["horas"]} for h in horario],
        },
        "redes": {
            k: v
            for k, v in {
                "instagram": marca.instagram,
                "facebook": marca.facebook,
                "tiktok": marca.tiktok,
                "youtube": marca.youtube,
            }.items()
            if v
        },
        "seo": {
            "titulo_sufixo": seo.titulo_sufixo,
            "descricao": seo.descricao,
            "imagem": imagem_api(seo.imagem_partilha),
            "indexar": seo.indexar and ginasio.estado == ginasio.Estado.ATIVO,
            "google_verificacao": seo.google_verificacao,
            "plausible_dominio": seo.plausible_dominio,
            "ga4_id": seo.ga4_id,
        },
        "privacidade": {"texto_consentimento": privacidade.texto_consentimento},
        "menu": menu,
        "adesao_online": _aceita_pagamentos(ginasio),
    }


def _aceita_pagamentos(ginasio) -> bool:
    from apps.billing.providers.registry import fornecedor_pagamento

    return fornecedor_pagamento(ginasio) is not None


# --------------------------------------------------------------------------- Formulários


class ConsentimentoMixin(serializers.Serializer):
    consentimento = serializers.BooleanField()

    def validate_consentimento(self, value):
        if not value:
            raise serializers.ValidationError("É necessário aceitar a política de privacidade.")
        return value

    def dados_consentimento(self) -> dict:
        request = self.context["request"]
        ginasio = request.ginasio
        texto = PrivacidadeSettings.for_site(ginasio.site).texto_consentimento
        ip = request.headers.get("X-Visitor-Ip") or request.META.get("REMOTE_ADDR")
        return {
            "consentimento": True,
            "consentimento_texto": texto,
            "consentimento_em": timezone.now(),
            "ip": ip.split(",")[0].strip() if ip else None,
            "user_agent": request.headers.get("User-Agent", "")[:300],
        }


class LeadSerializer(ConsentimentoMixin, serializers.ModelSerializer):
    modalidade = SlugDoGinasio(Modalidade, {"live": True}, slug_field="slug", required=False, allow_null=True)
    # Campo-armadilha para bots: tem de ficar vazio.
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Lead
        fields = [
            "tipo",
            "nome",
            "email",
            "telefone",
            "mensagem",
            "modalidade",
            "data_preferida",
            "origem",
            "consentimento",
            "website",
        ]

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("telefone"):
            raise serializers.ValidationError({"email": "Indique um email ou um telefone."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("website", None)
        validated_data.pop("consentimento")
        return Lead.objects.create(**validated_data, **self.dados_consentimento())


class PedidoDadosSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedidoDados
        fields = ["tipo", "nome", "email", "telefone"]


class AdesaoSerializer(ConsentimentoMixin, serializers.Serializer):
    plano = PkDoGinasio(Plano, {"live": True, "adesao_online": True})
    nome = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    telefone = serializers.CharField(max_length=30)
    nif = serializers.RegexField(
        r"^\d{9}$", required=False, allow_blank=True, error_messages={"invalid": "O NIF tem 9 dígitos."}
    )
    morada = serializers.CharField(max_length=200, required=False, allow_blank=True)
