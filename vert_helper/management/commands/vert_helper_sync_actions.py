from django.core.management.base import BaseCommand

from vert_helper.sync import sync_actions_from_registry


class Command(BaseCommand):
    help = "Sincroniza actions registradas com @helper_action."

    def handle(self, *args, **options):
        result = sync_actions_from_registry()
        self.stdout.write(self.style.SUCCESS("Actions sincronizadas."))
        self.stdout.write(f"Criadas: {result['created']}")
        self.stdout.write(f"Atualizadas: {result['updated']}")
        self.stdout.write(f"Deletadas: {result['deleted']}")
