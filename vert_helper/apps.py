from django.apps import AppConfig


class VertHelperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vert_helper"
    verbose_name = "Vert Helper"

    def ready(self):
        from . import signals  # noqa: F401

