from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from mydashboard.createsuperuser_if_not_exists import create_superuser
        create_superuser()
