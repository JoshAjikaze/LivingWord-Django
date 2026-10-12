from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Faster local iteration: serve media locally regardless of USE_S3
# The console backend remains the safe default for development. Set
# EMAIL_BACKEND in .env to SMTP when testing real Gmail verification emails.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# Use plain staticfiles storage in dev/tests — the prod whitenoise manifest
# backend raises MissingStaticFileError when collectstatic hasn't run.
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
