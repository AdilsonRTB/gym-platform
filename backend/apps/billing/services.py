"""Fluxo de adesão: pedido → pagamento → confirmação → fatura → notificações."""

import logging
import secrets

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.branding.models import MarcaSettings
from apps.core.notifications import enviar_email, enviar_whatsapp
from apps.tenants.models import Ginasio

from .models import Adesao, Fatura, Pagamento
from .providers.base import InicioPagamento, ResultadoPagamento
from .providers.registry import fornecedor_faturacao, fornecedor_pagamento
from .signals import pagamento_confirmado

logger = logging.getLogger(__name__)


class PagamentoIndisponivel(Exception):
    pass


def _referencia() -> str:
    return f"A{timezone.now():%y%m%d}{secrets.randbelow(10**8):08d}"  # 15 caracteres (limite SISP)


def url_retorno(pagamento: Pagamento) -> str:
    return (
        f"{settings.API_PUBLIC_URL.rstrip('/')}/pagamentos/{pagamento.fornecedor}/retorno/{pagamento.uuid}/"
    )


@transaction.atomic
def iniciar_adesao(
    ginasio: Ginasio, plano, dados: dict, consentimento: dict
) -> tuple[Adesao, InicioPagamento]:
    fornecedor = fornecedor_pagamento(ginasio)
    if fornecedor is None:
        raise PagamentoIndisponivel("Este ginásio ainda não aceita pagamentos online.")
    adesao = Adesao.objects.create(
        ginasio=ginasio, plano=plano, valor_cve=plano.total_adesao_cve, **dados, **consentimento
    )
    pagamento = Pagamento.objects.create(
        ginasio=ginasio,
        adesao=adesao,
        metodo=Pagamento.Metodo.VINTI4,
        fornecedor=fornecedor.codigo,
        valor_cve=adesao.valor_cve,
        origem=Pagamento.Origem.ADESAO,
        descricao=f"Adesão · {plano.nome}",
        nome_cliente=adesao.nome,
        nif_cliente=adesao.nif,
        email_cliente=adesao.email,
        referencia=_referencia(),
    )
    return adesao, fornecedor.iniciar(pagamento, url_retorno(pagamento))


def iniciar_pagamento_online(pagamento: Pagamento) -> InicioPagamento:
    """Inicia o pagamento online de um pagamento já criado (ex.: mensalidade paga na app)."""
    fornecedor = fornecedor_pagamento(pagamento.ginasio)
    if fornecedor is None:
        raise PagamentoIndisponivel("Este ginásio ainda não aceita pagamentos online.")
    pagamento.fornecedor = fornecedor.codigo
    pagamento.metodo = Pagamento.Metodo.VINTI4
    pagamento.referencia = pagamento.referencia or _referencia()
    pagamento.save(update_fields=["fornecedor", "metodo", "referencia"])
    return fornecedor.iniciar(pagamento, url_retorno(pagamento))


def processar_retorno(pagamento: Pagamento, dados: dict) -> ResultadoPagamento:
    fornecedor = fornecedor_pagamento(pagamento.ginasio)
    if fornecedor is None or fornecedor.codigo != pagamento.fornecedor:
        return ResultadoPagamento(pago=False, mensagem="Fornecedor de pagamento indisponível.")
    resultado = fornecedor.processar_retorno(pagamento, dados)
    if pagamento.estado == Pagamento.Estado.PAGO:  # retorno repetido: idempotente
        return ResultadoPagamento(pago=True, transacao_id=pagamento.transacao_id)
    if resultado.pago:
        confirmar_pagamento(pagamento, resultado)
    else:
        pagamento.estado = Pagamento.Estado.CANCELADO if resultado.cancelado else Pagamento.Estado.FALHADO
        pagamento.resposta = _sem_dados_cartao(resultado.dados)
        pagamento.save(update_fields=["estado", "resposta"])
        if pagamento.adesao:
            pagamento.adesao.estado = (
                Adesao.Estado.CANCELADA if resultado.cancelado else Adesao.Estado.FALHADA
            )
            pagamento.adesao.save(update_fields=["estado"])
    return resultado


