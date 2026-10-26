"""Configuração da plataforma (Admin CMS + API).

Todas as variáveis sensíveis vêm do ambiente; os valores por omissão servem apenas para desenvolvimento.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
# Os domínios dos ginásios são dinâmicos; a validação real é feita pelo middleware de tenant.
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000")

INSTALLED_APPS = [
    "apps.core",
    "apps.tenants",
    "apps.branding",
    "apps.content",
    "apps.leads",
    "apps.billing",
    "apps.gestao",
    "apps.api",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "rest_framework",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.tenants.middleware.TenantMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
    )
}

REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
else:
    # Em ficheiro (e não em memória) para ser partilhada entre processos: a pré-visualização depende disso.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": BASE_DIR / ".cache",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt"
TIME_ZONE = "Atlantic/Cape_Verde"
USE_I18N = True
USE_TZ = True
WAGTAIL_I18N_ENABLED = False
WAGTAILADMIN_PERMITTED_LANGUAGES = [("pt", "Português"), ("en", "English")]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AWS_STORAGE_BUCKET_NAME = os.environ.get("S3_BUCKET")
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.environ.get("S3_REGION", "eu-west-1")
    AWS_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("S3_CUSTOM_DOMAIN")
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    DEFAULT_STORAGE = {"BACKEND": "storages.backends.s3.S3Storage"}
else:
    DEFAULT_STORAGE = {"BACKEND": "django.core.files.storage.FileSystemStorage"}

STORAGES = {
    "default": DEFAULT_STORAGE,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Wagtail -------------------------------------------------------------
WAGTAIL_SITE_NAME = "Plataforma Ginásios"
WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "http://localhost:8000")
WAGTAILSEARCH_BACKENDS = {"default": {"BACKEND": "wagtail.search.backends.database"}}
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "avif", "svg"]
WAGTAILDOCS_EXTENSIONS = ["pdf", "docx", "xlsx", "csv", "txt", "zip"]
WAGTAIL_ALLOW_UNICODE_SLUGS = False

# --- API e site ----------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # Só os formulários têm limite (por visitante); as leituras vêm do servidor Next.js, em cache.
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {"formularios": "20/min", "login": "10/min", "otp": "5/min"},
    "UNAUTHENTICATED_USER": None,
}
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_HEADERS = ["content-type", "x-gym-host", "authorization"]

# Domínio da plataforma: cada ginásio recebe <slug>.<PLATFORM_DOMAIN> por omissão.
PLATFORM_DOMAIN = os.environ.get("PLATFORM_DOMAIN", "localhost")
# IPs públicos da plataforma, para verificar o DNS dos domínios próprios no Admin.
PLATFORM_IPS = env_list("PLATFORM_IPS")
# Protocolo e porta usados para construir os URLs públicos dos sites (pré-visualização, pagamentos).
SITE_PUBLIC_SCHEME = os.environ.get("SITE_PUBLIC_SCHEME", "http")
SITE_PUBLIC_PORT = os.environ.get("SITE_PUBLIC_PORT", "3100")
# URL interno do Next.js (para o webhook de revalidação) e segredo partilhado.
FRONTEND_INTERNAL_URL = os.environ.get("FRONTEND_INTERNAL_URL", "http://localhost:3100")
REVALIDATE_SECRET = os.environ.get("REVALIDATE_SECRET", "dev-revalidate-secret")
# URL público da API, usado para construir URLs absolutos de imagens.
API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL", "http://localhost:8000")

# Chave para cifrar credenciais (SISP, certificado e-Fatura). Gerar com Fernet.generate_key().
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "")

# --- Email e notificações -----------------------------------------------
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Plataforma Ginásios <no-reply@localhost>")
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
SMS_API_URL = os.environ.get("SMS_API_URL", "")
SMS_API_TOKEN = os.environ.get("SMS_API_TOKEN", "")
SMS_REMETENTE = os.environ.get("SMS_REMETENTE", "GINASIO")

# --- Segurança em produção ----------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:  # pragma: no cover - opcional
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1, send_default_pii=False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
