"""Fornecedores simulados para desenvolvimento, staging e demonstrações."""

import hashlib

from django.conf import settings
from django.utils import timezone

from .base import InicioPagamento, ResultadoFatura, ResultadoPagamento


class PagamentoSimulado:
    codigo = "simulado"

    def __init__(self, config=None):
        self.config = config

    def iniciar(self, pagamento, url_retorno: str) -> InicioPagamento:
        url = f"{settings.API_PUBLIC_URL.rstrip('/')}/pagamentos/simulado/{pagamento.uuid}/"
        return InicioPagamento(tipo="redirect", url=url)

    def processar_retorno(self, pagamento, dados: dict) -> ResultadoPagamento:
        if dados.get("resultado") == "aprovado":
            return ResultadoPagamento(pago=True, transacao_id=f"SIM-{pagamento.referencia}", dados=dados)
        return ResultadoPagamento(pago=False, cancelado=dados.get("resultado") == "cancelado", dados=dados)


class FaturacaoSimulada:
    codigo = "simulado"

    def __init__(self, config=None):
        self.config = config

    def emitir(self, fatura) -> ResultadoFatura:
        base = f"{fatura.ginasio_id}-{fatura.numero}-{timezone.now().isoformat()}"
        iud = "CVSIM" + hashlib.sha1(base.encode()).hexdigest()[:40].upper()
        xml = (
            f"<Fatura simulada='true'><Numero>{fatura.numero}</Numero>"
            f"<Valor moeda='CVE'>{fatura.valor_cve}</Valor><IUD>{iud}</IUD></Fatura>"
        )
        return ResultadoFatura(emitida=True, iud=iud, xml=xml)
