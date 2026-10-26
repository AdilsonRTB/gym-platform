"""Isolamento entre ginásios: ler ou escrever dados de outro ginásio tem de falhar."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.billing.models import Adesao
from apps.content.models import Modalidade, Plano
from apps.leads.models import Lead
from apps.tenants.context import using_ginasio

from .conftest import host

pytestmark = pytest.mark.django_db


def test_manager_filtra_pelo_ginasio_atual(dois_ginasios):
    a, b = dois_ginasios
    with using_ginasio(a):
        assert list(Modalidade.objects.values_list("nome", flat=True)) == ["Yoga A"]
        assert not Modalidade.objects.filter(ginasio=b).exists()
    with using_ginasio(b):
        assert list(Modalidade.objects.values_list("nome", flat=True)) == ["Yoga B"]


def test_sem_ginasio_nao_ve_nada(dois_ginasios):
    with using_ginasio(None):
        assert Modalidade.objects.count() == 0


def test_criar_sem_ginasio_falha(db):
    with using_ginasio(None), pytest.raises(ValidationError):
        Modalidade(nome="Órfã").save()


def test_api_so_devolve_dados_do_dominio(client, dois_ginasios):
    a, b = dois_ginasios
    nomes = [m["nome"] for m in client.get("/api/v1/modalidades/", **host(a)).json()]
    assert nomes == ["Yoga A"]
    with using_ginasio(b):
        slug_b = Modalidade.objects.get().slug
    assert client.get(f"/api/v1/modalidades/{slug_b}/", **host(a)).status_code in (200, 404)
    # O slug pode coincidir; o conteúdo devolvido nunca pode ser o do outro ginásio.
    resposta = client.get(f"/api/v1/modalidades/{slug_b}/", **host(a))
    if resposta.status_code == 200:
        assert resposta.json()["nome"] == "Yoga A"


def test_dominio_desconhecido_da_404(client, dois_ginasios):
    assert client.get("/api/v1/site/", HTTP_X_GYM_HOST="nao-existe.cv").status_code == 404


def test_lead_nao_pode_referir_modalidade_de_outro_ginasio(client, dois_ginasios):
    a, b = dois_ginasios
    with using_ginasio(b):
        slug_b = Modalidade.objects.get().slug
    with using_ginasio(a):
        Modalidade.objects.update(slug="so-em-a")
    resposta = client.post(
        "/api/v1/leads/",
        {
            "tipo": "aula_experimental",
            "nome": "X",
            "telefone": "999",
            "modalidade": slug_b,
            "consentimento": True,
        },
        content_type="application/json",
        **host(a),
    )
    assert resposta.status_code == 400
    assert "modalidade" in resposta.json()


def test_adesao_nao_aceita_plano_de_outro_ginasio(client, dois_ginasios):
    a, b = dois_ginasios
    with using_ginasio(b):
        plano_b = Plano.objects.get().pk
    resposta = client.post(
        "/api/v1/adesoes/",
        {"plano": plano_b, "nome": "X", "email": "x@x.cv", "telefone": "999", "consentimento": True},
        content_type="application/json",
        **host(a),
    )
    assert resposta.status_code == 400
    assert Adesao.todos.count() == 0


def test_estado_de_adesao_de_outro_ginasio_da_404(client, dois_ginasios):
    a, b = dois_ginasios
    with using_ginasio(b):
        plano = Plano.objects.get()
        adesao = Adesao.objects.create(plano=plano, nome="Y", email="y@y.cv", telefone="1", valor_cve=3000)
    assert client.get(f"/api/v1/adesoes/{adesao.uuid}/", **host(a)).status_code == 404
    assert client.get(f"/api/v1/adesoes/{adesao.uuid}/", **host(b)).status_code == 200


def test_admin_so_mostra_leads_do_ginasio_do_utilizador(client, dois_ginasios, django_user_model):
    from apps.tenants.models import Membro, Papel

    a, b = dois_ginasios
    with using_ginasio(a):
        Lead.objects.create(nome="Lead de A", telefone="1")
    with using_ginasio(b):
        Lead.objects.create(nome="Lead de B", telefone="2")
    gestor = django_user_model.objects.create_user("gestor-a", password="x")
    Membro.objects.create(user=gestor, ginasio=a, papel=Papel.GESTOR)
    client.force_login(gestor)
    html = client.get(reverse("leads_lead:index")).content.decode()
    assert "Lead de A" in html
    assert "Lead de B" not in html


def test_admin_configuracoes_de_outro_site_redirecionam(client, dois_ginasios, django_user_model):
    from apps.tenants.models import Membro, Papel

    a, b = dois_ginasios
    dono = django_user_model.objects.create_user("dono-a", password="x")
    Membro.objects.create(user=dono, ginasio=a, papel=Papel.DONO)
    client.force_login(dono)
    resposta = client.get(f"/admin/settings/branding/marcasettings/{b.site_id}/")
    assert resposta.status_code == 302
    assert resposta.url.endswith(f"/{a.site_id}/")
