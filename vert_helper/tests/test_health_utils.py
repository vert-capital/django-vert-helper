from __future__ import annotations

from django.test import SimpleTestCase

from vert_helper.health_checks.types import HealthCheckResult
from vert_helper.health_checks.utils import normalize_result


class HealthUtilsTests(SimpleTestCase):
    def test_normalize_result_keeps_dataclass(self):
        result = HealthCheckResult(status="OK", message="fine")

        normalized = normalize_result(result, fallback_status="UNKNOWN")

        self.assertEqual(normalized.status, "OK")
        self.assertEqual(normalized.message, "fine")

    def test_normalize_result_from_tuple(self):
        normalized = normalize_result(("FAILED", "boom"), "UNKNOWN")

        self.assertEqual(normalized.status, "FAILED")
        self.assertEqual(normalized.message, "boom")

    def test_normalize_result_from_dict_without_status(self):
        normalized = normalize_result({"message": "x"}, "UNKNOWN")

        self.assertEqual(normalized.status, "UNKNOWN")
        self.assertEqual(normalized.message, "x")

    def test_normalize_result_with_invalid_type(self):
        normalized = normalize_result(123, "UNKNOWN")

        self.assertEqual(normalized.status, "UNKNOWN")
        self.assertIn("Invalid", normalized.message)
