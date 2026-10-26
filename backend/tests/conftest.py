import pytest
from django.core.cache import cache

from apps.content.models import Modalidade, Plano
from apps.tenants.context import using_ginasio
from apps.tenants.models import Ginasio


@pytest.fixture(autouse=True)
def _chave_cifra(settings):
    from cryptography.fernet import Fernet

    from apps.core.fields import _fernet

    settings.FIELD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    _fernet.cache_clear()
    yield
    _fernet.cache_clear()


@pytest.fixture(autouse=True)
def _limpar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def dois_ginasios(db):
    """Dois ginásios provisionados, cada um com uma modalidade e um plano publicados."""
    a = Ginasio.objects.create(nome="Ginásio A", slug="a", estado=Ginasio.Estado.ATIVO)
    b = Ginasio.objects.create(nome="Ginásio B", slug="b", estado=Ginasio.Estado.ATIVO)
    for g in (a, b):
        g.refresh_from_db()
        with using_ginasio(g):
            m = Modalidade(nome=f"Yoga {g.slug.upper()}")
            m.save()
            m.save_revision().publish()
            p = Plano(nome=f"Mensal {g.slug.upper()}", preco_cve=3000)
            p.save()
            p.save_revision().publish()
    return a, b


def host(g):
    return {"HTTP_X_GYM_HOST": f"{g.slug}.localhost"}
