import socket

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from wagtail.log_actions import log

from .middleware import SESSION_KEY, ginasios_do_utilizador
from .models import Dominio, Membro, Papel


def trocar_ginasio(request):
    ginasios = ginasios_do_utilizador(request.user).select_related("site")
    if request.method == "POST":
        ginasio = get_object_or_404(ginasios, pk=request.POST.get("ginasio"))
        request.session[SESSION_KEY] = ginasio.pk
        log(instance=ginasio, action="plataforma.trocar_ginasio", user=request.user)
        messages.success(request, f"A gerir agora: {ginasio.nome}")
        return redirect("wagtailadmin_home")
    return render(request, "tenants/trocar.html", {"ginasios": ginasios, "atual": request.ginasio})


class NovoMembroForm(forms.Form):
    nome = forms.CharField(max_length=150)
    email = forms.EmailField()
    papel = forms.ChoiceField(choices=Papel.choices)


def _exigir_gestao_equipa(request):
    if (
        not (request.user.is_superuser or request.user.has_perm("tenants.gerir_equipa"))
        or request.ginasio is None
    ):
        raise PermissionDenied


def equipa(request):
    _exigir_gestao_equipa(request)
    ginasio = request.ginasio
    form = NovoMembroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        User = get_user_model()
        email = form.cleaned_data["email"].lower()
        user = User.objects.filter(email__iexact=email).first()
        novo = user is None
        if novo:
            primeiro, _, apelido = form.cleaned_data["nome"].partition(" ")
            user = User.objects.create_user(
                username=email, email=email, first_name=primeiro, last_name=apelido
            )
            user.set_unusable_password()
            user.save()
        membro, _ = Membro.objects.update_or_create(
            user=user, ginasio=ginasio, defaults={"papel": form.cleaned_data["papel"]}
        )
        log(instance=membro, action="wagtail.create", user=request.user)
        if novo:
            send_mail(
                f"Acesso ao Admin de {ginasio.nome}",
                f"Foi adicionado(a) à equipa de {ginasio.nome}.\n\n"
                f"Defina a sua palavra-passe em {settings.WAGTAILADMIN_BASE_URL}/admin/password_reset/ "
                f"com o email {email}.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        messages.success(request, f"{user.get_full_name() or email} faz agora parte da equipa.")
        return redirect("tenants_equipa")
    membros = (
        Membro.objects.filter(ginasio=ginasio).select_related("user").order_by("papel", "user__first_name")
    )
    return render(request, "tenants/equipa.html", {"membros": membros, "form": form, "ginasio": ginasio})


@require_POST
def remover_membro(request, pk):
    _exigir_gestao_equipa(request)
    membro = get_object_or_404(Membro, pk=pk, ginasio=request.ginasio)
    if membro.user == request.user:
        messages.error(request, "Não pode remover a sua própria conta.")
    else:
        log(instance=membro, action="wagtail.delete", user=request.user)
        membro.delete()
        messages.success(request, "Membro removido da equipa.")
    return redirect("tenants_equipa")


def verificar_dominio(request, pk):
    """Confirma que o DNS do domínio aponta para a plataforma (guia de onboarding)."""
    if not request.user.is_superuser:
        raise PermissionDenied
    dominio = get_object_or_404(Dominio, pk=pk)
    esperados = set(filter(None, settings.PLATFORM_IPS))
    try:
        ips = {info[4][0] for info in socket.getaddrinfo(dominio.hostname, 443)}
    except socket.gaierror:
        ips = set()
    ok = bool(ips) and (not esperados or bool(ips & esperados))
    if ok:
        dominio.verificado = True
        dominio.save(update_fields=["verificado"])
        messages.success(request, f"{dominio.hostname} aponta para a plataforma ({', '.join(sorted(ips))}).")
    else:
        messages.error(
            request,
            f"{dominio.hostname} ainda não aponta para a plataforma. "
            f"Registos encontrados: {', '.join(sorted(ips)) or 'nenhum'}. "
            f"Esperado: {', '.join(sorted(esperados)) or 'IP do servidor'}.",
        )
    return redirect("tenants_dominio:edit", pk)
