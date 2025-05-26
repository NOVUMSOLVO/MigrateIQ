"""
ASGI config for migrateiq project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'migrateiq.settings')

application = get_asgi_application()
