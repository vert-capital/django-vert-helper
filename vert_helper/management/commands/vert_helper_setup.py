from django.core.management.base import BaseCommand

from vert_helper.async_manager import ensure_scheduler_registration
from vert_helper.sync import (
    sync_actions_from_registry,
    sync_services_from_settings,
)
from vert_helper.management.utils import create_helper_auth_user


class Command(BaseCommand):
    help = "Setup completo do vert_helper (services + actions + scheduler + auth user)."

    def handle(self, *args, **options):
        auth_result = create_helper_auth_user(self.stdout, self.style)
        services_result = sync_services_from_settings()
        actions_result = sync_actions_from_registry()
        scheduler_message = ensure_scheduler_registration()

        self.stdout.write(
            self.style.SUCCESS("Setup do vert_helper concluido.")
        )
        if auth_result:
            self.stdout.write(auth_result)
        self.stdout.write(
            "Services -> "
            f"Criados: {services_result['created']}, "
            f"Reativados: {services_result['reactivated']}, "
            f"Desativados: {services_result['deactivated']}"
        )
        self.stdout.write(
            "Actions -> "
            f"Criadas: {actions_result['created']}, "
            f"Atualizadas: {actions_result['updated']}, "
            f"Deletadas: {actions_result['deleted']}"
        )
        self.stdout.write(f"Scheduler -> {scheduler_message}")
