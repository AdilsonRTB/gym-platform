from django import forms
from django.contrib.auth import get_user_model
from wagtail.admin.forms import WagtailAdminModelForm

from .context import get_current_ginasio
from .models import TenantModel


class TenantAdminModelForm(WagtailAdminModelForm):
    """Formulário base do Admin para conteúdo por ginásio.

    O Wagtail guarda as classes de formulário em cache; os querysets das escolhas (ex.: a modalidade
    de uma aula) seriam os do primeiro pedido. Aqui são recalculados em cada formulário, com o filtro
    do ginásio atual.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.ModelChoiceField | forms.ModelMultipleChoiceField):
                modelo = field.queryset.model
                if issubclass(modelo, TenantModel):
                    field.queryset = modelo.objects.all()
                elif modelo is get_user_model():
                    # Só a equipa do ginásio atual (não expor utilizadores de outros ginásios).
                    field.queryset = modelo.objects.filter(membros__ginasio=get_current_ginasio()).distinct()
