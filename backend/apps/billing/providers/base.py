"""Interfaces dos fornecedores de pagamento e faturação.

Cada país acrescenta as suas implementações (ex.: Portugal com MB Way, SEPA e faturação AT) sem
alterar o fluxo de adesão: o núcleo só conhece estas interfaces.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class InicioPagamento:
    """O que o site deve fazer para o visitante pagar."""

    tipo: str  # "form_post" (submeter formulário) ou "redirect"
    url: str
    campos: dict[str, str] = field(default_factory=dict)


@dataclass
class ResultadoPagamento:
    pago: bool
    cancelado: bool = False
    transacao_id: str = ""
    mensagem: str = ""
    dados: dict = field(default_factory=dict)


@dataclass
class ResultadoFatura:
    emitida: bool
    iud: str = ""
    xml: str = ""
    erro: str = ""


class FornecedorPagamento(Protocol):
    codigo: str

    def iniciar(self, pagamento, url_retorno: str) -> InicioPagamento: ...

    def processar_retorno(self, pagamento, dados: dict) -> ResultadoPagamento: ...


class FornecedorFaturacao(Protocol):
    codigo: str

    def emitir(self, fatura) -> ResultadoFatura: ...
