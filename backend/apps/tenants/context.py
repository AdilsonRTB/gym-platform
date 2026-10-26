"""Ginásio atual do pedido, guardado num ContextVar (seguro para threads e async).

Estados possíveis:
- não definido (`None`): comandos, migrações e shell → sem filtro;
- `TenantState(ginasio=g)`: pedidos da API ou do Admin → filtra por `g`;
- `TenantState(ginasio=None)`: utilizador sem ginásio → não vê nada.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import Ginasio


@dataclass(frozen=True)
class TenantState:
    ginasio: Optional["Ginasio"]


_state: ContextVar[TenantState | None] = ContextVar("tenant_state", default=None)


def current_state() -> TenantState | None:
    return _state.get()


def get_current_ginasio() -> Optional["Ginasio"]:
    state = _state.get()
    return state.ginasio if state else None


def set_current(ginasio: Optional["Ginasio"]):
    return _state.set(TenantState(ginasio=ginasio))


def reset(token) -> None:
    _state.reset(token)


@contextmanager
def using_ginasio(ginasio: Optional["Ginasio"]):
    token = set_current(ginasio)
    try:
        yield
    finally:
        reset(token)


@contextmanager
def unscoped():
    """Desliga o filtro (uso interno: webhooks de pagamento, tarefas de plataforma)."""
    token = _state.set(None)
    try:
        yield
    finally:
        _state.reset(token)
