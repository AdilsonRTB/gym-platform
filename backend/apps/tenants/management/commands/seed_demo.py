"""Cria três ginásios de demonstração (um por modelo de site) com conteúdo completo.

Uso: python manage.py seed_demo [--reset]
"""

import io
import random
from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFilter
from wagtail.images.models import Image
from wagtail.models import Page, Site

from apps.billing.models import ConfiguracaoFiscal, ConfiguracaoPagamentos
from apps.branding.models import MarcaSettings, PrivacidadeSettings, SeoSettings
from apps.content.models import (
    Aula,
    HomePage,
    Modalidade,
    PaginaGenerica,
    Pergunta,
    Plano,
    Testemunho,
    Treinador,
)
from apps.gestao.models import Assinatura, CheckIn, Cobranca, Socio, somar_periodo
from apps.gestao.services import iniciar_assinatura, marcar_cobranca_paga
from apps.tenants.context import using_ginasio
from apps.tenants.models import Dominio, Ginasio, Membro, Papel
from apps.tenants.permissions import sincronizar_grupos

SENHA_DEMO = "demo12345"

GINASIOS = [
    {
        "nome": "Força Praia",
        "slug": "forca",
        "nif": "250000001",
        "cidade": "Praia",
        "modelo": "essencial",
        "cores": ("#111111", "#d7ff3a", "#ffffff", "#111111"),
        "fontes": ("space-grotesk", "inter"),
        "paleta": ["#d7ff3a", "#111111", "#6b7280", "#e5e7eb"],
        "slogan": "Treino sério, ambiente leve.",
        "hero": (
            "Treina com propósito.",
            "Musculação, cross training e aulas de grupo no coração do Plateau.",
        ),
        "morada": "Av. Amílcar Cabral, 12 — Plateau",
        "telefone": "+238 261 00 00",
        "whatsapp": "+238 991 00 00",
    },
    {
        "nome": "Mindelo Fit Studio",
        "slug": "mindelo",
        "nif": "250000002",
        "cidade": "Mindelo",
        "modelo": "atelier",
        "cores": ("#1f3d36", "#e9b99a", "#f7f3ee", "#1c1917"),
        "fontes": ("fraunces", "manrope"),
        "paleta": ["#1f3d36", "#e9b99a", "#c9d6cf", "#f7f3ee"],
        "slogan": "Movimento consciente, junto ao mar.",
        "hero": (
            "Um estúdio para te sentires bem.",
            "Pilates, yoga e treino funcional em turmas pequenas, com acompanhamento próximo.",
        ),
        "morada": "Rua de Lisboa, 45 — Mindelo",
        "telefone": "+238 232 00 00",
        "whatsapp": "+238 992 00 00",
    },
    {
        "nome": "Sal Energy Club",
        "slug": "sal",
        "nif": "250000003",
        "cidade": "Santa Maria",
        "modelo": "energia",
        "cores": ("#ff5a1f", "#ff5a1f", "#0b0b0c", "#f5f5f4"),
        "fontes": ("archivo", "inter"),
        "paleta": ["#ff5a1f", "#0b0b0c", "#ff9f1c", "#2b2b2e"],
        "slogan": "Energia de ilha, todos os dias.",
        "hero": (
            "Supera o teu limite.",
            "Boxe, HIIT e spinning com a energia de Santa Maria. Aberto a residentes e visitantes.",
        ),
        "morada": "Rua 1.º de Junho — Santa Maria, Sal",
        "telefone": "+238 242 00 00",
        "whatsapp": "+238 993 00 00",
    },
]

