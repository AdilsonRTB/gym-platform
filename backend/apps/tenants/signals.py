from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Dominio, Ginasio, Membro
from .permissions import grupo_do_papel
from .resolver import limpar_cache_host


@receiver(post_save, sender=Membro)
def adicionar_ao_grupo(sender, instance: Membro, **kwargs):
    grupos_do_ginasio = instance.user.groups.filter(name__startswith=f"{instance.ginasio.slug} · ")
    instance.user.groups.remove(*grupos_do_ginasio)
    instance.user.groups.add(grupo_do_papel(instance.ginasio, instance.papel))


@receiver(post_delete, sender=Membro)
def remover_do_grupo(sender, instance: Membro, **kwargs):
    instance.user.groups.remove(*instance.user.groups.filter(name__startswith=f"{instance.ginasio.slug} · "))


@receiver(post_save, sender=Dominio)
@receiver(post_delete, sender=Dominio)
def limpar_cache(sender, instance: Dominio, **kwargs):
    limpar_cache_host(instance.hostname)


@receiver(post_save, sender=Ginasio)
def provisionar(sender, instance: Ginasio, created, **kwargs):
    """Um ginásio novo recebe logo página inicial, Site, subdomínio, coleção de media e grupos."""
    if created and instance.site_id is None and not kwargs.get("raw"):
        from .provisioning import provisionar_ginasio

        provisionar_ginasio(instance)
