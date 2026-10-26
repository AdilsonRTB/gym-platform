"""Fase 2: sócios, cobranças, check-in offline, lembretes e app do sócio."""

import uuid
from datetime import date, timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.billing.models import ConfiguracaoFiscal, ConfiguracaoPagamentos, Fatura
from apps.content.models import Plano
from apps.gestao.auth import gerar_codigo, token_equipa
from apps.gestao.models import Assinatura, CheckIn, Cobranca, Lembrete, Socio, somar_periodo
from apps.gestao.services import enviar_lembretes, gerar_cobrancas, iniciar_assinatura, marcar_cobranca_paga
from apps.tenants.context import using_ginasio
from apps.tenants.models import Membro, Papel

from .conftest import host

pytestmark = pytest.mark.django_db


def _socio(g, nome="Ana Lima", **extra):
    with using_ginasio(g):
        s = Socio(nome=nome, telefone="+238 991 23 45", email=f"{nome.split()[0].lower()}@x.cv", **extra)
        s.save()
        return s


def _equipa(g, django_user_model, papel=Papel.RECECIONISTA):
    user = django_user_model.objects.create_user(f"{papel}-{g.slug}", password="x")
    Membro.objects.create(user=user, ginasio=g, papel=papel)
    return {"HTTP_AUTHORIZATION": f"Bearer {token_equipa(user, g)}", **host(g)}


def test_somar_periodo():
    assert somar_periodo(date(2026, 1, 15), "mensal") == date(2026, 2, 14)
    assert somar_periodo(date(2026, 1, 31), "mensal") == date(2026, 2, 27)
    assert somar_periodo(date(2026, 11, 1), "trimestral") == date(2027, 1, 31)
    assert somar_periodo(date(2026, 3, 1), "anual") == date(2027, 2, 28)
    assert somar_periodo(date(2026, 3, 1), "semanal") == date(2026, 3, 7)


def test_numero_de_socio_e_sequencial_por_ginasio(dois_ginasios):
    a, b = dois_ginasios
    assert [_socio(a, "A Um").numero, _socio(a, "A Dois").numero, _socio(b, "B Um").numero] == [1, 2, 1]


def test_pagar_cobranca_ativa_e_renova_assinatura(dois_ginasios):
    a, _ = dois_ginasios
    s = _socio(a)
    with using_ginasio(a):
        plano = Plano.objects.get()
        cobranca = iniciar_assinatura(s, plano, inicio=date(2026, 9, 1))
        assinatura = cobranca.assinatura
        assert not assinatura.valida(date(2026, 9, 1))
        marcar_cobranca_paga(cobranca)
        assinatura.refresh_from_db()
        assert assinatura.data_fim == date(2026, 9, 30)
        assert gerar_cobrancas(a, hoje=date(2026, 9, 25)) == 1
        assert gerar_cobrancas(a, hoje=date(2026, 9, 26)) == 0  # não duplica
        seguinte = Cobranca.objects.get(estado=Cobranca.Estado.PENDENTE)
        assert (seguinte.periodo_inicio, seguinte.periodo_fim) == (date(2026, 10, 1), date(2026, 10, 31))


def test_pagamento_na_rececao_emite_fatura_e_isola_ginasios(client, dois_ginasios, django_user_model):
    a, b = dois_ginasios
    ConfiguracaoFiscal.objects.update_or_create(site=a.site, defaults={"fornecedor": "simulado"})
    s = _socio(a)
    with using_ginasio(a):
        cobranca = iniciar_assinatura(s, Plano.objects.get())
    auth_b = _equipa(b, django_user_model)
    assert (
        client.post(
            f"/api/v1/gestao/cobrancas/{cobranca.pk}/pagar/",
            {"metodo": "numerario"},
            content_type="application/json",
            **auth_b,
        ).status_code
        == 404
    )
    auth_a = _equipa(a, django_user_model)
    r = client.post(
        f"/api/v1/gestao/cobrancas/{cobranca.pk}/pagar/",
        {"metodo": "numerario"},
        content_type="application/json",
        **auth_a,
    )
    assert r.status_code == 200 and r.json()["estado"] == "paga" and r.json()["fatura"]["numero"]
    assert Fatura.todos.filter(ginasio=a).count() == 1
    assert Assinatura.todos.get(socio=s).valida()


def test_token_de_equipa_nao_serve_noutro_ginasio(client, dois_ginasios, django_user_model):
    a, b = dois_ginasios
    auth = _equipa(a, django_user_model)
    assert client.get("/api/v1/gestao/resumo/", **auth).status_code == 200
    assert client.get("/api/v1/gestao/resumo/", **{**auth, **host(b)}).status_code == 401


def test_treinador_so_faz_checkin(client, dois_ginasios, django_user_model):
    a, _ = dois_ginasios
    auth = _equipa(a, django_user_model, Papel.TREINADOR)
    assert client.get("/api/v1/gestao/socios/", **auth).status_code == 403
    assert client.get("/api/v1/gestao/checkins/snapshot/", **auth).status_code == 200


