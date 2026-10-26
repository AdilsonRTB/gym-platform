import pytest

from apps.billing.models import ConfiguracaoFiscal, ConfiguracaoPagamentos, Fatura
from apps.billing.providers.sisp import fingerprint_pedido, fingerprint_resposta
from apps.content.models import Plano
from apps.leads.models import Lead, PedidoDados
from apps.leads.services import concluir_pedido
from apps.tenants.context import using_ginasio

from .conftest import host

pytestmark = pytest.mark.django_db


def test_lead_exige_consentimento_e_regista_o_texto(client, dois_ginasios):
    a, _ = dois_ginasios
    dados = {"tipo": "contacto", "nome": "Ana", "email": "ana@x.cv"}
    r = client.post(
        "/api/v1/leads/", {**dados, "consentimento": False}, content_type="application/json", **host(a)
    )
    assert r.status_code == 400
    r = client.post(
        "/api/v1/leads/", {**dados, "consentimento": True}, content_type="application/json", **host(a)
    )
    assert r.status_code == 201
    lead = Lead.todos.get()
    assert lead.ginasio == a and lead.consentimento and lead.consentimento_texto and lead.consentimento_em


def test_adesao_paga_emite_fatura(client, dois_ginasios):
    a, _ = dois_ginasios
    ConfiguracaoPagamentos.objects.update_or_create(site=a.site, defaults={"fornecedor": "simulado"})
    ConfiguracaoFiscal.objects.update_or_create(
        site=a.site, defaults={"fornecedor": "simulado", "serie": "FT"}
    )
    with using_ginasio(a):
        plano = Plano.objects.get()
    r = client.post(
        "/api/v1/adesoes/",
        {"plano": plano.pk, "nome": "Rui", "email": "rui@x.cv", "telefone": "999", "consentimento": True},
        content_type="application/json",
        **host(a),
    )
    assert r.status_code == 201
    url = r.json()["pagamento"]["url"].split("8000", 1)[-1]
    r = client.post(url, {"resultado": "aprovado"})
    assert r.status_code == 302 and "/aderir/resultado?ref=" in r.url
    estado = client.get(f"/api/v1/adesoes/{r.url.split('ref=')[1]}/", **host(a)).json()
    assert estado["estado"] == "paga"
    fatura = Fatura.todos.get()
    assert fatura.numero.startswith("FT ") and fatura.estado == "emitida" and fatura.iud


def test_adesao_sem_pagamentos_configurados_da_409(client, dois_ginasios):
    a, _ = dois_ginasios
    with using_ginasio(a):
        plano = Plano.objects.get()
    r = client.post(
        "/api/v1/adesoes/",
        {"plano": plano.pk, "nome": "Rui", "email": "rui@x.cv", "telefone": "999", "consentimento": True},
        content_type="application/json",
        **host(a),
    )
    assert r.status_code == 409


def test_fingerprint_sisp_e_deterministico_e_valida_resposta():
    fp = fingerprint_pedido("segredo", "2026-09-25 10:00:00", 3500, "A1", "S1", "90000001", "132", "1")
    assert fp == fingerprint_pedido(
        "segredo", "2026-09-25 10:00:00", 3500, "A1", "S1", "90000001", "132", "1"
    )
    assert fp != fingerprint_pedido("outro", "2026-09-25 10:00:00", 3500, "A1", "S1", "90000001", "132", "1")
    resposta = {"messageType": "8", "merchantRespMerchantRef": "A1", "merchantRespPurchaseAmount": "3500"}
    assert fingerprint_resposta("segredo", resposta) != fingerprint_resposta("outro", resposta)


def test_pedido_de_eliminacao_anonimiza(dois_ginasios):
    a, b = dois_ginasios
    with using_ginasio(a):
        Lead.objects.create(nome="Ana", email="ana@x.cv")
        pedido = PedidoDados.objects.create(tipo="eliminacao", email="ana@x.cv")
    with using_ginasio(b):
        Lead.objects.create(nome="Ana", email="ana@x.cv")  # outro ginásio: não pode ser tocado
    concluir_pedido(pedido)
    assert Lead.todos.get(ginasio=a).nome == "[eliminado]"
    assert Lead.todos.get(ginasio=b).nome == "Ana"


def test_endpoint_do_caddy_valida_dominios(client, dois_ginasios):
    assert client.get("/internal/dominio-valido/?domain=a.localhost").status_code == 200
    assert client.get("/internal/dominio-valido/?domain=intruso.cv").status_code == 404


def test_campo_cifrado_nao_fica_em_claro(dois_ginasios):
    from django.db import connection

    a, _ = dois_ginasios
    config = ConfiguracaoPagamentos.for_site(a.site)
    config.sisp_pos_aut_code = "super-secreto"
    config.save()
    with connection.cursor() as c:
        c.execute("SELECT sisp_pos_aut_code FROM billing_configuracaopagamentos")
        bruto = c.fetchone()[0]
    assert bruto.startswith("enc:") and "super-secreto" not in bruto
    config.refresh_from_db()
    assert config.sisp_pos_aut_code == "super-secreto"
