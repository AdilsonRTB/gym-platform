"""Campo de texto cifrado com Fernet, usado para credenciais SISP e e-Fatura."""

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        if not settings.DEBUG:
            raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY é obrigatório em produção.")
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return ""


class EncryptedTextField(models.TextField):
    """Guarda o valor cifrado na base de dados e expõe-no em claro no Python."""

    prefix = "enc:"

    def from_db_value(self, value, expression, connection):
        if value and value.startswith(self.prefix):
            return decrypt(value[len(self.prefix) :])
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value and not value.startswith(self.prefix):
            return self.prefix + encrypt(value)
        return value
