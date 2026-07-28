from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from vert_helper.maintenance import cleanup_service_health_logs
from vert_helper.models import Service, ServiceHealth


class MaintenanceTests(TestCase):
    def test_cleanup_removes_old_health_logs(self):
        service = Service.all_objects.create(name="postgres", is_active=True)

        old_log = ServiceHealth.objects.create(
            service=service,
            status=ServiceHealth.Status.OK,
            checked_at=timezone.now() - timedelta(days=40),
        )
        recent_log = ServiceHealth.objects.create(
            service=service,
            status=ServiceHealth.Status.OK,
            checked_at=timezone.now() - timedelta(days=5),
        )

        deleted = cleanup_service_health_logs(retention_days=30)

        self.assertEqual(deleted, 1)
        self.assertFalse(
            ServiceHealth.objects.filter(pk=old_log.pk).exists()
        )
        self.assertTrue(
            ServiceHealth.objects.filter(pk=recent_log.pk).exists()
        )
