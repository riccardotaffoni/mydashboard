from django.apps import AppConfig
from django.db.models.signals import post_migrate

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from mydashboard.createsuperuser_if_not_exists import create_superuser
        post_migrate.connect(create_superuser, sender=self)
