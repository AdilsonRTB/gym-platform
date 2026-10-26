from django.core.cache import cache

from .models import Dominio, Ginasio, normalizar_host

CACHE_TTL = 60


def _cache_key(host: str) -> str:
    return f"tenant:host:{host}"


def resolver_ginasio(host: str) -> Ginasio | None:
    """Domínio (próprio ou subdomínio da plataforma) → ginásio."""
    host = normalizar_host(host)
    if not host:
        return None
    ginasio_id = cache.get(_cache_key(host))
    if ginasio_id is None:
        dominio = Dominio.objects.filter(hostname=host).only("ginasio_id").first()
        ginasio_id = dominio.ginasio_id if dominio else 0
        cache.set(_cache_key(host), ginasio_id, CACHE_TTL)
    if not ginasio_id:
        return None
    return Ginasio.objects.select_related("site").filter(pk=ginasio_id).first()


def limpar_cache_host(host: str) -> None:
    cache.delete(_cache_key(normalizar_host(host)))
