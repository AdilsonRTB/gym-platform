import uuid

from django import forms
from django.db import models
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from apps.core.fields import EncryptedTextField
from apps.leads.models import Consentimento
from apps.tenants.forms import TenantAdminModelForm
from apps.tenants.models import TenantModel

# --------------------------------------------------------------------------- Configuração por ginásio


class Ambiente(models.TextChoices):
    TESTE = "teste", "Testes"
    PRODUCAO = "producao", "Produção"


@register_setting(icon="credit-card")
class ConfiguracaoPagamentos(BaseSiteSetting):
    class Fornecedor(models.TextChoices):
        DESLIGADO = "", "Sem pagamento online"
        SISP = "sisp", "SISP · Vinti4Net"
        SIMULADO = "simulado", "Simulado (só para testes)"

    fornecedor = models.CharField(max_length=20, choices=Fornecedor.choices, blank=True, default="")
    ambiente = models.CharField(max_length=20, choices=Ambiente.choices, default=Ambiente.TESTE)
    sisp_pos_id = models.CharField("POS ID", max_length=30, blank=True)
    sisp_pos_aut_code = EncryptedTextField("POS Auth Code", blank=True, help_text="Guardado cifrado.")
    sisp_url = models.URLField(
        "URL de pagamento", blank=True, help_text="Vazio usa o endereço oficial do Vinti4Net."
    )

    panels = [
        FieldRowPanel([FieldPanel("fornecedor"), FieldPanel("ambiente")]),
        MultiFieldPanel(
            [
                FieldPanel("sisp_pos_id"),
                FieldPanel("sisp_pos_aut_code", widget=forms.PasswordInput(render_value=True)),
                FieldPanel("sisp_url"),
            ],
            heading="Credenciais SISP",
        ),
    ]

    class Meta:
        verbose_name = "Pagamentos online"


class ConfiguracaoFiscalForm(WagtailAdminModelForm):
    certificado_ficheiro = forms.FileField(
        label="Certificado ICP-CV (.p12/.pfx)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.certificado_nome:
            self.fields[
                "certificado_ficheiro"
            ].help_text = f"Certificado atual: {self.instance.certificado_nome}. Envie outro ficheiro para o substituir."
        else:
            self.fields["certificado_ficheiro"].help_text = "Ainda não foi carregado nenhum certificado."

    def save(self, commit=True):
        ficheiro = self.cleaned_data.get("certificado_ficheiro")
        if ficheiro:
            import base64

            self.instance.certificado_b64 = base64.b64encode(ficheiro.read()).decode()
            self.instance.certificado_nome = ficheiro.name
        return super().save(commit)


@register_setting(icon="doc-full-inverse")
class ConfiguracaoFiscal(BaseSiteSetting):
    class Fornecedor(models.TextChoices):
        DESLIGADO = "", "Sem faturação automática"
        EFATURA_CV = "efatura_cv", "e-Fatura (DNRE Cabo Verde)"
        SIMULADO = "simulado", "Simulado (só para testes)"

    fornecedor = models.CharField(max_length=20, choices=Fornecedor.choices, blank=True, default="")
    ambiente = models.CharField(max_length=20, choices=Ambiente.choices, default=Ambiente.TESTE)
    nif = models.CharField("NIF do emissor", max_length=20, blank=True)
    nome_fiscal = models.CharField(max_length=200, blank=True)
    morada_fiscal = models.CharField(max_length=250, blank=True)
    serie = models.CharField(
        "Série", max_length=20, default="FT", help_text="Prefixo da numeração das faturas."
    )
    certificado_b64 = EncryptedTextField(blank=True, editable=False)
    certificado_nome = models.CharField(max_length=200, blank=True, editable=False)
    certificado_senha = EncryptedTextField("Palavra-passe do certificado", blank=True)
    efatura_url = models.URLField(
        "Endpoint e-Fatura", blank=True, help_text="Endereço de transmissão da DNRE."
    )

    base_form_class = ConfiguracaoFiscalForm
    panels = [
        FieldRowPanel([FieldPanel("fornecedor"), FieldPanel("ambiente")]),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("nif"), FieldPanel("nome_fiscal")]),
                FieldPanel("morada_fiscal"),
                FieldPanel("serie"),
            ],
            heading="Dados fiscais do ginásio (emissor)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("certificado_ficheiro"),
                FieldPanel("certificado_senha", widget=forms.PasswordInput(render_value=True)),
                FieldPanel("efatura_url"),
            ],
            heading="Certificado digital",
        ),
    ]

    class Meta:
        verbose_name = "Faturação (e-Fatura)"


