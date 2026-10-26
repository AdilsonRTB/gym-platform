import uuid
from datetime import date, timedelta

from django.db import models, transaction
from django.db.models import Max
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from apps.leads.models import Consentimento
from apps.tenants.forms import TenantAdminModelForm
from apps.tenants.models import Ginasio, TenantModel


def so_digitos(valor: str) -> str:
    return "".join(c for c in (valor or "") if c.isdigit())


class Socio(Consentimento, TenantModel):
    class Estado(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        SUSPENSO = "suspenso", "Suspenso"
        INATIVO = "inativo", "Inativo"

    base_form_class = TenantAdminModelForm

    numero = models.PositiveIntegerField("Nº de sócio", editable=False)
    codigo = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, help_text="Conteúdo do QR do cartão de sócio."
    )
    nome = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    telefone_digitos = models.CharField(max_length=30, blank=True, editable=False, db_index=True)
    nif = models.CharField("NIF", max_length=20, blank=True)
    data_nascimento = models.DateField("Data de nascimento", null=True, blank=True)
    morada = models.CharField(max_length=200, blank=True)
    contacto_emergencia = models.CharField("Contacto de emergência", max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ATIVO)
    lembretes = models.BooleanField("Receber lembretes", default=True)
    notas = models.TextField("Notas internas", blank=True)
    criado_em = models.DateTimeField("Sócio desde", auto_now_add=True)

    panels = [
        FieldRowPanel([FieldPanel("nome"), FieldPanel("estado")]),
        FieldRowPanel([FieldPanel("email"), FieldPanel("telefone"), FieldPanel("nif")]),
        FieldRowPanel([FieldPanel("data_nascimento"), FieldPanel("contacto_emergencia")]),
        FieldPanel("morada"),
        FieldPanel("lembretes"),
        FieldPanel("notas"),
    ]

    class Meta:
        verbose_name = "sócio"
        verbose_name_plural = "sócios"
        ordering = ["-numero"]
        constraints = [models.UniqueConstraint(fields=["ginasio", "numero"], name="socio_numero_por_ginasio")]

    def __str__(self) -> str:
        return f"#{self.numero} {self.nome}"

    def save(self, *args, **kwargs):
        self.atribuir_ginasio()
        self.telefone_digitos = so_digitos(self.telefone)[-9:]  # sem indicativo (238)
        if self.numero:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            Ginasio.objects.select_for_update().get(pk=self.ginasio_id)  # serializa a numeração
            ultimo = Socio.todos.filter(ginasio_id=self.ginasio_id).aggregate(n=Max("numero"))["n"]
            self.numero = (ultimo or 0) + 1
            return super().save(*args, **kwargs)

    # O sócio autenticado na app é o `request.user` do DRF.
    is_authenticated = True

    @property
    def assinatura_atual(self):
        return self.assinaturas.filter(estado=Assinatura.Estado.ATIVA).order_by("-data_fim").first()


PERIODO_MESES = {"mensal": 1, "trimestral": 3, "semestral": 6, "anual": 12}
PERIODO_DIAS = {"semanal": 7, "avulso": 1}


