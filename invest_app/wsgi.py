"""WSGI config for invest_app (fallback for non-ASGI deployments)."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invest_app.settings.local")

application = get_wsgi_application()
