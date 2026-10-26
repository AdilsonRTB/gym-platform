"""Autenticação por token assinado para o painel da receção e para a app do sócio.

Os tokens levam o id do ginásio: um token de um ginásio nunca é aceite no domínio de outro.
O Next.js guarda-os em cookies httpOnly e envia-os como `Authorization: Bearer`.
"""

import hashlib
import hmac
import secrets

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from rest_framework import authentication, exceptions, permissions

from apps.tenants.models import Membro, Papel

from .models import Socio, so_digitos

SAL_EQUIPA = "gestao.equipa"
SAL_SOCIO = "gestao.socio"
DURACAO_EQUIPA = 60 * 60 * 12  # um turno
DURACAO_SOCIO = 60 * 60 * 24 * 60  # 60 dias na app

PAPEIS_PAINEL = {Papel.DONO, Papel.GESTOR, Papel.RECECIONISTA}
PAPEIS_CHECKIN = PAPEIS_PAINEL | {Papel.TREINADOR}


def token_equipa(user, ginasio) -> str:
    return signing.dumps({"u": user.pk, "g": ginasio.pk}, salt=SAL_EQUIPA)


def token_socio(socio) -> str:
    return signing.dumps({"s": socio.pk, "g": socio.ginasio_id, "c": str(socio.codigo)[:8]}, salt=SAL_SOCIO)


def papel_de(user, ginasio) -> str | None:
    if user.is_superuser:
        return "plataforma"
    return Membro.objects.filter(user=user, ginasio=ginasio).values_list("papel", flat=True).first()


def _bearer(request) -> str | None:
    header = request.headers.get("Authorization", "")
    return header[7:] if header.startswith("Bearer ") else None


class EquipaAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = _bearer(request)
        if not token:
            return None
        try:
            dados = signing.loads(token, salt=SAL_EQUIPA, max_age=DURACAO_EQUIPA)
        except signing.BadSignature as exc:
            raise exceptions.AuthenticationFailed("Sessão expirada. Entre novamente.") from exc
        if dados.get("g") != request.ginasio.pk:
            raise exceptions.AuthenticationFailed("Sessão de outro ginásio.")
        user = get_user_model().objects.filter(pk=dados.get("u"), is_active=True).first()
        papel = papel_de(user, request.ginasio) if user else None
        if papel is None:
            raise exceptions.AuthenticationFailed("Sem acesso a este ginásio.")
        request.papel = papel
        return user, dados

    def authenticate_header(self, request):
        return "Bearer"


class SocioAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = _bearer(request)
        if not token:
            return None
        try:
            dados = signing.loads(token, salt=SAL_SOCIO, max_age=DURACAO_SOCIO)
        except signing.BadSignature as exc:
            raise exceptions.AuthenticationFailed("Sessão expirada. Entre novamente.") from exc
        if dados.get("g") != request.ginasio.pk:
            raise exceptions.AuthenticationFailed("Sessão de outro ginásio.")
        socio = Socio.objects.filter(pk=dados.get("s")).first()
        # Regenerar o código do cartão termina também as sessões da app.
        if socio is None or str(socio.codigo)[:8] != dados.get("c") or socio.estado == Socio.Estado.INATIVO:
            raise exceptions.AuthenticationFailed("Sessão inválida.")
        request.socio = socio
        return socio, dados

    def authenticate_header(self, request):
        return "Bearer"


class DoPainel(permissions.BasePermission):
    message = "Sem permissão para o painel da receção."

    def has_permission(self, request, view):
        return getattr(request, "papel", None) in PAPEIS_PAINEL | {"plataforma"}


class PodeFazerCheckIn(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request, "papel", None) in PAPEIS_CHECKIN | {"plataforma"}


class SoGestao(permissions.BasePermission):
    """Anular cobranças e mudar planos: dono e gestor."""

    def has_permission(self, request, view):
        return getattr(request, "papel", None) in {Papel.DONO, Papel.GESTOR, "plataforma"}


class EhSocio(permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(getattr(request, "user", None), Socio)


# --------------------------------------------------------------------------- Código de acesso (app)

TENTATIVAS = 5
VALIDADE_CODIGO = 60 * 10


def encontrar_socio(ginasio, contacto: str) -> Socio | None:
    contacto = (contacto or "").strip()
    qs = Socio.todos.filter(ginasio=ginasio).exclude(estado=Socio.Estado.INATIVO)
    if "@" in contacto:
        return qs.filter(email__iexact=contacto).first()
    digitos = so_digitos(contacto)[-9:]
    return qs.filter(telefone_digitos=digitos).first() if len(digitos) >= 7 else None


def _chave(socio) -> str:
    return f"otp:{socio.ginasio_id}:{socio.pk}"


def _hash(codigo: str) -> str:
    return hashlib.sha256(codigo.encode()).hexdigest()


def gerar_codigo(socio) -> str:
    codigo = f"{secrets.randbelow(10**6):06d}"
    cache.set(_chave(socio), {"h": _hash(codigo), "t": 0}, VALIDADE_CODIGO)
    return codigo


def verificar_codigo(socio, codigo: str) -> bool:
    dados = cache.get(_chave(socio))
    if not dados or dados["t"] >= TENTATIVAS:
        return False
    if hmac.compare_digest(dados["h"], _hash(so_digitos(codigo))):
        cache.delete(_chave(socio))
        return True
    dados["t"] += 1
    cache.set(_chave(socio), dados, VALIDADE_CODIGO)
    return False