def somar_periodo(inicio: date, periodicidade: str) -> date:
    """Último dia do período que começa em `inicio` (ex.: 15/01 mensal → 14/02)."""
    if periodicidade in PERIODO_DIAS:
        return inicio + timedelta(days=PERIODO_DIAS[periodicidade] - 1)
    meses = PERIODO_MESES.get(periodicidade, 1)
    ano, mes = divmod(inicio.month - 1 + meses, 12)
    ano, mes = inicio.year + ano, mes + 1
    dias_no_mes = (date(ano + (mes // 12), mes % 12 + 1, 1) - timedelta(days=1)).day
    return date(ano, mes, min(inicio.day, dias_no_mes)) - timedelta(days=1)


class Assinatura(TenantModel):
    class Estado(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        CANCELADA = "cancelada", "Cancelada"

    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name="assinaturas")
    plano = models.ForeignKey("content.Plano", on_delete=models.PROTECT, related_name="assinaturas")
    preco_cve = models.PositiveIntegerField("Preço (CVE)")
    data_inicio = models.DateField()
    data_fim = models.DateField("Válida até", help_text="Avança a cada pagamento.")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ATIVA)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "assinatura"
        verbose_name_plural = "assinaturas"
        ordering = ["-data_fim"]

    def __str__(self) -> str:
        return f"{self.socio} · {self.plano.nome}"

    @property
    def periodicidade(self) -> str:
        return self.plano.periodicidade

    def valida(self, dia: date | None = None, tolerancia: int = 0) -> bool:
        dia = dia or timezone.localdate()
        return self.estado == self.Estado.ATIVA and self.data_fim >= dia - timedelta(days=tolerancia)


class Cobranca(TenantModel):
    class Estado(models.TextChoices):
        PENDENTE = "pendente", "Por pagar"
        PAGA = "paga", "Paga"
        ANULADA = "anulada", "Anulada"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name="cobrancas")
    assinatura = models.ForeignKey(Assinatura, on_delete=models.CASCADE, related_name="cobrancas")
    descricao = models.CharField(max_length=200)
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()
    valor_cve = models.PositiveIntegerField("Valor (CVE)")
    vencimento = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    paga_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cobrança"
        verbose_name_plural = "cobranças"
        ordering = ["-vencimento"]

    def __str__(self) -> str:
        return f"{self.descricao} · {self.valor_cve} CVE"

    @property
    def atrasada(self) -> bool:
        return self.estado == self.Estado.PENDENTE and self.vencimento < timezone.localdate()


class CheckIn(TenantModel):
    class Origem(models.TextChoices):
        QR = "qr", "Cartão QR"
        MANUAL = "manual", "Manual"

    socio = models.ForeignKey(Socio, null=True, blank=True, on_delete=models.CASCADE, related_name="checkins")
    momento = models.DateTimeField(
        help_text="Hora da entrada no dispositivo (pode chegar mais tarde, se offline)."
    )
    recebido_em = models.DateTimeField(auto_now_add=True)
    origem = models.CharField(max_length=10, choices=Origem.choices, default=Origem.QR)
    permitido = models.BooleanField()
    motivo = models.CharField(max_length=120, blank=True)
    offline = models.BooleanField(default=False)
    dispositivo = models.CharField(max_length=80, blank=True)
    client_id = models.UUIDField(
        null=True, blank=True, help_text="Identificador do dispositivo (evita duplicados)."
    )
    registado_por = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "check-in"
        verbose_name_plural = "check-ins"
        ordering = ["-momento"]
        constraints = [
            models.UniqueConstraint(fields=["ginasio", "client_id"], name="checkin_client_id_unico")
        ]

    def __str__(self) -> str:
        return f"{self.socio or 'Desconhecido'} · {timezone.localtime(self.momento):%d/%m %H:%M}"


class Lembrete(TenantModel):
    class Tipo(models.TextChoices):
        VENCIMENTO = "vencimento", "Mensalidade a vencer"
        ATRASO_1 = "atraso_1", "Mensalidade em atraso"
        ATRASO_7 = "atraso_7", "Mensalidade em atraso (7 dias)"
        MANUAL = "manual", "Enviado pela receção"

    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name="lembretes_enviados")
    cobranca = models.ForeignKey(
        Cobranca, null=True, blank=True, on_delete=models.CASCADE, related_name="lembretes"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    canais = models.CharField(max_length=60)
    mensagem = models.TextField()
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "lembrete"
        verbose_name_plural = "lembretes"
        ordering = ["-enviado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["cobranca", "tipo"],
                condition=~models.Q(tipo="manual"),
                name="lembrete_unico_por_cobranca",
            )
        ]


MENSAGEM_VENCIMENTO = (
    "Olá {nome}! A sua mensalidade de {valor} CVE no {ginasio} vence a {vencimento}. "
    "Pode pagar na receção ou na app: {link}"
)
MENSAGEM_ATRASO = (
    "Olá {nome}, a mensalidade de {valor} CVE no {ginasio} venceu a {vencimento}. "
    "Regularize na receção ou na app para continuar a treinar: {link}"
)


@register_setting(icon="calendar")
class GestaoSettings(BaseSiteSetting):
    class Canal(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"
        TODOS = "todos", "WhatsApp, SMS e email"

    tolerancia_dias = models.PositiveSmallIntegerField(
        "Tolerância de atraso (dias)",
        default=3,
        help_text="Dias depois do fim da assinatura em que o check-in ainda é aceite.",
    )
    gerar_dias_antes = models.PositiveSmallIntegerField(
        "Gerar cobrança (dias antes)",
        default=7,
        help_text="Quantos dias antes do fim do período se cria a cobrança seguinte.",
    )
    lembretes_ativos = models.BooleanField("Enviar lembretes automáticos", default=True)
    lembrete_dias_antes = models.PositiveSmallIntegerField("Lembrar (dias antes do vencimento)", default=3)
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.WHATSAPP)
    mensagem_vencimento = models.TextField(default=MENSAGEM_VENCIMENTO)
    mensagem_atraso = models.TextField(default=MENSAGEM_ATRASO)

    panels = [
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("tolerancia_dias"), FieldPanel("gerar_dias_antes")])],
            heading="Assinaturas e check-in",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("lembretes_ativos"), FieldPanel("lembrete_dias_antes"), FieldPanel("canal")]
                ),
                FieldPanel(
                    "mensagem_vencimento", help_text="Variáveis: {nome} {valor} {vencimento} {ginasio} {link}"
                ),
                FieldPanel("mensagem_atraso"),
            ],
            heading="Lembretes",
        ),
    ]

    class Meta:
        verbose_name = "Gestão de sócios"