MODALIDADES = {
    "forca": [
        ("Musculação", "Plano de treino individual e sala equipada.", "todos", 60),
        ("Cross Training", "Treino funcional de alta intensidade em grupo.", "intermedio", 50),
        ("Spinning", "Cardio em bicicleta ao ritmo da música.", "todos", 45),
        ("Treino Funcional", "Força, mobilidade e resistência para o dia a dia.", "iniciante", 50),
        ("Boxe Fitness", "Técnica de boxe sem contacto, muita energia.", "todos", 50),
        ("Alongamentos", "Recuperação ativa e mobilidade articular.", "iniciante", 30),
    ],
    "mindelo": [
        ("Pilates Clínico", "Postura, core e controlo em turmas até 8 pessoas.", "todos", 55),
        ("Yoga Vinyasa", "Fluxos dinâmicos ligados à respiração.", "intermedio", 60),
        ("Yoga Suave", "Prática calma para todas as idades.", "iniciante", 60),
        ("Funcional", "Força e condição física com pouco material.", "todos", 45),
        ("Barre", "Inspirado no ballet, para tonificar com leveza.", "todos", 45),
        ("Meditação", "Pausa guiada de respiração e foco.", "iniciante", 30),
    ],
    "sal": [
        ("HIIT", "Intervalos de alta intensidade em 40 minutos.", "avancado", 40),
        ("Boxe", "Técnica, sacos e trabalho de pés.", "todos", 60),
        ("Spinning", "Subidas, sprints e muita música.", "todos", 45),
        ("Musculação", "Sala completa com vista para o mar.", "todos", 60),
        ("Kickboxing", "Combinações de braços e pernas em circuito.", "intermedio", 50),
        ("Mobilidade", "Para recuperar depois de um dia de praia ou kite.", "iniciante", 30),
    ],
}

TREINADORES = {
    "forca": [
        ("Carla Semedo", "Treinadora principal", "Musculação, Força, Nutrição desportiva"),
        ("Hélder Tavares", "Coach de Cross Training", "Cross Training, Levantamento olímpico"),
        ("Nádia Lopes", "Instrutora de grupo", "Spinning, Funcional"),
        ("Rui Fortes", "Treinador", "Boxe, Condição física"),
    ],
    "mindelo": [
        ("Inês Duarte", "Fundadora · Fisioterapeuta", "Pilates clínico, Reabilitação"),
        ("Tomás Andrade", "Professor de yoga", "Vinyasa, Meditação"),
        ("Sara Évora", "Instrutora", "Barre, Funcional"),
    ],
    "sal": [
        ("Mickael Silva", "Head coach", "HIIT, Boxe, Kickboxing"),
        ("Jéssica Ramos", "Instrutora", "Spinning, Mobilidade"),
        ("Paulo Brito", "Personal trainer", "Musculação, Emagrecimento"),
        ("Aline Monteiro", "Treinadora", "Boxe, Funcional"),
    ],
}

PLANOS = [
    (
        "Aula avulsa",
        "Para experimentar ou treinar de passagem.",
        500,
        "avulso",
        0,
        ["Acesso a uma aula ou sala", "Sem compromisso"],
        False,
    ),
    (
        "Mensal",
        "Acesso livre à sala e a todas as aulas.",
        3500,
        "mensal",
        1000,
        ["Sala e aulas de grupo ilimitadas", "Avaliação física inicial", "Plano de treino personalizado"],
        True,
    ),
    (
        "Trimestral",
        "Compromisso de 3 meses com melhor preço.",
        9500,
        "trimestral",
        0,
        ["Tudo do plano mensal", "Sem taxa de inscrição", "1 sessão de personal trainer"],
        False,
    ),
    (
        "Anual",
        "O melhor valor para quem treina todo o ano.",
        33000,
        "anual",
        0,
        ["Tudo do plano trimestral", "2 meses oferta", "Congelamento até 30 dias"],
        False,
    ),
]

TESTEMUNHOS = [
    (
        "Em seis meses mudei a forma como me sinto no dia a dia. A equipa conhece-me pelo nome e isso faz toda a diferença.",
        "Ana Rodrigues",
        "Sócia desde 2024",
    ),
    (
        "O horário flexível encaixa na minha vida. Treino antes do trabalho e saio cheio de energia.",
        "Djamilson Pires",
        "Sócio desde 2023",
    ),
    (
        "Aulas cheias de energia e treinadores que corrigem com cuidado. Recomendo a toda a gente.",
        "Marisa Fonseca",
        "Sócia desde 2025",
    ),
]

PERGUNTAS = [
    (
        "Posso experimentar antes de me inscrever?",
        "Sim. A primeira aula experimental é gratuita — basta marcar pelo formulário ou por WhatsApp.",
    ),
    (
        "Como posso pagar a mensalidade?",
        "Online com cartão Vinti4, ou na receção em numerário, TPA ou transferência. A fatura é emitida automaticamente.",
    ),
    (
        "Preciso de levar alguma coisa?",
        "Roupa confortável, uma toalha e uma garrafa de água. Temos balneários com duche.",
    ),
    (
        "Há acompanhamento para iniciantes?",
        "Sim. Todos os planos incluem avaliação física e um plano de treino adaptado ao teu nível.",
    ),
    (
        "Posso congelar o meu plano?",
        "Nos planos trimestral e anual podes congelar em caso de viagem ou lesão. Fala connosco na receção.",
    ),
]

