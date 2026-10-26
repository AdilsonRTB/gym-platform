"""Escolha do fornecedor por ginásio. Novos países registam aqui as suas implementações."""

from .efatura_cv import EFaturaCV
from .simulado import FaturacaoSimulada, PagamentoSimulado
from .sisp import SispVinti4

PAGAMENTOS = {"sisp": SispVinti4, "simulado": PagamentoSimulado}
FATURACAO = {"efatura_cv": EFaturaCV, "simulado": FaturacaoSimulada}


def fornecedor_pagamento(ginasio):
    from apps.billing.models import ConfiguracaoPagamentos

    if ginasio.site is None:
        return None
    config = ConfiguracaoPagamentos.for_site(ginasio.site)
    classe = PAGAMENTOS.get(config.fornecedor)
    return classe(config) if classe else None


def fornecedor_faturacao(ginasio):
    from apps.billing.models import ConfiguracaoFiscal

    if ginasio.site is None:
        return None, None
    config = ConfiguracaoFiscal.for_site(ginasio.site)
    classe = FATURACAO.get(config.fornecedor)
    return (classe(config) if classe else None), config
