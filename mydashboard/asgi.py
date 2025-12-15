import os
from django.core.asgi import get_asgi_application

# Metti qui il nome del tuo progetto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mydashboard.settings')

application = get_asgi_application()
