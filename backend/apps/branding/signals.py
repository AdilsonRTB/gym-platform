from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.revalidation import revalidate

from .models import MarcaSettings, PrivacidadeSettings, SeoSettings


@receiver(post_save, sender=MarcaSettings)
@receiver(post_save, sender=SeoSettings)
@receiver(post_save, sender=PrivacidadeSettings)
def revalidar_site(sender, instance, **kwargs):
    ginasio = getattr(instance.site, "ginasio", None)
    if ginasio:
        revalidate(ginasio.pk, "site", "paginas")
