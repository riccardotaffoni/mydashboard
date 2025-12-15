import os
from django.contrib.auth import get_user_model
from django.db import connection

def create_superuser(sender, **kwargs):
    User = get_user_model()

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if not username or not password:
        return

    # sicurezza extra: verifica che la tabella esista
    if "auth_user" not in connection.introspection.table_names():
        return

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