# --------------------------------------------------------------------------- Adesões, pagamentos e faturas


class Adesao(Consentimento, TenantModel):
    class Estado(models.TextChoices):
        PENDENTE = "pendente", "A aguardar pagamento"
        PAGA = "paga", "Paga"
        FALHADA = "falhada", "Pagamento falhado"
        CANCELADA = "cancelada", "Cancelada"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    plano = models.ForeignKey("content.Plano", on_delete=models.PROTECT, related_name="adesoes")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    nome = models.CharField(max_length=120)
    email = models.EmailField()
    telefone = models.CharField(max_length=30)
    nif = models.CharField("NIF", max_length=20, blank=True)
    morada = models.CharField(max_length=200, blank=True)
    valor_cve = models.PositiveIntegerField("Valor (CVE)")
    criado_em = models.DateTimeField(auto_now_add=True)
    paga_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "adesão"
        verbose_name_plural = "adesões"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.nome} · {self.plano.nome if self.plano_id else ''}"


class PagamentoForm(TenantAdminModelForm):
    """No Admin só se registam pagamentos presenciais; os online vêm do fluxo de adesão."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "metodo" in self.fields:
            self.fields["metodo"].choices = [c for c in self.fields["metodo"].choices if c[0] != "vinti4"]


class Pagamento(TenantModel):
    class Metodo(models.TextChoices):
        VINTI4 = "vinti4", "Vinti4Net (online)"
        NUMERARIO = "numerario", "Numerário"
        TPA = "tpa", "TPA / cartão"
        TRANSFERENCIA = "transferencia", "Transferência"

    class Origem(models.TextChoices):
        ADESAO = "adesao", "Adesão no site"
        APP = "app", "App do sócio"
        BALCAO = "balcao", "Receção"

    class Estado(models.TextChoices):
        INICIADO = "iniciado", "Iniciado"
        PAGO = "pago", "Pago"
        FALHADO = "falhado", "Falhado"
        CANCELADO = "cancelado", "Cancelado"

    base_form_class = PagamentoForm

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    adesao = models.ForeignKey(
        Adesao, null=True, blank=True, on_delete=models.SET_NULL, related_name="pagamentos"
    )
    socio = models.ForeignKey(
        "gestao.Socio", null=True, blank=True, on_delete=models.SET_NULL, related_name="pagamentos"
    )
    cobranca = models.ForeignKey(
        "gestao.Cobranca", null=True, blank=True, on_delete=models.SET_NULL, related_name="pagamentos"
    )
    origem = models.CharField(max_length=20, choices=Origem.choices, default=Origem.BALCAO)
    metodo = models.CharField("Método", max_length=20, choices=Metodo.choices)
    fornecedor = models.CharField(max_length=20, blank=True, editable=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.INICIADO)
    valor_cve = models.PositiveIntegerField("Valor (CVE)")
    descricao = models.CharField("Descrição", max_length=200)
    nome_cliente = models.CharField("Cliente", max_length=120)
    nif_cliente = models.CharField("NIF do cliente", max_length=20, blank=True)
    email_cliente = models.EmailField("Email do cliente", blank=True)
    referencia = models.CharField(max_length=40, blank=True, editable=False, db_index=True)
    transacao_id = models.CharField(max_length=60, blank=True, editable=False)
    resposta = models.JSONField(default=dict, blank=True, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    confirmado_em = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.valor_cve} CVE · {self.nome_cliente} · {self.get_estado_display()}"


class Fatura(TenantModel):
    class Estado(models.TextChoices):
        PENDENTE = "pendente", "Por emitir"
        EMITIDA = "emitida", "Emitida"
        ERRO = "erro", "Erro na emissão"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pagamento = models.OneToOneField(Pagamento, on_delete=models.PROTECT, related_name="fatura")
    serie = models.CharField(max_length=20)
    ano = models.PositiveIntegerField()
    sequencia = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    fornecedor = models.CharField(max_length=20, blank=True)
    iud = models.CharField("IUD", max_length=60, blank=True, help_text="Identificador único do documento.")
    valor_cve = models.PositiveIntegerField()
    nome_cliente = models.CharField(max_length=120)
    nif_cliente = models.CharField(max_length=20, blank=True)
    xml = models.TextField(blank=True)
    erro = models.TextField(blank=True)
    emitida_em = models.DateTimeField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "fatura"
        verbose_name_plural = "faturas"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["ginasio", "serie", "ano", "sequencia"], name="fatura_numero_unico"
            )
        ]

    def __str__(self) -> str:
        return self.numero

    @property
    def numero(self) -> str:
        return f"{self.serie} {self.ano}/{self.sequencia:05d}"
