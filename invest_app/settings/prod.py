from .base import *  # noqa

DEBUG = False

CORS_ALLOWED_ORIGINS = [
    # Add your production frontend URL here
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
