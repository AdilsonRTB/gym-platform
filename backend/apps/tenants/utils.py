from .models import Membro


def papel_atual(request) -> str | None:
    """Perfil do utilizador no ginásio atual (None para superutilizadores sem ligação)."""
    ginasio = getattr(request, "ginasio", None)
    if ginasio is None or not request.user.is_authenticated:
        return None
    if not hasattr(request, "_papel_atual"):
        request._papel_atual = (
            Membro.objects.filter(user=request.user, ginasio=ginasio).values_list("papel", flat=True).first()
        )
    return request._papel_atual
