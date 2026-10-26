from django import forms
from django.core.validators import RegexValidator
from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField

cor_hex = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use o formato #RRGGBB.")
COR_WIDGET = forms.TextInput(attrs={"type": "color", "style": "width:5rem;height:2.5rem;padding:0.2rem"})


class Modelo(models.TextChoices):
    ESSENCIAL = "essencial", "Essencial — claro e sóbrio"
    ENERGIA = "energia", "Energia — escuro e intenso"
    ATELIER = "atelier", "Atelier — suave e editorial"


class Fonte(models.TextChoices):
    INTER = "inter", "Inter"
    MANROPE = "manrope", "Manrope"
    SPACE_GROTESK = "space-grotesk", "Space Grotesk"
    ARCHIVO = "archivo", "Archivo"
    FRAUNCES = "fraunces", "Fraunces (serifa)"
    DM_SANS = "dm-sans", "DM Sans"


class IntervaloBlock(blocks.StructBlock):
    dias = blocks.CharBlock(max_length=40, help_text="Ex.: Segunda a sexta")
    horas = blocks.CharBlock(max_length=40, help_text="Ex.: 06:00 – 22:00 ou Encerrado")


@register_setting(icon="image")
class MarcaSettings(BaseSiteSetting):
    modelo = models.CharField(
        "Modelo do site", max_length=20, choices=Modelo.choices, default=Modelo.ESSENCIAL
    )
    slogan = models.CharField(max_length=120, blank=True)
    logotipo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    logotipo_claro = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Versão para fundos escuros (opcional).",
    )
    favicon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Quadrado, pelo menos 512×512.",
    )
    cor_primaria = models.CharField("Cor principal", max_length=7, default="#111111", validators=[cor_hex])
    cor_destaque = models.CharField("Cor de destaque", max_length=7, default="#e4ff3a", validators=[cor_hex])
    cor_fundo = models.CharField("Cor de fundo", max_length=7, default="#ffffff", validators=[cor_hex])
    cor_texto = models.CharField("Cor do texto", max_length=7, default="#111111", validators=[cor_hex])
    fonte_titulos = models.CharField(max_length=20, choices=Fonte.choices, default=Fonte.INTER)
    fonte_texto = models.CharField(max_length=20, choices=Fonte.choices, default=Fonte.INTER)

    telefone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True, help_text="Com indicativo, ex.: +238 991 23 45")
    email = models.EmailField(blank=True, help_text="Recebe também as notificações de novos pedidos.")
    morada = models.CharField(max_length=200, blank=True)
    cidade = models.CharField(max_length=80, blank=True)
    mapa_url = models.URLField(
        "Mapa (URL de incorporação)",
        max_length=600,
        blank=True,
        help_text="Google Maps → Partilhar → Incorporar.",
    )
    horario_funcionamento = StreamField(
        [("intervalo", IntervaloBlock())],
        blank=True,
        use_json_field=True,
        verbose_name="Horário de funcionamento",
    )

    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    youtube = models.URLField(blank=True)

    identidade_panels = [
        FieldPanel("modelo"),
        FieldPanel("slogan"),
        FieldRowPanel([FieldPanel("logotipo"), FieldPanel("logotipo_claro"), FieldPanel("favicon")]),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("cor_primaria", widget=COR_WIDGET),
                        FieldPanel("cor_destaque", widget=COR_WIDGET),
                        FieldPanel("cor_fundo", widget=COR_WIDGET),
                        FieldPanel("cor_texto", widget=COR_WIDGET),
                    ]
                ),
                FieldRowPanel([FieldPanel("fonte_titulos"), FieldPanel("fonte_texto")]),
            ],
            heading="Cores e tipografia",
        ),
    ]
    contactos_panels = [
        FieldRowPanel([FieldPanel("telefone"), FieldPanel("whatsapp"), FieldPanel("email")]),
        FieldRowPanel([FieldPanel("morada"), FieldPanel("cidade")]),
        FieldPanel("mapa_url"),
        FieldPanel("horario_funcionamento"),
    ]
    redes_panels = [
        FieldPanel("instagram"),
        FieldPanel("facebook"),
        FieldPanel("tiktok"),
        FieldPanel("youtube"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(identidade_panels, heading="Identidade"),
            ObjectList(contactos_panels, heading="Contactos e horário"),
            ObjectList(redes_panels, heading="Redes sociais"),
        ]
    )

    class Meta:
        verbose_name = "Marca"


@register_setting(icon="search")
class SeoSettings(BaseSiteSetting):
    titulo_sufixo = models.CharField(
        "Sufixo dos títulos", max_length=60, blank=True, help_text="Acrescentado ao título de cada página."
    )
    descricao = models.CharField("Descrição por omissão", max_length=160, blank=True)
    imagem_partilha = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    indexar = models.BooleanField(
        "Permitir indexação", default=True, help_text="Desligar durante o onboarding."
    )
    google_verificacao = models.CharField("Google Search Console (código)", max_length=100, blank=True)
    plausible_dominio = models.CharField(
        "Plausible (domínio)", max_length=120, blank=True, help_text="Analítica sem cookies."
    )
    ga4_id = models.CharField(
        "Google Analytics 4 (ID)", max_length=30, blank=True, help_text="Só com consentimento."
    )

    panels = [
        FieldPanel("titulo_sufixo"),
        FieldPanel("descricao"),
        FieldPanel("imagem_partilha"),
        FieldPanel("indexar"),
        MultiFieldPanel(
            [FieldPanel("google_verificacao"), FieldPanel("plausible_dominio"), FieldPanel("ga4_id")],
            heading="Pesquisa e analítica",
        ),
    ]

    class Meta:
        verbose_name = "SEO e analítica"


TEXTO_CONSENTIMENTO = (
    "Autorizo o tratamento dos meus dados pessoais para ser contactado(a) sobre este pedido, "
    "nos termos da política de privacidade."
)


@register_setting(icon="lock")
class PrivacidadeSettings(BaseSiteSetting):
    responsavel = models.CharField("Responsável pelo tratamento", max_length=200, blank=True)
    email_privacidade = models.EmailField("Email para pedidos de dados", blank=True)
    texto_consentimento = models.TextField(default=TEXTO_CONSENTIMENTO)
    politica = RichTextField("Política de privacidade", blank=True)
    atualizada_em = models.DateField("Última atualização", null=True, blank=True)

    panels = [
        FieldRowPanel([FieldPanel("responsavel"), FieldPanel("email_privacidade")]),
        FieldPanel("texto_consentimento"),
        FieldPanel("politica"),
        FieldPanel("atualizada_em"),
    ]

    class Meta:
        verbose_name = "Privacidade (CNPD)"
