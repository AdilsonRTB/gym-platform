"""Regras de negócio da gestão de sócios: assinaturas, cobranças, check-in e lembretes."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.billing.models import Pagamento
from apps.billing.providers.base import InicioPagamento
from apps.billing.services import iniciar_pagamento_online
from apps.core.notifications import enviar_email, enviar_sms, enviar_whatsapp
from apps.tenants.models import Ginasio

from .models import Assinatura, CheckIn, Cobranca, GestaoSettings, Lembrete, Socio, somar_periodo

logger = logging.getLogger(__name__)


def config(ginasio: Ginasio) -> GestaoSettings:
    return GestaoSettings.for_site(ginasio.site)


# --------------------------------------------------------------------------- Sócios e assinaturas


def _descricao(plano, inicio: date, fim: date) -> str:
    if plano.periodicidade == "avulso":
        return f"{plano.nome} · {inicio:%d/%m/%Y}"
    return f"{plano.nome} · {inicio:%d/%m} a {fim:%d/%m/%Y}"


@transaction.atomic
def iniciar_assinatura(
    socio: Socio, plano, inicio: date | None = None, com_inscricao: bool = True
) -> Cobranca:
    """Nova assinatura (cancela a anterior) e a primeira cobrança, por pagar.

    A assinatura só fica válida quando a cobrança é paga: `data_fim` começa no dia anterior ao início.
    """
    inicio = inicio or timezone.localdate()
    socio.assinaturas.filter(estado=Assinatura.Estado.ATIVA).update(estado=Assinatura.Estado.CANCELADA)
    socio.cobrancas.filter(estado=Cobranca.Estado.PENDENTE).update(estado=Cobranca.Estado.ANULADA)
    assinatura = Assinatura.objects.create(
        ginasio_id=socio.ginasio_id,
        socio=socio,
        plano=plano,
        preco_cve=plano.preco_cve,
        data_inicio=inicio,
        data_fim=inicio - timedelta(days=1),
    )
    fim = somar_periodo(inicio, plano.periodicidade)
    taxa = plano.taxa_inscricao_cve if com_inscricao else 0
    return Cobranca.objects.create(
        ginasio_id=socio.ginasio_id,
        socio=socio,
        assinatura=assinatura,
        descricao=_descricao(plano, inicio, fim) + (" + inscrição" if taxa else ""),
        periodo_inicio=inicio,
        periodo_fim=fim,
        valor_cve=plano.preco_cve + taxa,
        vencimento=inicio,
    )


@transaction.atomic
def marcar_cobranca_paga(cobranca: Cobranca, quando: datetime | None = None) -> None:
    cobranca = Cobranca.todos.select_for_update().select_related("assinatura", "socio").get(pk=cobranca.pk)
    if cobranca.estado == Cobranca.Estado.PAGA:
        return
    cobranca.estado = Cobranca.Estado.PAGA
    cobranca.paga_em = quando or timezone.now()
    cobranca.save(update_fields=["estado", "paga_em"])
    assinatura = cobranca.assinatura
    assinatura.data_fim = max(assinatura.data_fim, cobranca.periodo_fim)
    assinatura.estado = Assinatura.Estado.ATIVA
    assinatura.save(update_fields=["data_fim", "estado"])
    if cobranca.socio.estado == Socio.Estado.INATIVO:
        cobranca.socio.estado = Socio.Estado.ATIVO
        cobranca.socio.save(update_fields=["estado"])


def socio_da_adesao(adesao) -> Socio:
    """Adesão paga no site → sócio (o existente com o mesmo email, ou um novo)."""
    socio = Socio.todos.filter(ginasio_id=adesao.ginasio_id, email__iexact=adesao.email).first()
    if socio is None:
        socio = Socio(
            ginasio_id=adesao.ginasio_id,
            nome=adesao.nome,
            email=adesao.email,
            telefone=adesao.telefone,
            nif=adesao.nif,
            morada=adesao.morada,
            consentimento=adesao.consentimento,
            consentimento_texto=adesao.consentimento_texto,
            consentimento_em=adesao.consentimento_em,
            ip=adesao.ip,
            user_agent=adesao.user_agent,
        )
        socio.save()
    return socio


def ao_confirmar_pagamento(pagamento: Pagamento) -> None:
    """Chamado dentro da transação que confirma um pagamento (sinal `pagamento_confirmado`)."""
    if pagamento.cobranca_id:
        marcar_cobranca_paga(pagamento.cobranca, pagamento.confirmado_em)
        return
    if pagamento.adesao_id:
        adesao = pagamento.adesao
        socio = socio_da_adesao(adesao)
        cobranca = iniciar_assinatura(socio, adesao.plano)
        cobranca.valor_cve = pagamento.valor_cve
        cobranca.save(update_fields=["valor_cve"])
        Pagamento.todos.filter(pk=pagamento.pk).update(socio=socio, cobranca=cobranca)
        pagamento.socio, pagamento.cobranca = socio, cobranca
        marcar_cobranca_paga(cobranca, pagamento.confirmado_em)


# --------------------------------------------------------------------------- Pagamentos de cobranças


def _novo_pagamento(cobranca: Cobranca, metodo: str, origem: str) -> Pagamento:
    socio = cobranca.socio
    return Pagamento(
        ginasio_id=cobranca.ginasio_id,
        socio=socio,
        cobranca=cobranca,
        origem=origem,
        metodo=metodo,
        valor_cve=cobranca.valor_cve,
        descricao=cobranca.descricao,
        nome_cliente=socio.nome,
        nif_cliente=socio.nif,
        email_cliente=socio.email,
    )


class CobrancaInvalida(Exception):
    pass


def pagar_na_rececao(cobranca: Cobranca, metodo: str) -> Pagamento:
    """Numerário, TPA ou transferência: o pagamento é confirmado e faturado de imediato."""
    if cobranca.estado != Cobranca.Estado.PENDENTE:
        raise CobrancaInvalida("Esta cobrança já não está por pagar.")
    if metodo not in {Pagamento.Metodo.NUMERARIO, Pagamento.Metodo.TPA, Pagamento.Metodo.TRANSFERENCIA}:
        raise CobrancaInvalida("Método de pagamento inválido.")
    pagamento = _novo_pagamento(cobranca, metodo, Pagamento.Origem.BALCAO)
    pagamento.save()  # o sinal post_save confirma e emite a fatura
    pagamento.refresh_from_db()
    return pagamento


def pagar_online(cobranca: Cobranca) -> InicioPagamento:
    """Pagamento na app do sócio (Vinti4Net quando a SISP estiver configurada)."""
    if cobranca.estado != Cobranca.Estado.PENDENTE:
        raise CobrancaInvalida("Esta cobrança já não está por pagar.")
    pagamento = _novo_pagamento(cobranca, Pagamento.Metodo.VINTI4, Pagamento.Origem.APP)
    pagamento.save()
    return iniciar_pagamento_online(pagamento)


# --------------------------------------------------------------------------- Check-in


@dataclass
class ResultadoCheckIn:
    permitido: bool
    motivo: str
    checkin: CheckIn | None
    duplicado: bool = False


def validar_socio(socio: Socio | None, dia: date, tolerancia: int) -> tuple[bool, str]:
    if socio is None:
        return False, "Cartão desconhecido"
    if socio.estado == Socio.Estado.SUSPENSO:
        return False, "Sócio suspenso"
    if socio.estado == Socio.Estado.INATIVO:
        return False, "Sócio inativo"
    assinatura = socio.assinatura_atual
    if assinatura is None:
        return False, "Sem assinatura ativa"
    if assinatura.data_fim >= dia:
        return True, "Assinatura válida"
    if assinatura.valida(dia, tolerancia):
        return True, "Mensalidade em atraso (dentro da tolerância)"
    return False, "Mensalidade em atraso"


def registar_checkin(
    ginasio: Ginasio,
    *,
    codigo: str | None = None,
    socio_id: int | None = None,
    momento: datetime | None = None,
    client_id=None,
    origem: str = CheckIn.Origem.QR,
    offline: bool = False,
    dispositivo: str = "",
    user=None,
) -> ResultadoCheckIn:
    """Valida e regista uma entrada. Idempotente por `client_id` (sincronização offline)."""
    if client_id:
        existente = CheckIn.todos.filter(ginasio=ginasio, client_id=client_id).first()
        if existente:
            return ResultadoCheckIn(existente.permitido, existente.motivo, existente, duplicado=True)

    socio = None
    if codigo:
        socio = Socio.todos.filter(ginasio=ginasio, codigo=codigo).first() if _uuid_valido(codigo) else None
    elif socio_id:
        socio = Socio.todos.filter(ginasio=ginasio, pk=socio_id).first()

    momento = momento or timezone.now()
    permitido, motivo = validar_socio(
        socio, timezone.localtime(momento).date(), config(ginasio).tolerancia_dias
    )
    try:
        with transaction.atomic():
            checkin = CheckIn.todos.create(
                ginasio=ginasio,
                socio=socio,
                momento=momento,
                origem=origem,
                permitido=permitido,
                motivo=motivo,
                offline=offline,
                dispositivo=dispositivo[:80],
                client_id=client_id,
                registado_por=user,
            )
    except IntegrityError:  # o mesmo client_id chegou em paralelo
        existente = CheckIn.todos.get(ginasio=ginasio, client_id=client_id)
        return ResultadoCheckIn(existente.permitido, existente.motivo, existente, duplicado=True)
    return ResultadoCheckIn(permitido, motivo, checkin)


def _uuid_valido(valor: str) -> bool:
    import uuid

    try:
        uuid.UUID(str(valor))
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- Tarefas diárias


def gerar_cobrancas(ginasio: Ginasio, hoje: date | None = None) -> int:
    """Cria a cobrança do período seguinte para assinaturas que estão a terminar."""
    hoje = hoje or timezone.localdate()
    cfg = config(ginasio)
    limite = hoje + timedelta(days=cfg.gerar_dias_antes)
    criadas = 0
    assinaturas = (
        Assinatura.todos.filter(ginasio=ginasio, estado=Assinatura.Estado.ATIVA, data_fim__lte=limite)
        .exclude(plano__periodicidade="avulso")
        .exclude(socio__estado=Socio.Estado.INATIVO)
        .select_related("plano", "socio")
    )
    for a in assinaturas:
        if a.cobrancas.filter(estado=Cobranca.Estado.PENDENTE).exists():
            continue
        inicio = a.data_fim + timedelta(days=1)
        fim = somar_periodo(inicio, a.plano.periodicidade)
        Cobranca.todos.create(
            ginasio=ginasio,
            socio=a.socio,
            assinatura=a,
            descricao=_descricao(a.plano, inicio, fim),
            periodo_inicio=inicio,
            periodo_fim=fim,
            valor_cve=a.preco_cve,
            vencimento=inicio,
        )
        criadas += 1
    return criadas


def _formatar(modelo: str, cobranca: Cobranca, ginasio: Ginasio) -> str:
    return modelo.format(
        nome=cobranca.socio.nome.split(" ")[0],
        valor=f"{cobranca.valor_cve:,}".replace(",", " "),
        vencimento=f"{cobranca.vencimento:%d/%m}",
        ginasio=ginasio.nome,
        link=ginasio.url_publico("/app"),
    )


def enviar(socio: Socio, mensagem: str, canal: str, assunto: str) -> list[str]:
    canais = []
    if canal in {"whatsapp", "todos"} and socio.telefone:
        enviar_whatsapp(socio.telefone, mensagem)
        canais.append("whatsapp")
    if canal in {"sms", "todos"} and socio.telefone:
        enviar_sms(socio.telefone, mensagem)
        canais.append("sms")
    if (canal in {"email", "todos"} or not canais) and socio.email:
        enviar_email(socio.email, assunto, mensagem)
        canais.append("email")
    return canais


def enviar_lembretes(ginasio: Ginasio, hoje: date | None = None) -> int:
    """Lembretes antes do vencimento e depois (1 e 7 dias de atraso). Nunca repete o mesmo lembrete."""
    hoje = hoje or timezone.localdate()
    cfg = config(ginasio)
    if not cfg.lembretes_ativos:
        return 0
    alvos = {
        Lembrete.Tipo.VENCIMENTO: (hoje + timedelta(days=cfg.lembrete_dias_antes), cfg.mensagem_vencimento),
        Lembrete.Tipo.ATRASO_1: (hoje - timedelta(days=1), cfg.mensagem_atraso),
        Lembrete.Tipo.ATRASO_7: (hoje - timedelta(days=7), cfg.mensagem_atraso),
    }
    enviados = 0
    for tipo, (vencimento, modelo) in alvos.items():
        cobrancas = Cobranca.todos.filter(
            ginasio=ginasio, estado=Cobranca.Estado.PENDENTE, vencimento=vencimento, socio__lembretes=True
        ).exclude(lembretes__tipo=tipo)
        for cobranca in cobrancas.select_related("socio"):
            mensagem = _formatar(modelo, cobranca, ginasio)
            canais = enviar(cobranca.socio, mensagem, cfg.canal, f"{ginasio.nome}: mensalidade")
            if not canais:
                continue
            try:
                Lembrete.todos.create(
                    ginasio=ginasio,
                    socio=cobranca.socio,
                    cobranca=cobranca,
                    tipo=tipo,
                    canais=",".join(canais),
                    mensagem=mensagem,
                )
                enviados += 1
            except IntegrityError:
                pass
    return enviados


def lembrete_manual(cobranca: Cobranca) -> Lembrete:
    ginasio = cobranca.ginasio
    cfg = config(ginasio)
    modelo = cfg.mensagem_atraso if cobranca.atrasada else cfg.mensagem_vencimento
    mensagem = _formatar(modelo, cobranca, ginasio)
    canais = enviar(cobranca.socio, mensagem, cfg.canal, f"{ginasio.nome}: mensalidade")
    return Lembrete.todos.create(
        ginasio=ginasio,
        socio=cobranca.socio,
        cobranca=cobranca,
        tipo=Lembrete.Tipo.MANUAL,
        canais=",".join(canais) or "nenhum",
        mensagem=mensagem,
    )
