from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from apps.tenants.context import unscoped

from .models import Pagamento
from .services import processar_retorno


def _url_resultado(pagamento: Pagamento) -> str:
    if pagamento.origem == Pagamento.Origem.APP:
        return pagamento.ginasio.url_publico(f"/app?pagamento={pagamento.uuid}")
    ref = pagamento.adesao.uuid if pagamento.adesao else pagamento.uuid
    return pagamento.ginasio.url_publico(f"/aderir/resultado?ref={ref}")


@csrf_exempt
def retorno(request, fornecedor: str, uuid):
    """URL de resposta do fornecedor (o browser do visitante é reencaminhado para aqui)."""
    with unscoped():
        pagamento = get_object_or_404(Pagamento.todos.select_related("ginasio__site", "adesao"), uuid=uuid)
        if pagamento.fornecedor != fornecedor:
            raise Http404
        dados = request.POST.dict() if request.method == "POST" else request.GET.dict()
        processar_retorno(pagamento, dados)
        return redirect(_url_resultado(pagamento))


def simulado(request, uuid):
    """Página de pagamento simulado (substitui o Vinti4Net em desenvolvimento)."""
    with unscoped():
        pagamento = get_object_or_404(
            Pagamento.todos.select_related("ginasio", "adesao__plano"), uuid=uuid, fornecedor="simulado"
        )
        if request.method == "POST":
            processar_retorno(pagamento, {"resultado": request.POST.get("resultado", "recusado")})
            return redirect(_url_resultado(pagamento))
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET", "POST"])
        return render(request, "billing/simulado.html", {"pagamento": pagamento})
