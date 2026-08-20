"""
Base settings — shared across dev and prod.
Environment-specific overrides live in dev.py / prod.py.
"""
from pathlib import Path

import environ
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", default="http://localhost:8000")
SOCIAL_TOKEN_ENCRYPTION_KEY = env("SOCIAL_TOKEN_ENCRYPTION_KEY", default="")
SOCIAL_OAUTH_REDIRECT_BASE = env("SOCIAL_OAUTH_REDIRECT_BASE", default="")
SOCIAL_FACEBOOK_CLIENT_ID = env("SOCIAL_FACEBOOK_CLIENT_ID", default="")
SOCIAL_FACEBOOK_CLIENT_SECRET = env("SOCIAL_FACEBOOK_CLIENT_SECRET", default="")
SOCIAL_INSTAGRAM_CLIENT_ID = env("SOCIAL_INSTAGRAM_CLIENT_ID", default="")
SOCIAL_INSTAGRAM_CLIENT_SECRET = env("SOCIAL_INSTAGRAM_CLIENT_SECRET", default="")
SOCIAL_THREADS_CLIENT_ID = env("SOCIAL_THREADS_CLIENT_ID", default="")
SOCIAL_THREADS_CLIENT_SECRET = env("SOCIAL_THREADS_CLIENT_SECRET", default="")
SOCIAL_YOUTUBE_CLIENT_ID = env("SOCIAL_YOUTUBE_CLIENT_ID", default="")
SOCIAL_YOUTUBE_CLIENT_SECRET = env("SOCIAL_YOUTUBE_CLIENT_SECRET", default="")
SOCIAL_X_CLIENT_ID = env("SOCIAL_X_CLIENT_ID", default="")
SOCIAL_X_CLIENT_SECRET = env("SOCIAL_X_CLIENT_SECRET", default="")

INSTALLED_APPS = [
    # Admin theme — must precede django.contrib.admin
    "unfold",
    "unfold.contrib.filters",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",

    # Third-party
    "storages",
    "imagekit",
    "crispy_forms",
    "crispy_tailwind",

    # Authentication
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",

    # Local apps
    "apps.accounts",
    "apps.core",
    "apps.books",
    "apps.payments",
    "apps.social",
    "apps.newsletter",
    "apps.contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
                "apps.payments.context_processors.paypal",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///" + str(BASE_DIR / "db.sqlite3")),
}

# --- django-allauth ---
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # allauth's own backend — required for email login & social auth
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_FORMS = {"signup": "apps.accounts.forms.SignupForm"}
ACCOUNT_UNIQUE_EMAIL = True
# Temporary policy: do not require email verification during signup/login.
# Change to "mandatory" when SMTP and the production verification flow are ready.
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="none")
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[LivingWord Library] "
ACCOUNT_ADAPTER = "apps.accounts.adapters.CustomAccountAdapter"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "account:profile"
LOGOUT_REDIRECT_URL = "core:home"
ACCOUNT_SIGNUP_REDIRECT_URL = "account:profile"
ACCOUNT_PASSWORD_RESET_REDIRECT_URL = "account_login"

SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- PayPal ---
# Use https://api-m.sandbox.paypal.com during development and
# https://api-m.paypal.com in production. Keep secrets in .env.
PAYPAL_BASE_URL = env("PAYPAL_BASE_URL", default="https://api-m.sandbox.paypal.com")
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_CLIENT_SECRET = env("PAYPAL_CLIENT_SECRET", default="")
PAYPAL_WEBHOOK_ID = env("PAYPAL_WEBHOOK_ID", default="")

# Django 5.2's STORAGES dict is the setting that's actually respected —
# the legacy STATICFILES_STORAGE setting does NOT reliably activate a
# custom staticfiles backend on its own.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# --- Object storage (S3 / Cloudflare R2) ---
# Toggle by setting USE_S3=True in .env once bucket credentials are ready.
# Until then, media files are served locally from MEDIA_ROOT above.
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)  # set for R2
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True          # signed URLs — required for protected ebook files
    AWS_QUERYSTRING_EXPIRE = 3600        # signed link lifetime, seconds
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"  # legacy, harmless to keep
    STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"

# --- Unfold admin theme ---
UNFOLD = {
    "SITE_TITLE": "The Living Word Library — Admin",
    "SITE_HEADER": "The Living Word Library",
    "SITE_SYMBOL": "auto_stories",
    "SITE_LOGO": {
        "light": lambda request: static("images/livingword-logo.png"),
        "dark": lambda request: static("images/livingword-logo.png"),
    },
    "THEME": "auto",
    "COLORS": {
        "primary": {
            "50": "250 246 238",
            "100": "242 231 213",
            "500": "90 27 30",  # wine
            "600": "65 18 20",
            "700": "48 13 15",
        },
        "base": {
            "50": "250 246 238",
            "100": "244 236 223",
            "200": "232 217 195",
            "800": "43 35 30",
            "900": "33 27 23",
        },
    },
    "STYLES": [lambda request: static("css/admin-livingword.css")],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Library",
                "separator": True,
                "items": [
                    {"title": "Books", "icon": "menu_book", "link": "/admin/books/book/"},
                    {"title": "Orders", "icon": "payments", "link": "/admin/payments/order/"},
                    {"title": "PayPal webhooks", "icon": "webhook", "link": "/admin/payments/paypalwebhookevent/"},
                ],
            },
            {
                "title": "Accounts & content",
                "items": [
                    {"title": "Users", "icon": "group", "link": "/admin/accounts/user/"},
                    {"title": "Site settings", "icon": "tune", "link": "/admin/core/sitesettings/"},
                ],
            },
        ],
    },
}
