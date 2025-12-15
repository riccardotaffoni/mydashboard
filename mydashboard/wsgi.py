import os
from django.core.wsgi import get_wsgi_application

# Metti qui il nome del tuo progetto (la cartella che contiene settings.py)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mydashboard.settings')

application = get_wsgi_application()
