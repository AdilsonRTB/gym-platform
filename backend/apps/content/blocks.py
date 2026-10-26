"""Blocos do StreamField: o contrato entre o Admin e o site.

Cada bloco novo exige o componente correspondente em `site/src/components/blocks`.
Os blocos "dinâmicos" (planos, modalidades, equipa, testemunhos, FAQ) incluem na API os dados
atuais dos snippets, para o gestor editar o conteúdo num só sítio.
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from .images import imagem_api


class ImagemBlock(ImageChooserBlock):
    def get_api_representation(self, value, context=None):
        return imagem_api(value)


class LinkBlock(blocks.StructBlock):
    texto = blocks.CharBlock(required=False, max_length=40)
    link = blocks.CharBlock(
        required=False, help_text="Caminho do site (ex.: /planos) ou endereço completo (https://…)."
    )

    class Meta:
        icon = "link"
        label = "Botão"


class HeroBlock(blocks.StructBlock):
    etiqueta = blocks.CharBlock(required=False, max_length=60, help_text="Texto pequeno por cima do título.")
    titulo = blocks.CharBlock(max_length=120)
    subtitulo = blocks.TextBlock(required=False, max_length=280)
    imagem = ImagemBlock(required=False)
    botao = LinkBlock(required=False)
    botao_secundario = LinkBlock(required=False)
    variante = blocks.ChoiceBlock(
        choices=[
            ("dividido", "Texto e imagem lado a lado"),
            ("fundo", "Imagem de fundo"),
            ("centrado", "Centrado"),
        ],
        default="dividido",
    )

    class Meta:
        icon = "pick"
        label = "Hero"


class TextoBlock(blocks.StructBlock):
    titulo = blocks.CharBlock(required=False, max_length=120)
    corpo = blocks.RichTextBlock(features=["h3", "bold", "italic", "link", "ol", "ul"])

    class Meta:
        icon = "doc-full"
        label = "Texto"


class ImagemTextoBlock(blocks.StructBlock):
    imagem = ImagemBlock()
    titulo = blocks.CharBlock(max_length=120)
    corpo = blocks.RichTextBlock(features=["bold", "italic", "link", "ul"])
    botao = LinkBlock(required=False)
    imagem_a_direita = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "image"
        label = "Imagem e texto"


class CTABlock(blocks.StructBlock):
    titulo = blocks.CharBlock(max_length=120)
    texto = blocks.TextBlock(required=False, max_length=280)
    botao = LinkBlock()
    estilo = blocks.ChoiceBlock(choices=[("marca", "Cor da marca"), ("suave", "Suave")], default="marca")

    class Meta:
        icon = "pick"
        label = "Chamada para ação"


class DestaqueItemBlock(blocks.StructBlock):
    icone = blocks.ChoiceBlock(
        choices=[
            ("haltere", "Haltere"),
            ("coracao", "Coração"),
            ("relogio", "Relógio"),
            ("pessoas", "Pessoas"),
            ("estrela", "Estrela"),
            ("raio", "Energia"),
            ("escudo", "Segurança"),
            ("folha", "Bem-estar"),
        ],
        default="haltere",
    )
    titulo = blocks.CharBlock(max_length=60)
    texto = blocks.TextBlock(required=False, max_length=200)


class DestaquesBlock(blocks.StructBlock):
    titulo = blocks.CharBlock(required=False, max_length=120)
    subtitulo = blocks.TextBlock(required=False, max_length=280)
    itens = blocks.ListBlock(DestaqueItemBlock(), min_num=1, max_num=8)

    class Meta:
        icon = "list-ul"
        label = "Destaques"


class EstatisticasBlock(blocks.StructBlock):
    itens = blocks.ListBlock(
        blocks.StructBlock(
            [("valor", blocks.CharBlock(max_length=12)), ("rotulo", blocks.CharBlock(max_length=40))]
        ),
        min_num=1,
        max_num=4,
    )

    class Meta:
        icon = "order"
        label = "Números"


class GaleriaBlock(blocks.StructBlock):
    titulo = blocks.CharBlock(required=False, max_length=120)
    imagens = blocks.ListBlock(
        blocks.StructBlock(
            [("imagem", ImagemBlock()), ("legenda", blocks.CharBlock(required=False, max_length=120))]
        ),
        min_num=1,
    )

    class Meta:
        icon = "image"
        label = "Galeria"


class BlocoDinamico(blocks.StructBlock):
    """Bloco cujo conteúdo vem dos snippets do ginásio."""

    titulo = blocks.CharBlock(required=False, max_length=120)
    subtitulo = blocks.TextBlock(required=False, max_length=280)

    def itens(self, value, context):  # pragma: no cover - implementado nas subclasses
        return []

    def get_api_representation(self, value, context=None):
        data = super().get_api_representation(value, context)
        data["itens"] = self.itens(value, context)
        return data


class PlanosBlock(BlocoDinamico):
    def itens(self, value, context):
        from apps.api.serializers import PlanoSerializer

        from .models import Plano

        return PlanoSerializer(Plano.objects.filter(live=True), many=True).data

    class Meta:
        icon = "tag"
        label = "Planos (automático)"


class ModalidadesBlock(BlocoDinamico):
    limite = blocks.IntegerBlock(required=False, min_value=1, max_value=12, default=6)

    def itens(self, value, context):
        from apps.api.serializers import ModalidadeResumoSerializer

        from .models import Modalidade

        qs = Modalidade.objects.filter(live=True)
        return ModalidadeResumoSerializer(qs[: value.get("limite") or 6], many=True).data

    class Meta:
        icon = "list-ul"
        label = "Modalidades (automático)"


class EquipaBlock(BlocoDinamico):
    def itens(self, value, context):
        from apps.api.serializers import TreinadorSerializer

        from .models import Treinador

        return TreinadorSerializer(Treinador.objects.filter(live=True), many=True).data

    class Meta:
        icon = "group"
        label = "Equipa (automático)"


class TestemunhosBlock(BlocoDinamico):
    def itens(self, value, context):
        from apps.api.serializers import TestemunhoSerializer

        from .models import Testemunho

        return TestemunhoSerializer(Testemunho.objects.filter(live=True), many=True).data

    class Meta:
        icon = "openquote"
        label = "Testemunhos (automático)"


class FAQBlock(BlocoDinamico):
    def itens(self, value, context):
        from apps.api.serializers import PerguntaSerializer

        from .models import Pergunta

        return PerguntaSerializer(Pergunta.objects.filter(live=True), many=True).data

    class Meta:
        icon = "help"
        label = "Perguntas frequentes (automático)"


class HorarioBlock(BlocoDinamico):
    """Resumo do horário de hoje com ligação para /horario."""

    def itens(self, value, context):
        from apps.api.serializers import AulaSerializer

        from .models import Aula

        qs = Aula.objects.filter(live=True).select_related("modalidade", "treinador")
        return AulaSerializer(qs, many=True).data

    class Meta:
        icon = "time"
        label = "Horário (atalho)"


class BlocosPagina(blocks.StreamBlock):
    hero = HeroBlock()
    texto = TextoBlock()
    imagem_texto = ImagemTextoBlock()
    destaques = DestaquesBlock()
    numeros = EstatisticasBlock()
    cta = CTABlock()
    galeria = GaleriaBlock()
    planos = PlanosBlock()
    modalidades = ModalidadesBlock()
    equipa = EquipaBlock()
    testemunhos = TestemunhosBlock()
    faq = FAQBlock()
    horario = HorarioBlock()
