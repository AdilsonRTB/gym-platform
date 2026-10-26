from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.shortcuts import redirect
from django.utils.text import slugify
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import DraftStateMixin, Page, RevisionMixin
from wagtail.search import index

from apps.tenants.forms import TenantAdminModelForm
from apps.tenants.models import TenantModel

from .blocks import BlocosPagina

# Caminhos usados pelas páginas fixas do site; uma página do CMS não pode ocupar estes endereços.
ROTAS_RESERVADAS = {
    "modalidades",
    "horario",
    "planos",
    "equipa",
    "contactos",
    "aderir",
    "privacidade",
    "preview",
    "gestao",
    "app",
    "manifest.webmanifest",
    "api",
    "sitemap.xml",
    "robots.txt",
}


# --------------------------------------------------------------------------- Páginas


class PaginaBase(Page):
    corpo = StreamField(BlocosPagina(), blank=True, use_json_field=True)
    imagem_partilha = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Imagem mostrada ao partilhar nas redes sociais (1200×630).",
    )
    indexar = models.BooleanField("Mostrar nos motores de busca", default=True)

    content_panels = [*Page.content_panels, FieldPanel("corpo")]
    promote_panels = [
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("seo_title"), FieldPanel("search_description")],
            heading="SEO",
        ),
        MultiFieldPanel(
            [FieldPanel("imagem_partilha"), FieldPanel("indexar"), FieldPanel("show_in_menus")],
            heading="Partilha e navegação",
        ),
    ]
    search_fields = [*Page.search_fields, index.SearchField("corpo")]

    class Meta:
        abstract = True

    def ginasio(self):
        site = self.get_site()
        return getattr(site, "ginasio", None) if site else None

    def caminho_site(self) -> str:
        """Caminho da página no site do ginásio (ex.: `/`, `/sobre/`)."""
        site = self.get_site()
        if site is None:
            return "/"
        raiz = site.root_page.url_path
        return "/" + self.url_path[len(raiz) :] if self.url_path.startswith(raiz) else "/"

    def get_url_parts(self, request=None):
        """O endereço público de cada página é o do site Next.js do ginásio."""
        from apps.tenants.models import Ginasio

        parts = super().get_url_parts(request)
        if parts is None:
            return None
        site_id, root_url, page_path = parts
        ginasio = Ginasio.objects.filter(site_id=site_id).first()
        if ginasio:
            root_url = ginasio.url_publico("").rstrip("/")
        return site_id, root_url, page_path

    def serve(self, request, *args, **kwargs):
        # O site público é o Next.js; o Wagtail só serve a API e o Admin.
        ginasio = self.ginasio()
        if ginasio:
            return redirect(ginasio.url_publico(self.caminho_site()))
        return super().serve(request, *args, **kwargs)

    def serve_preview(self, request, mode_name):
        from .preview import guardar_preview

        ginasio = self.ginasio()
        token = guardar_preview(self, ginasio)
        return redirect(ginasio.url_publico(f"/preview/{token}") if ginasio else f"/api/v1/preview/{token}/")


class HomePage(PaginaBase):
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["content.PaginaGenerica"]

    class Meta:
        verbose_name = "página inicial"
        verbose_name_plural = "páginas iniciais"


class PaginaGenerica(PaginaBase):
    parent_page_types = ["content.HomePage", "content.PaginaGenerica"]
    subpage_types = ["content.PaginaGenerica"]

    class Meta:
        verbose_name = "página"
        verbose_name_plural = "páginas"

    def clean(self):
        super().clean()
        parent = self.get_parent()
        if parent and parent.specific_class is HomePage and self.slug in ROTAS_RESERVADAS:
            raise ValidationError({"slug": f"O endereço /{self.slug} é usado por uma página fixa do site."})


# --------------------------------------------------------------------------- Snippets


class ConteudoBase(DraftStateMixin, RevisionMixin, TenantModel):
    """Snippet do ginásio com rascunho/publicado e histórico de revisões."""

    ordem = models.PositiveIntegerField(default=0, help_text="Menor aparece primeiro.")
    _revisions = GenericRelation("wagtailcore.Revision")

    base_form_class = TenantAdminModelForm

    class Meta:
        abstract = True
        ordering = ["ordem", "pk"]

    @property
    def revisions(self):
        return self._revisions


