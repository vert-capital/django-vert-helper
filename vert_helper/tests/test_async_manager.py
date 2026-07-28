from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from vert_helper.async_manager.manager import ensure_scheduler_registration


class AsyncManagerTests(SimpleTestCase):
    @override_settings(
        VERT_HELPER={
            "SCHEDULER": "django_q",
            "HEALTH_CHECK_INTERVAL": 600,
        }
    )
    @patch("vert_helper.async_manager.django_q.register")
    def test_uses_django_q_manager(self, mock_register):
        mock_register.return_value = "ok"

        result = ensure_scheduler_registration()

        mock_register.assert_called_once_with(600)
        self.assertEqual(result, "ok")

    @override_settings(
        VERT_HELPER={
            "SCHEDULER": "rq",
            "HEALTH_CHECK_INTERVAL": 120,
        }
    )
    @patch("vert_helper.async_manager.django_rq.register")
    def test_uses_rq_manager(self, mock_register):
        mock_register.return_value = "ok-rq"

        result = ensure_scheduler_registration()

        mock_register.assert_called_once_with(120)
        self.assertEqual(result, "ok-rq")

    @override_settings(VERT_HELPER={})
    def test_returns_message_when_scheduler_not_configured(self):
        result = ensure_scheduler_registration()
        self.assertIn("SCHEDULER vazio", result)

    @override_settings(VERT_HELPER={"SCHEDULER": "abc"})
    def test_returns_message_when_scheduler_is_not_supported(self):
        result = ensure_scheduler_registration()
        self.assertIn("nao suportado", result)
