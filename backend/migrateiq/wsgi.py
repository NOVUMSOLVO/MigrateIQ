"""
WSGI config for migrateiq project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'migrateiq.settings')

application = get_wsgi_application()
