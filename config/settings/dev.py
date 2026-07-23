from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Faster local iteration: serve media locally regardless of USE_S3
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