def _sem_dados_cartao(dados: dict) -> dict:
    return {k: v for k, v in (dados or {}).items() if "pan" not in k.lower()}


def confirmar_pagamento(pagamento: Pagamento, resultado: ResultadoPagamento | None = None) -> None:
    with transaction.atomic():
        pagamento = Pagamento.todos.select_for_update().get(pk=pagamento.pk)
        if pagamento.estado == Pagamento.Estado.PAGO:
            return
        pagamento.estado = Pagamento.Estado.PAGO
        pagamento.confirmado_em = timezone.now()
        if resultado:
            pagamento.transacao_id = resultado.transacao_id
            pagamento.resposta = _sem_dados_cartao(resultado.dados)
        pagamento.save()
        if pagamento.adesao:
            pagamento.adesao.estado = Adesao.Estado.PAGA
            pagamento.adesao.paga_em = pagamento.confirmado_em
            pagamento.adesao.save(update_fields=["estado", "paga_em"])
        # A gestão de sócios marca a cobrança como paga (ou cria o sócio de uma adesão online).
        pagamento_confirmado.send(sender=Pagamento, pagamento=pagamento)
    fatura = emitir_fatura(pagamento)
    notificar_pagamento(pagamento, fatura)


def emitir_fatura(pagamento: Pagamento) -> Fatura | None:
    fornecedor, config = fornecedor_faturacao(pagamento.ginasio)
    if fornecedor is None:
        return None
    ano = timezone.localdate().year
    with transaction.atomic():
        Ginasio.objects.select_for_update().get(pk=pagamento.ginasio_id)  # serializa a numeração
        existente = Fatura.todos.filter(pagamento=pagamento).first()
        if existente:
            fatura = existente
        else:
            ultima = (
                Fatura.todos.filter(ginasio_id=pagamento.ginasio_id, serie=config.serie, ano=ano)
                .order_by("-sequencia")
                .values_list("sequencia", flat=True)
                .first()
            )
            fatura = Fatura.todos.create(
                ginasio_id=pagamento.ginasio_id,
                pagamento=pagamento,
                serie=config.serie,
                ano=ano,
                sequencia=(ultima or 0) + 1,
                fornecedor=fornecedor.codigo,
                valor_cve=pagamento.valor_cve,
                nome_cliente=pagamento.nome_cliente,
                nif_cliente=pagamento.nif_cliente,
            )
    if fatura.estado == Fatura.Estado.EMITIDA:
        return fatura
    resultado = fornecedor.emitir(fatura)
    fatura.xml = resultado.xml
    if resultado.emitida:
        fatura.estado, fatura.iud, fatura.erro, fatura.emitida_em = (
            Fatura.Estado.EMITIDA,
            resultado.iud,
            "",
            timezone.now(),
        )
    else:
        fatura.estado, fatura.erro = Fatura.Estado.ERRO, resultado.erro
        logger.error("Erro ao emitir fatura %s: %s", fatura.numero, resultado.erro)
    fatura.save()
    return fatura


def notificar_pagamento(pagamento: Pagamento, fatura: Fatura | None) -> None:
    ginasio = pagamento.ginasio
    marca = MarcaSettings.for_site(ginasio.site) if ginasio.site else None
    linha_fatura = f"\nFatura: {fatura.numero} (IUD {fatura.iud})" if fatura and fatura.iud else ""
    if pagamento.email_cliente:
        enviar_email(
            pagamento.email_cliente,
            f"{ginasio.nome}: pagamento confirmado",
            f"Olá {pagamento.nome_cliente},\n\nRecebemos o seu pagamento de {pagamento.valor_cve} CVE "
            f"({pagamento.descricao}).{linha_fatura}\n\nBem-vindo(a)!\n{ginasio.nome}",
        )
    if marca:
        enviar_email(
            marca.email,
            f"Nova adesão paga: {pagamento.nome_cliente}",
            f"{pagamento.descricao} · {pagamento.valor_cve} CVE{linha_fatura}",
        )
        enviar_whatsapp(
            marca.whatsapp, f"Nova adesão paga: {pagamento.nome_cliente} · {pagamento.valor_cve} CVE"
        )
