from __future__ import annotations

from django.test import TestCase, override_settings

from vert_helper.health_checks.engine import run_health_check_for_service
from vert_helper.models import Service, ServiceHealth


def health_ok(_context):
    return {"status": "OK", "message": None}


def health_broken(_context):
    raise RuntimeError("kaboom")


def health_invalid(_context):
    return {"status": "NOT_VALID", "message": "weird"}


class HealthEngineTests(TestCase):
    @override_settings(
        VERT_HELPER={
            "SERVICES": {
                "postgres": {
                    "function": "vert_helper.tests.test_engine.health_ok",
                    "context": {},
                }
            }
        }
    )
    def test_run_health_check_for_service_success(self):
        Service.all_objects.create(name="postgres", is_active=True)

        log = run_health_check_for_service("postgres")

        self.assertEqual(log.status, ServiceHealth.Status.OK)

    @override_settings(
        VERT_HELPER={
            "SERVICES": {
                "postgres": {
                    "function": "vert_helper.tests.test_engine.health_broken",
                    "context": {},
                }
            }
        }
    )
    def test_run_health_check_for_service_exception(self):
        Service.all_objects.create(name="postgres", is_active=True)

        log = run_health_check_for_service("postgres")

        self.assertEqual(log.status, ServiceHealth.Status.FAILED)
        self.assertIn("kaboom", log.message)

    @override_settings(
        VERT_HELPER={
            "SERVICES": {
                "postgres": {
                    "function": "vert_helper.tests.test_engine.health_invalid",
                    "context": {},
                }
            }
        }
    )
    def test_run_health_check_for_service_invalid_status(self):
        Service.all_objects.create(name="postgres", is_active=True)

        log = run_health_check_for_service("postgres")

        self.assertEqual(log.status, ServiceHealth.Status.UNKNOWN)

    @override_settings(VERT_HELPER={"SERVICES": {}})
    def test_run_health_check_for_service_without_function(self):
        Service.all_objects.create(name="postgres", is_active=True)

        log = run_health_check_for_service("postgres")

        self.assertEqual(log.status, ServiceHealth.Status.UNKNOWN)
        self.assertIn("nao configurada", log.message)
