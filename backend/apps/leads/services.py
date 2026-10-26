"""Operações CNPD: exportar e eliminar (anonimizar) os dados de uma pessoa num ginásio."""

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Adesao, Pagamento

from .models import Lead, PedidoDados

ANONIMO = "[eliminado]"


def _q_pessoa(email: str, telefone: str = ""):
    from django.db.models import Q

    q = Q(email__iexact=email)
    if telefone:
        q |= Q(telefone=telefone)
    return q


def exportar_dados(ginasio, email: str, telefone: str = "") -> dict:
    q = _q_pessoa(email, telefone)
    leads = Lead.todos.filter(q, ginasio=ginasio)
    adesoes = Adesao.todos.filter(q, ginasio=ginasio)
    return {
        "ginasio": ginasio.nome,
        "gerado_em": timezone.now().isoformat(),
        "email": email,
        "leads": [
            {
                "tipo": lead.tipo,
                "nome": lead.nome,
                "email": lead.email,
                "telefone": lead.telefone,
                "mensagem": lead.mensagem,
                "criado_em": lead.criado_em.isoformat(),
                "consentimento": lead.consentimento,
                "consentimento_texto": lead.consentimento_texto,
                "consentimento_em": lead.consentimento_em.isoformat() if lead.consentimento_em else None,
            }
            for lead in leads
        ],
        "adesoes": [
            {
                "plano": str(a.plano),
                "nome": a.nome,
                "email": a.email,
                "telefone": a.telefone,
                "nif": a.nif,
                "estado": a.estado,
                "valor_cve": a.valor_cve,
                "criado_em": a.criado_em.isoformat(),
                "pagamentos": [
                    {
                        "valor_cve": p.valor_cve,
                        "estado": p.estado,
                        "metodo": p.metodo,
                        "data": p.criado_em.isoformat(),
                    }
                    for p in a.pagamentos.all()
                ],
            }
            for a in adesoes
        ],
    }


@transaction.atomic
def eliminar_dados(ginasio, email: str, telefone: str = "") -> dict:
    """Anonimiza leads e adesões. As faturas mantêm-se por obrigação fiscal (retenção legal)."""
    q = _q_pessoa(email, telefone)
    n_leads = Lead.todos.filter(q, ginasio=ginasio).update(
        nome=ANONIMO, email="", telefone="", mensagem="", notas="", ip=None, user_agent=""
    )
    adesoes = Adesao.todos.filter(q, ginasio=ginasio)
    n_adesoes = adesoes.count()
    Pagamento.todos.filter(adesao__in=adesoes).update(nome_cliente=ANONIMO, email_cliente="")
    adesoes.update(nome=ANONIMO, email="", telefone="", morada="")
    return {"leads": n_leads, "adesoes": n_adesoes}


def concluir_pedido(pedido: PedidoDados) -> dict | None:
    if pedido.tipo == PedidoDados.Tipo.EXPORTACAO:
        resultado = exportar_dados(pedido.ginasio, pedido.email, pedido.telefone)
    else:
        resultado = eliminar_dados(pedido.ginasio, pedido.email, pedido.telefone)
        pedido.nome = ANONIMO
    pedido.estado = PedidoDados.Estado.CONCLUIDO
    pedido.concluido_em = timezone.now()
    pedido.save()
    return resultado
