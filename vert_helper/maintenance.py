from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from vert_helper.models import ServiceHealth


def cleanup_service_health_logs(retention_days: int = 30) -> int:
    cutoff = timezone.now() - timedelta(days=max(1, retention_days))
    deleted, _ = ServiceHealth.objects.filter(checked_at__lt=cutoff).delete()
    return deleted