class ComSlug(models.Model):
    """Slug único dentro do ginásio, gerado a partir de `nome`."""

    slug = models.SlugField(max_length=80, blank=True, help_text="Gerado a partir do nome se ficar vazio.")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.atribuir_ginasio()
        self.gerar_slug(self.nome)
        super().save(*args, **kwargs)

    def gerar_slug(self, base: str) -> None:
        if self.slug:
            return
        base = slugify(base)[:70] or "item"
        slug, n = base, 2
        manager = type(self).todos
        while manager.filter(ginasio_id=self.ginasio_id, slug=slug).exclude(pk=self.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        self.slug = slug


class Modalidade(ComSlug, ConteudoBase, index.Indexed):
    class Nivel(models.TextChoices):
        TODOS = "todos", "Todos os níveis"
        INICIANTE = "iniciante", "Iniciante"
        INTERMEDIO = "intermedio", "Intermédio"
        AVANCADO = "avancado", "Avançado"

    nome = models.CharField(max_length=80)
    resumo = models.CharField(max_length=180, blank=True, help_text="Uma frase para os cartões.")
    descricao = RichTextField("Descrição", blank=True, features=["h3", "bold", "italic", "link", "ul"])
    imagem = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    nivel = models.CharField("Nível", max_length=20, choices=Nivel.choices, default=Nivel.TODOS)
    duracao_min = models.PositiveIntegerField("Duração (min)", default=50)

    panels = [
        FieldPanel("nome"),
        FieldPanel("resumo"),
        FieldPanel("descricao"),
        FieldPanel("imagem"),
        FieldRowPanel([FieldPanel("nivel"), FieldPanel("duracao_min"), FieldPanel("ordem")]),
        FieldPanel("slug"),
    ]
    search_fields = [index.SearchField("nome"), index.AutocompleteField("nome")]

    class Meta(ConteudoBase.Meta):
        verbose_name = "modalidade"
        verbose_name_plural = "modalidades"
        constraints = [
            models.UniqueConstraint(fields=["ginasio", "slug"], name="modalidade_slug_por_ginasio")
        ]

    def __str__(self) -> str:
        return self.nome


class Treinador(ComSlug, ConteudoBase, index.Indexed):
    nome = models.CharField(max_length=80)
    cargo = models.CharField(max_length=80, blank=True, help_text="Ex.: Treinador principal")
    foto = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    especialidades = models.CharField(max_length=200, blank=True, help_text="Separadas por vírgulas.")
    biografia = models.TextField(blank=True)
    instagram = models.CharField(max_length=60, blank=True, help_text="Nome de utilizador, sem @.")
    modalidades = models.ManyToManyField(Modalidade, blank=True, related_name="treinadores")
    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="perfis_treinador",
        verbose_name="Utilizador",
        help_text="Conta do treinador no Admin, para editar o próprio perfil e as suas aulas.",
    )

    panels = [
        FieldRowPanel([FieldPanel("nome"), FieldPanel("cargo")]),
        FieldPanel("foto"),
        FieldPanel("especialidades"),
        FieldPanel("biografia"),
        FieldPanel("modalidades"),
        FieldRowPanel([FieldPanel("instagram"), FieldPanel("ordem")]),
        FieldPanel("user"),
        FieldPanel("slug"),
    ]
    search_fields = [index.SearchField("nome"), index.AutocompleteField("nome")]

    class Meta(ConteudoBase.Meta):
        verbose_name = "treinador"
        verbose_name_plural = "treinadores"
        constraints = [models.UniqueConstraint(fields=["ginasio", "slug"], name="treinador_slug_por_ginasio")]

    def __str__(self) -> str:
        return self.nome

    @property
    def lista_especialidades(self) -> list[str]:
        return [e.strip() for e in self.especialidades.split(",") if e.strip()]


