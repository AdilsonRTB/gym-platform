from apps.branding.models import MarcaSettings
from apps.core.notifications import enviar_email, enviar_whatsapp

from .models import Lead


def notificar_novo_lead(lead: Lead) -> None:
    ginasio = lead.ginasio
    marca = MarcaSettings.for_site(ginasio.site) if ginasio.site else None
    detalhes = [
        f"Tipo: {lead.get_tipo_display()}",
        f"Nome: {lead.nome}",
        f"Email: {lead.email or '—'}",
        f"Telefone: {lead.telefone or '—'}",
    ]
    if lead.modalidade:
        detalhes.append(f"Modalidade: {lead.modalidade}")
    if lead.data_preferida:
        detalhes.append(f"Data preferida: {lead.data_preferida:%d/%m/%Y}")
    if lead.mensagem:
        detalhes.append(f"\n{lead.mensagem}")
    corpo = "\n".join(detalhes)
    if marca:
        enviar_email(marca.email, f"Novo pedido no site: {lead.nome}", corpo)
        enviar_whatsapp(marca.whatsapp, f"Novo pedido no site ({lead.get_tipo_display()}): {lead.nome}")
