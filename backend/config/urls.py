from django.conf import settings
from django.urls import include, path
from django.views.generic import RedirectView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from apps.api import views as api_views
from apps.billing import views as billing_views

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documentos/", include(wagtaildocs_urls)),
    path("api/v1/", include("apps.api.urls")),
    path("internal/dominio-valido/", api_views.dominio_valido),
    path("internal/resolver/", api_views.resolver),
    path("health/", api_views.health),
    path("pagamentos/simulado/<uuid:uuid>/", billing_views.simulado, name="pagamento-simulado"),
    path("pagamentos/<str:fornecedor>/retorno/<uuid:uuid>/", billing_views.retorno, name="pagamento-retorno"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("", include(wagtail_urls)),
]