HORARIO_BASE = [
    (time(7, 0), time(7, 50)),
    (time(12, 30), time(13, 15)),
    (time(18, 0), time(18, 50)),
    (time(19, 15), time(20, 5)),
]

POLITICA = """
<h3>Quem somos</h3><p>{nome} é o responsável pelo tratamento dos dados pessoais recolhidos neste site.</p>
<h3>Que dados recolhemos</h3><p>Nome, contactos e a informação que nos envia nos formulários de contacto, aula experimental e adesão.
Nos pagamentos online, os dados do cartão são tratados diretamente pela SISP e nunca chegam até nós.</p>
<h3>Para que usamos os dados</h3><ul><li>Responder aos seus pedidos</li><li>Gerir a sua adesão e pagamentos</li>
<li>Emitir faturas, conforme a lei fiscal</li></ul>
<h3>Os seus direitos</h3><p>Pode pedir acesso, correção ou eliminação dos seus dados a qualquer momento, nos termos da lei de proteção
de dados pessoais de Cabo Verde (CNPD). As faturas são conservadas pelo prazo legal.</p>
"""


# --------------------------------------------------------------------------- Imagens geradas


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def gerar_imagem(titulo: str, paleta: list[str], largura=1600, altura=1100, seed=0) -> Image:
    """Composição abstrata (gradiente com formas desfocadas e grão) nas cores da marca."""
    rnd = random.Random(seed)
    base = PILImage.new("RGB", (largura, altura), _hex(paleta[-1]))
    camada = PILImage.new("RGB", (largura, altura), _hex(paleta[-1]))
    draw = ImageDraw.Draw(camada)
    for i in range(6):
        cor = _hex(paleta[i % len(paleta)])
        r = rnd.randint(int(altura * 0.25), int(altura * 0.6))
        x, y = rnd.randint(-r // 2, largura), rnd.randint(-r // 2, altura)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=cor)
    camada = camada.filter(ImageFilter.GaussianBlur(radius=altura // 7))
    base = PILImage.blend(base, camada, 0.95)
    grao = PILImage.effect_noise((largura, altura), 18).convert("RGB")
    base = PILImage.blend(base, grao, 0.06)
    buffer = io.BytesIO()
    base.save(buffer, format="JPEG", quality=86)
    return buffer


def criar_imagem(ginasio, titulo, paleta, seed, **kwargs) -> Image:
    buffer = gerar_imagem(titulo, paleta, seed=seed, **kwargs)
    nome = f"{ginasio.slug}-{seed}.jpg"
    img = Image(title=titulo, collection=ginasio.colecao, description=titulo)
    img.file = ImageFile(buffer, name=nome)
    img.save()
    return img


# --------------------------------------------------------------------------- Sócios

NOMES = [
    "Ana Tavares",
    "Bruno Semedo",
    "Carla Lopes",
    "Dário Fortes",
    "Elisa Monteiro",
    "Fábio Gomes",
    "Graça Varela",
    "Hélio Furtado",
    "Inês Rocha",
    "Jailson Silva",
    "Katia Moreira",
    "Leandro Pina",
    "Mariana Barros",
    "Nelson Cabral",
    "Odete Andrade",
    "Paulo Évora",
    "Quintino Dias",
    "Rosa Spencer",
    "Sandro Brito",
    "Telma Correia",
    "Ulisses Neves",
    "Vera Duarte",
    "Wilson Soares",
    "Yara Fonseca",
    "Zeca Ramos",
    "Adilsa Pires",
    "Benvindo Lima",
    "Cristina Mendes",
    "Daniel Vaz",
    "Edna Santos",
    "Filipe Teixeira",
    "Gilda Carvalho",
    "Hugo Delgado",
    "Isa Brito",
    "João Almeida",
    "Luísa Veiga",
]


def criar_socios(ginasio, seed=0) -> int:
    """Sócios com assinaturas em vários estados (em dia, a vencer, em atraso) e check-ins."""
    from datetime import datetime, timedelta

    from django.utils import timezone

    rnd = random.Random(seed)
    hoje = timezone.localdate()
    planos = list(Plano.objects.filter(live=True).exclude(periodicidade="avulso"))
    mensal = next(p for p in planos if p.periodicidade == "mensal")
    for n, nome in enumerate(NOMES):
        socio = Socio(
            nome=nome,
            email=f"{nome.split()[0].lower()}.{nome.split()[-1].lower()}@exemplo.cv",
            telefone=f"+238 9{rnd.randint(10, 99)} {rnd.randint(10, 99)} {rnd.randint(10, 99)}",
            consentimento=True,
            consentimento_texto="Consentimento recolhido na receção (demonstração).",
            consentimento_em=timezone.now(),
        )
        socio.save()
        plano = mensal if n % 4 else rnd.choice(planos)
        # Início entre 20 e 400 dias atrás; alguns com a última mensalidade por pagar.
        inicio = hoje - timedelta(days=rnd.randint(20, 400))
        cobranca = iniciar_assinatura(socio, plano, inicio=inicio)
        while True:
            em_atraso = n % 7 == 3 and cobranca.periodo_fim >= hoje - timedelta(days=10)
            if em_atraso:
                break
            pagamento_em = timezone.make_aware(datetime.combine(cobranca.vencimento, datetime.min.time()))
            marcar_cobranca_paga(cobranca, pagamento_em)
            a = Assinatura.objects.get(pk=cobranca.assinatura_id)
            if a.data_fim >= hoje + timedelta(days=rnd.randint(0, 25)):
                break
            cobranca = Cobranca.objects.create(
                socio=socio,
                assinatura=a,
                descricao=f"{plano.nome} · {a.data_fim + timedelta(days=1):%d/%m}",
                periodo_inicio=a.data_fim + timedelta(days=1),
                periodo_fim=somar_periodo(a.data_fim + timedelta(days=1), plano.periodicidade),
                valor_cve=plano.preco_cve,
                vencimento=a.data_fim + timedelta(days=1),
            )
        if n == len(NOMES) - 1:
            socio.estado = Socio.Estado.SUSPENSO
            socio.save(update_fields=["estado"])
        # Check-ins nos últimos 14 dias
        for d in range(14):
            if rnd.random() < 0.45:
                dia = hoje - timedelta(days=d)
                hora = rnd.choice([6, 7, 7, 8, 12, 12, 13, 17, 18, 18, 19, 19, 20])
                momento = timezone.make_aware(
                    datetime(dia.year, dia.month, dia.day, hora, rnd.randint(0, 59))
                )
                if momento > timezone.now():
                    continue
                CheckIn.objects.create(
                    socio=socio, momento=momento, permitido=True, motivo="Assinatura válida"
                )
    return len(NOMES)


def garantir_treinador(ginasio, User) -> None:
    """Conta `treinador@<slug>.cv` ligada ao primeiro perfil de treinador (idempotente)."""
    email = f"treinador@{ginasio.slug}.cv"
    user, criado = User.objects.get_or_create(username=email, defaults={"email": email})
    with using_ginasio(ginasio):
        perfil = Treinador.objects.order_by("ordem", "pk").first()
    if criado:
        user.first_name = perfil.nome.split()[0] if perfil else "Treinador"
        user.set_password(SENHA_DEMO)
        user.save()
    Membro.objects.get_or_create(user=user, ginasio=ginasio, defaults={"papel": Papel.TREINADOR})
    if perfil and perfil.user_id != user.pk:
        # Pela revisão, para a ligação não se perder na próxima publicação feita no Admin.
        perfil.user = user
        perfil.save_revision().publish()


# --------------------------------------------------------------------------- Comando


class Command(BaseCommand):
    help = "Cria ginásios de demonstração com conteúdo completo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Apaga os ginásios de demonstração primeiro."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if options["reset"]:
            for dados in GINASIOS:
                g = Ginasio.objects.filter(slug=dados["slug"]).first()
                if g:
                    site = g.site
                    root = site.root_page if site else None
                    g.delete()
                    if site:
                        site.delete()
                    if root:
                        root.delete()

        # A página e o site de boas-vindas do Wagtail não são usados.
        Site.objects.filter(hostname="localhost", port=80, ginasio__isnull=True).delete()
        Page.objects.filter(depth=2, slug="home", content_type__model="page").delete()

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@plataforma.local", "admin")
            self.stdout.write("Superutilizador: admin / admin")

        for i, dados in enumerate(GINASIOS):
            if Ginasio.objects.filter(slug=dados["slug"]).exists():
                self.stdout.write(f"· {dados['nome']} já existe (use --reset para recriar)")
            else:
                self.criar_ginasio(dados, i, User)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {dados['nome']} → http://{dados['slug']}.localhost:3100")
                )
            ginasio = Ginasio.objects.select_related("site", "colecao").get(slug=dados["slug"])
            sincronizar_grupos(ginasio)
            garantir_treinador(ginasio, User)
            if not Socio.todos.filter(ginasio=ginasio).exists():
                with using_ginasio(ginasio):
                    n = criar_socios(ginasio, seed=i)
                self.stdout.write(f"  {n} sócios de demonstração")

    def criar_ginasio(self, d, indice, User):
        ginasio = Ginasio.objects.create(
            nome=d["nome"], slug=d["slug"], nif=d["nif"], estado=Ginasio.Estado.ATIVO, plano_plataforma="pro"
        )  # o sinal post_save provisiona Site, página inicial, coleção e grupos
        ginasio.refresh_from_db()
        site = ginasio.site
        paleta = d["paleta"]

        with using_ginasio(ginasio):
            # Equipa
            for papel, prefixo in (
                (Papel.DONO, "dono"),
                (Papel.GESTOR, "gestor"),
                (Papel.RECECIONISTA, "rececao"),
            ):
                email = f"{prefixo}@{d['slug']}.cv"
                user, created = User.objects.get_or_create(
                    username=email, defaults={"email": email, "first_name": prefixo.capitalize()}
                )
                if created:
                    user.set_password(SENHA_DEMO)
                    user.save()
                Membro.objects.get_or_create(user=user, ginasio=ginasio, defaults={"papel": papel})

            # Imagens
            hero = criar_imagem(ginasio, f"{d['nome']} — espaço", paleta, seed=indice * 100 + 1)
            galeria = [
                criar_imagem(
                    ginasio,
                    f"{d['nome']} — galeria {n}",
                    paleta[n % 2 :] + paleta[: n % 2],
                    seed=indice * 100 + 10 + n,
                    largura=1200,
                    altura=900,
                )
                for n in range(4)
            ]
            partilha = criar_imagem(
                ginasio, f"{d['nome']} — partilha", paleta, seed=indice * 100 + 5, largura=1200, altura=630
            )

            # Marca, SEO, privacidade, pagamentos e faturação
            primaria, destaque, fundo, texto = d["cores"]
            MarcaSettings.objects.update_or_create(
                site=site,
                defaults=dict(
                    modelo=d["modelo"],
                    slogan=d["slogan"],
                    cor_primaria=primaria,
                    cor_destaque=destaque,
                    cor_fundo=fundo,
                    cor_texto=texto,
                    fonte_titulos=d["fontes"][0],
                    fonte_texto=d["fontes"][1],
                    telefone=d["telefone"],
                    whatsapp=d["whatsapp"],
                    email=f"geral@{d['slug']}.cv",
                    morada=d["morada"],
                    cidade=d["cidade"],
                    mapa_url="",
                    horario_funcionamento=[
                        ("intervalo", {"dias": "Segunda a sexta", "horas": "06:00 – 22:00"}),
                        ("intervalo", {"dias": "Sábado", "horas": "08:00 – 18:00"}),
                        ("intervalo", {"dias": "Domingo e feriados", "horas": "09:00 – 13:00"}),
                    ],
                    instagram=f"https://instagram.com/{d['slug']}.cv",
                    facebook=f"https://facebook.com/{d['slug']}.cv",
                ),
            )
            SeoSettings.objects.update_or_create(
                site=site,
                defaults=dict(
                    titulo_sufixo=d["nome"],
                    descricao=f"{d['slogan']} Ginásio em {d['cidade']}, Cabo Verde.",
                    imagem_partilha=partilha,
                    indexar=True,
                ),
            )
            PrivacidadeSettings.objects.update_or_create(
                site=site,
                defaults=dict(
                    responsavel=d["nome"],
                    email_privacidade=f"privacidade@{d['slug']}.cv",
                    politica=POLITICA.format(nome=d["nome"]),
                    atualizada_em=date(2026, 9, 1),
                ),
            )
            ConfiguracaoPagamentos.objects.update_or_create(site=site, defaults={"fornecedor": "simulado"})
            ConfiguracaoFiscal.objects.update_or_create(
                site=site,
                defaults=dict(
                    fornecedor="simulado",
                    nif=d["nif"],
                    nome_fiscal=d["nome"] + ", Lda.",
                    morada_fiscal=d["morada"],
                    serie="FT",
                ),
            )

            # Snippets
            modalidades = []
            for n, (nome, resumo, nivel, duracao) in enumerate(MODALIDADES[d["slug"]]):
                img = criar_imagem(
                    ginasio,
                    nome,
                    paleta[n % len(paleta) :] + paleta[: n % len(paleta)],
                    seed=indice * 100 + 30 + n,
                    largura=1200,
                    altura=900,
                )
                m = Modalidade(
                    nome=nome,
                    resumo=resumo,
                    descricao=f"<p>{resumo} Aulas orientadas por treinadores certificados, adaptadas a cada nível.</p>"
                    "<h3>Para quem é</h3><p>Para quem quer treinar com acompanhamento e ver resultados de forma consistente.</p>"
                    "<h3>O que levar</h3><ul><li>Roupa confortável</li><li>Toalha</li><li>Água</li></ul>",
                    imagem=img,
                    nivel=nivel,
                    duracao_min=duracao,
                    ordem=n,
                )
                m.save()
                m.save_revision().publish()
                modalidades.append(m)

            treinadores = []
            for n, (nome, cargo, esp) in enumerate(TREINADORES[d["slug"]]):
                t = Treinador(
                    nome=nome,
                    cargo=cargo,
                    especialidades=esp,
                    biografia=f"{nome.split()[0]} treina há mais de 8 anos e acredita que o melhor treino é aquele que se consegue manter.",
                    instagram=nome.split()[0].lower(),
                    ordem=n,
                )
                t.save()
                t.modalidades.set(modalidades[n : n + 2] or modalidades[:1])
                t.save_revision().publish()
                treinadores.append(t)

            for n, (nome, desc, preco, per, taxa, beneficios, destaque_) in enumerate(PLANOS):
                p = Plano(
                    nome=nome,
                    descricao=desc,
                    preco_cve=preco,
                    periodicidade=per,
                    taxa_inscricao_cve=taxa,
                    beneficios="\n".join(beneficios),
                    destaque=destaque_,
                    ordem=n,
                )
                p.save()
                p.save_revision().publish()

            rnd = random.Random(indice)
            for dia in range(6):
                for k, (inicio, fim) in enumerate(HORARIO_BASE):
                    if dia == 5 and k > 1:
                        continue
                    m = modalidades[(dia + k) % len(modalidades)]
                    a = Aula(
                        modalidade=m,
                        dia_semana=dia,
                        hora_inicio=inicio,
                        hora_fim=fim,
                        treinador=treinadores[(dia + k) % len(treinadores)],
                        sala=rnd.choice(["Estúdio 1", "Estúdio 2", "Sala principal"]),
                        lotacao=rnd.choice([12, 16, 20]),
                    )
                    a.save()
                    a.save_revision().publish()

            for n, (texto_, autor, detalhe) in enumerate(TESTEMUNHOS):
                t = Testemunho(texto=texto_, autor=autor, detalhe=detalhe, ordem=n)
                t.save()
                t.save_revision().publish()
            for n, (pergunta, resposta) in enumerate(PERGUNTAS):
                q = Pergunta(pergunta=pergunta, resposta=resposta, ordem=n)
                q.save()
                q.save_revision().publish()

            # Páginas
            home = site.root_page.specific
            assert isinstance(home, HomePage)
            titulo, subtitulo = d["hero"]
            home.title = d["nome"]
            home.seo_title = f"{d['nome']} — ginásio em {d['cidade']}"
            home.search_description = f"{d['slogan']} Planos desde 500 CVE. Marca a tua aula experimental."
            home.corpo = [
                (
                    "hero",
                    {
                        "etiqueta": f"Ginásio em {d['cidade']}",
                        "titulo": titulo,
                        "subtitulo": subtitulo,
                        "imagem": hero,
                        "botao": {
                            "texto": "Aula experimental grátis",
                            "link": "/contactos?tipo=aula_experimental",
                        },
                        "botao_secundario": {"texto": "Ver planos", "link": "/planos"},
                        "variante": "fundo" if d["modelo"] == "energia" else "dividido",
                    },
                ),
                (
                    "numeros",
                    {
                        "itens": [
                            {"valor": "1200+", "rotulo": "sócios ativos"},
                            {"valor": f"{len(modalidades)}", "rotulo": "modalidades"},
                            {"valor": "40+", "rotulo": "aulas por semana"},
                            {"valor": "7/7", "rotulo": "dias abertos"},
                        ]
                    },
                ),
                (
                    "destaques",
                    {
                        "titulo": "Tudo o que precisas para treinar bem",
                        "subtitulo": "Um espaço pensado para evoluíres ao teu ritmo, com acompanhamento de verdade.",
                        "itens": [
                            {
                                "icone": "pessoas",
                                "titulo": "Treinadores presentes",
                                "texto": "Acompanhamento em sala durante todo o horário.",
                            },
                            {
                                "icone": "relogio",
                                "titulo": "Horário alargado",
                                "texto": "Das 6h às 22h nos dias úteis, também ao fim de semana.",
                            },
                            {
                                "icone": "coracao",
                                "titulo": "Avaliação física",
                                "texto": "Começa com uma avaliação e um plano à tua medida.",
                            },
                            {
                                "icone": "escudo",
                                "titulo": "Pagamento simples",
                                "texto": "Vinti4 online ou na receção, com fatura automática.",
                            },
                        ],
                    },
                ),
                (
                    "modalidades",
                    {"titulo": "Modalidades", "subtitulo": "Encontra o treino certo para ti.", "limite": 6},
                ),
                ("horario", {"titulo": "Aulas de hoje", "subtitulo": ""}),
                (
                    "planos",
                    {
                        "titulo": "Planos simples, sem surpresas",
                        "subtitulo": "Preços em escudos, fatura sempre incluída.",
                    },
                ),
                ("testemunhos", {"titulo": "Quem treina connosco", "subtitulo": ""}),
                (
                    "galeria",
                    {"titulo": "O espaço", "imagens": [{"imagem": img, "legenda": ""} for img in galeria]},
                ),
                ("faq", {"titulo": "Perguntas frequentes", "subtitulo": ""}),
                (
                    "cta",
                    {
                        "titulo": "A primeira aula é por nossa conta.",
                        "texto": "Marca a tua aula experimental e conhece o espaço sem compromisso.",
                        "botao": {
                            "texto": "Marcar aula experimental",
                            "link": "/contactos?tipo=aula_experimental",
                        },
                        "estilo": "marca",
                    },
                ),
            ]
            home.imagem_partilha = partilha
            home.save_revision().publish()

            sobre = PaginaGenerica(
                title="Sobre nós",
                slug="sobre",
                show_in_menus=True,
                search_description=f"A história de {d['nome']}.",
                corpo=[
                    (
                        "hero",
                        {
                            "etiqueta": "Sobre nós",
                            "titulo": f"{d['nome']} nasceu para tornar o treino acessível.",
                            "subtitulo": "Somos uma equipa local, apaixonada por movimento e por pessoas.",
                            "imagem": None,
                            "botao": {"texto": "", "link": ""},
                            "botao_secundario": {"texto": "", "link": ""},
                            "variante": "centrado",
                        },
                    ),
                    (
                        "imagem_texto",
                        {
                            "imagem": galeria[0],
                            "titulo": "Um espaço à tua medida",
                            "corpo": "<p>Abrimos portas em 2019 com uma ideia simples: um ginásio onde toda a gente se sente "
                            "bem-vinda. Hoje somos mais de mil sócios, mas continuamos a conhecer cada um pelo nome.</p>",
                            "botao": {"texto": "Conhece a equipa", "link": "/equipa"},
                            "imagem_a_direita": False,
                        },
                    ),
                    (
                        "texto",
                        {
                            "titulo": "O que nos move",
                            "corpo": "<p>Treino com método, ambiente positivo e preços justos. Investimos em equipamento de "
                            "qualidade e na formação contínua dos nossos treinadores.</p>",
                        },
                    ),
                    ("equipa", {"titulo": "A equipa", "subtitulo": ""}),
                ],
            )
            home.add_child(instance=sobre)
            sobre.save_revision().publish()

        Dominio.objects.filter(ginasio=ginasio).update(verificado=True)
