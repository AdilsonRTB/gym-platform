import uuid

from django.db import models

from apps.tenants.forms import TenantAdminModelForm
from apps.tenants.models import TenantModel


class Consentimento(models.Model):
    """Registo do consentimento dado num formulário (CNPD)."""

    consentimento = models.BooleanField(default=False)
    consentimento_texto = models.TextField("Texto aceite", blank=True)
    consentimento_em = models.DateTimeField("Aceite em", null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    class Meta:
        abstract = True


class Lead(Consentimento, TenantModel):
    class Tipo(models.TextChoices):
        CONTACTO = "contacto", "Contacto"
        AULA_EXPERIMENTAL = "aula_experimental", "Aula experimental"

    class Estado(models.TextChoices):
        NOVO = "novo", "Novo"
        CONTACTADO = "contactado", "Contactado"
        CONVERTIDO = "convertido", "Convertido em sócio"
        ARQUIVADO = "arquivado", "Arquivado"

    base_form_class = TenantAdminModelForm

    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.CONTACTO)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.NOVO)
    nome = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    mensagem = models.TextField(blank=True)
    modalidade = models.ForeignKey(
        "content.Modalidade", null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    data_preferida = models.DateField("Data preferida", null=True, blank=True)
    origem = models.CharField(max_length=200, blank=True, help_text="Página do site onde o pedido foi feito.")
    notas = models.TextField("Notas internas", blank=True)
    criado_em = models.DateTimeField("Recebido em", auto_now_add=True)

    class Meta:
        verbose_name = "lead"
        verbose_name_plural = "leads"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.nome} · {self.get_tipo_display()}"


class PedidoDados(TenantModel):
    """Pedido de acesso/exportação ou eliminação de dados pessoais."""

    class Tipo(models.TextChoices):
        EXPORTACAO = "exportacao", "Acesso / exportação"
        ELIMINACAO = "eliminacao", "Eliminação"

    class Estado(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONCLUIDO = "concluido", "Concluído"
        REJEITADO = "rejeitado", "Rejeitado"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDENTE)
    nome = models.CharField(max_length=120, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    notas = models.TextField(blank=True)
    pedido_em = models.DateTimeField(auto_now_add=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "pedido de dados"
        verbose_name_plural = "pedidos de dados (CNPD)"
        ordering = ["-pedido_em"]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} · {self.email}"
