"""Notificações ao ginásio (email e WhatsApp)."""

import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_email(destinatario: str, assunto: str, corpo: str) -> None:
    if not destinatario:
        return
    try:
        send_mail(assunto, corpo, settings.DEFAULT_FROM_EMAIL, [destinatario], fail_silently=False)
    except Exception as exc:  # noqa: BLE001 - uma notificação falhada não pode bloquear o pedido
        logger.warning("Falha ao enviar email para %s: %s", destinatario, exc)


def enviar_whatsapp(numero: str, mensagem: str) -> None:
    """Envia via WhatsApp Cloud API (ou fornecedor compatível) quando configurado."""
    if not numero:
        return
    if not (settings.WHATSAPP_API_URL and settings.WHATSAPP_API_TOKEN):
        logger.info("[whatsapp:simulado] %s → %s", numero, mensagem)
        return
    try:
        requests.post(
            settings.WHATSAPP_API_URL,
            headers={"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": numero.replace("+", "").replace(" ", ""),
                "type": "text",
                "text": {"body": mensagem},
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.warning("Falha ao enviar WhatsApp para %s: %s", numero, exc)


def enviar_sms(numero: str, mensagem: str) -> None:
    """Envia SMS por um gateway HTTP genérico (ex.: operador local) quando configurado."""
    if not numero:
        return
    if not (settings.SMS_API_URL and settings.SMS_API_TOKEN):
        logger.info("[sms:simulado] %s → %s", numero, mensagem)
        return
    try:
        requests.post(
            settings.SMS_API_URL,
            headers={"Authorization": f"Bearer {settings.SMS_API_TOKEN}"},
            json={"to": numero.replace(" ", ""), "from": settings.SMS_REMETENTE, "text": mensagem[:459]},
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.warning("Falha ao enviar SMS para %s: %s", numero, exc)
