from __future__ import annotations

from django.conf import settings

from vert_helper.health_checks import run_health_checks
from vert_helper.maintenance import cleanup_service_health_logs


def run_health_checks_task() -> int:
    results = run_health_checks(force_only_active=True)
    return len(results)


def run_health_logs_cleanup_task() -> int:
    config = getattr(settings, "VERT_HELPER", {}) or {}
    retention_days = int(config.get("HEALTH_LOG_RETENTION_DAYS") or 30)
    return cleanup_service_health_logs(retention_days=retention_days)