def test_checkin_valida_estado_e_tolerancia(dois_ginasios):
    from apps.gestao.services import registar_checkin

    a, _ = dois_ginasios
    s = _socio(a)
    with using_ginasio(a):
        assert not registar_checkin(a, codigo=str(s.codigo)).permitido  # sem assinatura
        cobranca = iniciar_assinatura(
            s, Plano.objects.get(), inicio=timezone.localdate() - timedelta(days=32)
        )
        marcar_cobranca_paga(cobranca)  # válida até há 2 dias
        r = registar_checkin(a, codigo=str(s.codigo))
        assert r.permitido and "tolerância" in r.motivo  # tolerância por omissão: 3 dias
        s.estado = Socio.Estado.SUSPENSO
        s.save()
        assert registar_checkin(a, codigo=str(s.codigo)).motivo == "Sócio suspenso"
        assert registar_checkin(a, codigo=str(uuid.uuid4())).motivo == "Cartão desconhecido"


def test_sincronizacao_offline_e_idempotente(client, dois_ginasios, django_user_model):
    a, b = dois_ginasios
    s = _socio(a)
    outro = _socio(b, "Bruno Outro")
    auth = _equipa(a, django_user_model)
    itens = [
        {"codigo": str(s.codigo), "client_id": str(uuid.uuid4()), "momento": "2026-09-20T08:00:00Z"},
        {"codigo": str(outro.codigo), "client_id": str(uuid.uuid4())},  # cartão de outro ginásio
    ]
    for _ in range(2):  # reenviar a mesma fila não duplica
        r = client.post(
            "/api/v1/gestao/checkins/lote/", {"itens": itens}, content_type="application/json", **auth
        )
        assert r.status_code == 200
    assert CheckIn.todos.filter(ginasio=a).count() == 2
    desconhecido = CheckIn.todos.get(client_id=itens[1]["client_id"])
    assert desconhecido.socio is None and not desconhecido.permitido and desconhecido.offline


def test_lembretes_nao_se_repetem(dois_ginasios):
    a, _ = dois_ginasios
    s = _socio(a)
    hoje = timezone.localdate()
    with using_ginasio(a):
        iniciar_assinatura(s, Plano.objects.get(), inicio=hoje + timedelta(days=3))
        assert enviar_lembretes(a, hoje) == 1
        assert enviar_lembretes(a, hoje) == 0
        assert Lembrete.objects.get().tipo == Lembrete.Tipo.VENCIMENTO


def test_app_do_socio_entra_com_codigo_e_paga_online(client, dois_ginasios):
    a, b = dois_ginasios
    ConfiguracaoPagamentos.objects.update_or_create(site=a.site, defaults={"fornecedor": "simulado"})
    s = _socio(a)
    with using_ginasio(a):
        cobranca = iniciar_assinatura(s, Plano.objects.get())

    assert client.post(
        "/api/v1/socio/auth/codigo/", {"contacto": "ana@x.cv"}, content_type="application/json", **host(a)
    ).json() == {"ok": True}
    assert len(mail.outbox) == 1
    codigo = mail.outbox[0].body[:6]
    assert (
        client.post(
            "/api/v1/socio/auth/entrar/",
            {"contacto": "ana@x.cv", "codigo": "000000"},
            content_type="application/json",
            **host(a),
        ).status_code
        == 400
    )
    r = client.post(
        "/api/v1/socio/auth/entrar/",
        {"contacto": "ana@x.cv", "codigo": codigo},
        content_type="application/json",
        **host(a),
    )
    auth = {"HTTP_AUTHORIZATION": f"Bearer {r.json()['token']}"}

    eu = client.get("/api/v1/socio/eu/", **auth, **host(a)).json()
    assert eu["socio"]["numero"] == s.numero and len(eu["por_pagar"]) == 1
    assert client.get("/api/v1/socio/eu/", **auth, **host(b)).status_code == 401

    r = client.post(
        f"/api/v1/socio/cobrancas/{cobranca.uuid}/pagar/", content_type="application/json", **auth, **host(a)
    )
    url = r.json()["pagamento"]["url"].split("8000", 1)[-1]
    retorno = client.post(url, {"resultado": "aprovado"})
    assert retorno.url.endswith(f"/app?pagamento={Cobranca.todos.get().pagamentos.get().uuid}")
    assert Cobranca.todos.get().estado == Cobranca.Estado.PAGA


def test_codigo_da_app_bloqueia_apos_tentativas(dois_ginasios):
    from apps.gestao.auth import verificar_codigo

    a, _ = dois_ginasios
    s = _socio(a)
    codigo = gerar_codigo(s)
    for _ in range(5):
        assert not verificar_codigo(s, "999999")
    assert not verificar_codigo(s, codigo)


def test_adesao_online_cria_socio(client, dois_ginasios):
    a, _ = dois_ginasios
    ConfiguracaoPagamentos.objects.update_or_create(site=a.site, defaults={"fornecedor": "simulado"})
    with using_ginasio(a):
        plano = Plano.objects.get()
    r = client.post(
        "/api/v1/adesoes/",
        {
            "plano": plano.pk,
            "nome": "Rui Novo",
            "email": "rui@x.cv",
            "telefone": "999",
            "consentimento": True,
        },
        content_type="application/json",
        **host(a),
    )
    client.post(r.json()["pagamento"]["url"].split("8000", 1)[-1], {"resultado": "aprovado"})
    socio = Socio.todos.get(ginasio=a, email="rui@x.cv")
    assert socio.assinatura_atual.valida()
    assert socio.cobrancas.get().estado == Cobranca.Estado.PAGA
