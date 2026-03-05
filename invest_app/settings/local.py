from .base import *  # noqa

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

# Use console email backend in development — no SMTP needed
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Skip mandatory email verification so dev/test registration works immediately
ACCOUNT_EMAIL_VERIFICATION = "optional"