class Plano(ConteudoBase, index.Indexed):
    class Periodicidade(models.TextChoices):
        AVULSO = "avulso", "Aula avulsa"
        SEMANAL = "semanal", "Semanal"
        MENSAL = "mensal", "Mensal"
        TRIMESTRAL = "trimestral", "Trimestral"
        SEMESTRAL = "semestral", "Semestral"
        ANUAL = "anual", "Anual"

    nome = models.CharField(max_length=80)
    descricao = models.CharField("Descrição", max_length=200, blank=True)
    preco_cve = models.PositiveIntegerField("Preço (CVE)")
    periodicidade = models.CharField(
        max_length=20, choices=Periodicidade.choices, default=Periodicidade.MENSAL
    )
    taxa_inscricao_cve = models.PositiveIntegerField("Taxa de inscrição (CVE)", default=0)
    beneficios = models.TextField("Benefícios", blank=True, help_text="Um benefício por linha.")
    destaque = models.BooleanField(default=False, help_text="Realçar como plano recomendado.")
    adesao_online = models.BooleanField("Permite adesão online", default=True)

    panels = [
        FieldRowPanel([FieldPanel("nome"), FieldPanel("periodicidade")]),
        FieldPanel("descricao"),
        FieldRowPanel([FieldPanel("preco_cve"), FieldPanel("taxa_inscricao_cve")]),
        FieldPanel("beneficios"),
        FieldRowPanel([FieldPanel("destaque"), FieldPanel("adesao_online"), FieldPanel("ordem")]),
    ]
    search_fields = [index.SearchField("nome")]

    class Meta(ConteudoBase.Meta):
        verbose_name = "plano"
        verbose_name_plural = "planos"

    def __str__(self) -> str:
        return f"{self.nome} · {self.preco_cve} CVE"

    @property
    def lista_beneficios(self) -> list[str]:
        return [b.strip() for b in self.beneficios.splitlines() if b.strip()]

    @property
    def total_adesao_cve(self) -> int:
        return self.preco_cve + self.taxa_inscricao_cve


class Aula(ConteudoBase):
    class Dia(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE, related_name="aulas")
    dia_semana = models.PositiveSmallIntegerField("Dia", choices=Dia.choices)
    hora_inicio = models.TimeField("Início")
    hora_fim = models.TimeField("Fim")
    treinador = models.ForeignKey(
        Treinador, null=True, blank=True, on_delete=models.SET_NULL, related_name="aulas"
    )
    sala = models.CharField(max_length=60, blank=True)
    lotacao = models.PositiveIntegerField(
        "Lotação", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(500)]
    )

    panels = [
        FieldPanel("modalidade"),
        FieldRowPanel([FieldPanel("dia_semana"), FieldPanel("hora_inicio"), FieldPanel("hora_fim")]),
        FieldRowPanel([FieldPanel("treinador"), FieldPanel("sala"), FieldPanel("lotacao")]),
    ]

    class Meta(ConteudoBase.Meta):
        verbose_name = "aula no horário"
        verbose_name_plural = "horário de aulas"
        ordering = ["dia_semana", "hora_inicio"]

    def __str__(self) -> str:
        return f"{self.modalidade} · {self.get_dia_semana_display()} {self.hora_inicio:%H:%M}"

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError({"hora_fim": "A aula tem de terminar depois de começar."})


class Testemunho(ConteudoBase):
    texto = models.TextField(max_length=600)
    autor = models.CharField(max_length=80)
    detalhe = models.CharField(max_length=80, blank=True, help_text="Ex.: Sócia desde 2022")
    foto = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    panels = [
        FieldPanel("texto"),
        FieldRowPanel([FieldPanel("autor"), FieldPanel("detalhe")]),
        FieldRowPanel([FieldPanel("foto"), FieldPanel("ordem")]),
    ]

    class Meta(ConteudoBase.Meta):
        verbose_name = "testemunho"
        verbose_name_plural = "testemunhos"

    def __str__(self) -> str:
        return f"{self.autor}: {self.texto[:40]}…"


class Pergunta(ConteudoBase):
    pergunta = models.CharField(max_length=200)
    resposta = models.TextField()

    panels = [FieldPanel("pergunta"), FieldPanel("resposta"), FieldPanel("ordem")]

    class Meta(ConteudoBase.Meta):
        verbose_name = "pergunta frequente"
        verbose_name_plural = "perguntas frequentes"

    def __str__(self) -> str:
        return self.pergunta
