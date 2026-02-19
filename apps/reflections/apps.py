from django.apps import AppConfig


class ReflectionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reflections"
    label = "reflections"

    def ready(self):
        from . import signals  # noqa