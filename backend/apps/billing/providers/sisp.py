"""SISP · Vinti4Net (compra com cartão, transactionCode 1).

Implementa o cálculo do fingerprint de pedido e de resposta conforme o manual de integração
Vinti4Net (versão 1 do fingerprint). Validar com a documentação atual da SISP antes de produção.
"""

import base64
import hashlib
import json

from django.utils import timezone

from .base import InicioPagamento, ResultadoPagamento

URL_PRODUCAO = "https://mc.vinti4net.cv/BizMPIOnUs/CardPayment"
MOEDA_CVE = "132"
TIPOS_SUCESSO = {"8", "10", "M", "P"}


def _b64_sha512(texto: str) -> str:
    return base64.b64encode(hashlib.sha512(texto.encode("utf-8")).digest()).decode()


def _valor_milesimos(valor) -> str:
    return str(int(round(float(valor) * 1000)))


def fingerprint_pedido(
    pos_aut_code: str,
    timestamp: str,
    valor,
    merchant_ref: str,
    merchant_session: str,
    pos_id: str,
    moeda: str,
    transaction_code: str,
    entity_code: str = "",
    reference_number: str = "",
) -> str:
    texto = (
        _b64_sha512(pos_aut_code)
        + timestamp
        + _valor_milesimos(valor)
        + merchant_ref.strip()
        + merchant_session.strip()
        + pos_id.strip()
        + moeda.strip()
        + transaction_code.strip()
    )
    if entity_code:
        texto += str(int(entity_code))
    if reference_number:
        texto += str(int(reference_number))
    return _b64_sha512(texto)


def fingerprint_resposta(pos_aut_code: str, d: dict) -> str:
    texto = (
        _b64_sha512(pos_aut_code)
        + d.get("messageType", "")
        + d.get("merchantRespCP", "")
        + d.get("merchantRespTid", "")
        + d.get("merchantRespMerchantRef", "")
        + d.get("merchantRespMerchantSession", "")
        + _valor_milesimos(d.get("merchantRespPurchaseAmount") or 0)
        + d.get("merchantRespMessageID", "")
        + d.get("merchantRespPan", "")
        + d.get("merchantResp", "")
        + d.get("merchantRespTimeStamp", "")
        + d.get("merchantRespReferenceNumber", "")
        + d.get("merchantRespEntityCode", "")
        + d.get("merchantRespClientReceipt", "")
        + d.get("merchantRespAdditionalErrorMessage", "").strip()
        + d.get("merchantRespReloadCode", "")
    )
    return _b64_sha512(texto)


class SispVinti4:
    codigo = "sisp"

    def __init__(self, config):
        self.config = config

    def iniciar(self, pagamento, url_retorno: str) -> InicioPagamento:
        timestamp = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
        merchant_ref = pagamento.referencia[:15]
        merchant_session = f"S{timezone.now():%Y%m%d%H%M%S}"[:15]
        pos_id = self.config.sisp_pos_id
        fp = fingerprint_pedido(
            self.config.sisp_pos_aut_code,
            timestamp,
            pagamento.valor_cve,
            merchant_ref,
            merchant_session,
            pos_id,
            MOEDA_CVE,
            "1",
        )
        compra_3ds = {
            "acctID": pagamento.email_cliente or merchant_ref,
            "acctInfo": {"chAccAgeInd": "05"},
            "email": pagamento.email_cliente,
            "addrMatch": "N",
            "billAddrCountry": "132",
        }
        campos = {
            "transactionCode": "1",
            "posID": pos_id,
            "merchantRef": merchant_ref,
            "merchantSession": merchant_session,
            "amount": str(pagamento.valor_cve),
            "currency": MOEDA_CVE,
            "is3DSec": "1",
            "urlMerchantResponse": url_retorno,
            "languageMessages": "pt",
            "timeStamp": timestamp,
            "fingerprintversion": "1",
            "entityCode": "",
            "referenceNumber": "",
            "purchaseRequest": base64.b64encode(json.dumps(compra_3ds).encode()).decode(),
            "FingerPrint": fp,
        }
        base = self.config.sisp_url or URL_PRODUCAO
        url = f"{base}?FingerPrint={fp}&TimeStamp={timestamp}&FingerPrintVersion=1"
        return InicioPagamento(tipo="form_post", url=url, campos=campos)

    def processar_retorno(self, pagamento, dados: dict) -> ResultadoPagamento:
        if dados.get("UserCancelled") == "true":
            return ResultadoPagamento(
                pago=False, cancelado=True, mensagem="Pagamento cancelado.", dados=dados
            )
        if dados.get("messageType") not in TIPOS_SUCESSO:
            return ResultadoPagamento(
                pago=False,
                mensagem=dados.get("merchantRespErrorDescription", "Pagamento recusado."),
                dados=dados,
            )
        esperado = fingerprint_resposta(self.config.sisp_pos_aut_code, dados)
        if esperado != dados.get("resultFingerPrint"):
            return ResultadoPagamento(pago=False, mensagem="Fingerprint inválido.", dados=dados)
        if dados.get("merchantRespMerchantRef") != pagamento.referencia[:15]:
            return ResultadoPagamento(pago=False, mensagem="Referência não corresponde.", dados=dados)
        if int(float(dados.get("merchantRespPurchaseAmount") or 0)) != pagamento.valor_cve:
            return ResultadoPagamento(pago=False, mensagem="Valor não corresponde.", dados=dados)
        return ResultadoPagamento(pago=True, transacao_id=dados.get("merchantRespTid", ""), dados=dados)
