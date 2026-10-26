from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from .context import get_current_ginasio
from .managers import TenantManager


class Ginasio(models.Model):
    class Estado(models.TextChoices):
        ONBOARDING = "onboarding", "Em configuração"
        ATIVO = "ativo", "Ativo"
        SUSPENSO = "suspenso", "Suspenso"

    class PlanoPlataforma(models.TextChoices):
        ESSENCIAL = "essencial", "Essencial"
        PRO = "pro", "Pro"
        PREMIUM = "premium", "Premium"

    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True, help_text="Usado no subdomínio da plataforma.")
    nif = models.CharField("NIF", max_length=20, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ONBOARDING)
    plano_plataforma = models.CharField(
        "Plano da plataforma",
        max_length=20,
        choices=PlanoPlataforma.choices,
        default=PlanoPlataforma.ESSENCIAL,
    )
    pais = models.CharField("País", max_length=2, default="CV", help_text="Define pagamentos e faturação.")
    site = models.OneToOneField(
        "wagtailcore.Site", null=True, blank=True, on_delete=models.SET_NULL, related_name="ginasio"
    )
    colecao = models.OneToOneField(
        "wagtailcore.Collection", null=True, blank=True, on_delete=models.SET_NULL, related_name="ginasio"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ginásio"
        verbose_name_plural = "ginásios"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)[:60]
        super().save(*args, **kwargs)

    @property
    def publico(self) -> bool:
        return self.estado != self.Estado.SUSPENSO

    @property
    def dominio_principal(self) -> str | None:
        dominio = self.dominios.filter(principal=True).first() or self.dominios.first()
        return dominio.hostname if dominio else None

    def url_publico(self, path: str = "/") -> str:
        host = self.dominio_principal or f"{self.slug}.{settings.PLATFORM_DOMAIN}"
        port = settings.SITE_PUBLIC_PORT
        suffix = f":{port}" if port and port not in {"80", "443"} else ""
        return f"{settings.SITE_PUBLIC_SCHEME}://{host}{suffix}{path}"


class Dominio(models.Model):
    ginasio = models.ForeignKey(Ginasio, on_delete=models.CASCADE, related_name="dominios")
    hostname = models.CharField(
        max_length=253, unique=True, help_text="Ex.: ginasio.cv ou forca.plataforma.cv"
    )
    principal = models.BooleanField(default=False)
    verificado = models.BooleanField(default=False, help_text="DNS apontado para a plataforma.")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "domínio"
        verbose_name_plural = "domínios"
        ordering = ["-principal", "hostname"]

    def __str__(self) -> str:
        return self.hostname

    def clean(self):
        self.hostname = normalizar_host(self.hostname)
        if not self.hostname or "/" in self.hostname:
            raise ValidationError({"hostname": "Indique apenas o domínio, sem http:// nem caminho."})

    def save(self, *args, **kwargs):
        self.hostname = normalizar_host(self.hostname)
        super().save(*args, **kwargs)
        if self.principal:
            self.ginasio.dominios.exclude(pk=self.pk).update(principal=False)
            site = self.ginasio.site
            if site and site.hostname != self.hostname:
                site.hostname = self.hostname
                site.save(update_fields=["hostname"])


def normalizar_host(host: str) -> str:
    host = (host or "").strip().lower()
    for prefix in ("https://", "http://"):
        host = host.removeprefix(prefix)
    host = host.split("/")[0].split(":")[0]
    return host.rstrip(".")


class Papel(models.TextChoices):
    DONO = "dono", "Dono"
    GESTOR = "gestor", "Gestor"
    RECECIONISTA = "rececionista", "Rececionista"
    TREINADOR = "treinador", "Treinador"


class Membro(models.Model):
    """Ligação utilizador ↔ ginásio com um perfil. Um utilizador pode pertencer a vários ginásios."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membros")
    ginasio = models.ForeignKey(Ginasio, on_delete=models.CASCADE, related_name="membros")
    papel = models.CharField(max_length=20, choices=Papel.choices)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "membro da equipa"
        verbose_name_plural = "equipa do ginásio"
        permissions = [("gerir_equipa", "Pode gerir a equipa do ginásio")]
        constraints = [models.UniqueConstraint(fields=["user", "ginasio"], name="membro_unico_por_ginasio")]

    def __str__(self) -> str:
        return f"{self.user} · {self.get_papel_display()} · {self.ginasio}"


class TenantModel(models.Model):
    """Base de todo o conteúdo próprio: chave de tenant + filtro automático."""

    ginasio = models.ForeignKey(Ginasio, on_delete=models.CASCADE, editable=False, related_name="+")

    objects = TenantManager()
    todos = models.Manager()

    class Meta:
        abstract = True

    def atribuir_ginasio(self) -> None:
        if not self.ginasio_id:
            ginasio = get_current_ginasio()
            if ginasio is None:
                raise ValidationError("Selecione um ginásio antes de criar conteúdo.")
            self.ginasio = ginasio

    def save(self, *args, **kwargs):
        self.atribuir_ginasio()
        super().save(*args, **kwargs)
