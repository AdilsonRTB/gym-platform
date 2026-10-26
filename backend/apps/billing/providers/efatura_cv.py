"""e-Fatura (DNRE, Cabo Verde).

Cada ginásio é o emissor: os documentos são assinados com o certificado ICP-CV do ginásio e
transmitidos à plataforma e-Fatura.

ATENÇÃO: o XML abaixo é um esqueleto do DFE. Os nomes dos elementos, a assinatura XML e o endpoint
têm de ser alinhados com o esquema em vigor da DNRE antes de produção — a equipa já tem esta
integração feita noutro projeto; o cliente existente deve substituir `construir_xml` e `emitir`.
O endpoint é configurado por ginásio no Admin (Configurações → Faturação).
"""

import base64
from xml.sax.saxutils import escape

import requests
from django.utils import timezone

from .base import ResultadoFatura


class EFaturaCV:
    codigo = "efatura_cv"

    def __init__(self, config):
        self.config = config

    def construir_xml(self, fatura) -> str:
        c = self.config
        data = timezone.localtime(fatura.criada_em or timezone.now())
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Dfe>"
            f"<Emissor><NIF>{escape(c.nif)}</NIF><Nome>{escape(c.nome_fiscal)}</Nome>"
            f"<Morada>{escape(c.morada_fiscal)}</Morada></Emissor>"
            f"<Documento><Tipo>FTR</Tipo><Serie>{escape(fatura.serie)}</Serie>"
            f"<Numero>{fatura.sequencia}</Numero><Data>{data:%Y-%m-%d}</Data><Moeda>CVE</Moeda></Documento>"
            f"<Cliente><NIF>{escape(fatura.nif_cliente or '000000000')}</NIF>"
            f"<Nome>{escape(fatura.nome_cliente)}</Nome></Cliente>"
            f"<Linhas><Linha><Descricao>{escape(fatura.pagamento.descricao)}</Descricao>"
            f"<Quantidade>1</Quantidade><PrecoUnitario>{fatura.valor_cve}</PrecoUnitario></Linha></Linhas>"
            f"<Totais><Total>{fatura.valor_cve}</Total></Totais>"
            "</Dfe>"
        )

    def emitir(self, fatura) -> ResultadoFatura:
        c = self.config
        if not (c.nif and c.certificado_b64 and c.efatura_url):
            return ResultadoFatura(emitida=False, erro="Dados fiscais, certificado ou endpoint em falta.")
        xml = self.construir_xml(fatura)
        url = c.efatura_url
        try:
            import tempfile

            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                NoEncryption,
                PrivateFormat,
                pkcs12,
            )

            chave, cert, _ = pkcs12.load_key_and_certificates(
                base64.b64decode(c.certificado_b64), (c.certificado_senha or "").encode() or None
            )
            with tempfile.NamedTemporaryFile(suffix=".pem") as pem:
                pem.write(chave.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
                pem.write(cert.public_bytes(Encoding.PEM))
                pem.flush()
                resposta = requests.post(
                    url,
                    data=xml.encode(),
                    headers={"Content-Type": "application/xml"},
                    cert=pem.name,
                    timeout=30,
                )
            if resposta.status_code >= 400:
                return ResultadoFatura(
                    emitida=False, xml=xml, erro=f"{resposta.status_code}: {resposta.text[:500]}"
                )
            dados = resposta.json() if "json" in resposta.headers.get("content-type", "") else {}
            return ResultadoFatura(emitida=True, iud=dados.get("iud", ""), xml=xml)
        except Exception as exc:  # noqa: BLE001 - o erro fica registado na fatura para nova tentativa
            return ResultadoFatura(emitida=False, xml=xml, erro=str(exc))
