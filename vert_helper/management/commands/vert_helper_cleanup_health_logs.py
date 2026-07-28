from django.conf import settings
from django.core.management.base import BaseCommand

from vert_helper.maintenance import cleanup_service_health_logs


class Command(BaseCommand):
    help = "Limpa logs antigos de ServiceHealth com base em retenção."

    def add_arguments(self, parser):
        parser.add_argument(
            "--retention-days",
            type=int,
            help="Dias de retenção dos logs.",
        )

    def handle(self, *args, **options):
        config = getattr(settings, "VERT_HELPER", {}) or {}
        default_retention = int(config.get("HEALTH_LOG_RETENTION_DAYS") or 30)
        retention_days = options.get("retention_days") or default_retention

        deleted = cleanup_service_health_logs(retention_days=retention_days)
        self.stdout.write(
            self.style.SUCCESS(
                f"Limpeza concluida. Registros removidos: {deleted}"
            )
        )
