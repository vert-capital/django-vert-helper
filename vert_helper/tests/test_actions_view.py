from __future__ import annotations

from django.test import TestCase

from vert_helper.models import Action, Service, ServiceHealth


class ActionViewSetTests(TestCase):
    def test_actions_list_does_not_raise_field_error(self):
        service = Service.all_objects.create(name="S3", is_active=True)
        action = Action.objects.create(
            slug="generate-report",
            name="Generate Report",
            description="",
            function_path="app.actions.generate_report",
            status=Action.Status.ACTIVE,
        )
        action.services.add(service)

        response = self.client.get("/api/helper/v1/actions/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["slug"], "generate-report")
        self.assertFalse(payload["results"][0]["is_recommended"])

    def test_actions_list_marks_recommended_when_service_failed(self):
        service_failed = Service.all_objects.create(name="KAFKA", is_active=True)
        service_ok = Service.all_objects.create(name="POSTGRES", is_active=True)

        action_recommended = Action.objects.create(
            slug="execute-without-kafka",
            name="Execute Without Kafka",
            description="",
            function_path="app.actions.execute_without_kafka",
            status=Action.Status.ACTIVE,
        )
        action_recommended.services.add(service_failed)

        action_not_recommended = Action.objects.create(
            slug="sync-cache",
            name="Sync Cache",
            description="",
            function_path="app.actions.sync_cache",
            status=Action.Status.ACTIVE,
        )
        action_not_recommended.services.add(service_ok)

        ServiceHealth.objects.create(
            service=service_failed,
            status=ServiceHealth.Status.FAILED,
            message="timeout",
        )
        ServiceHealth.objects.create(
            service=service_ok,
            status=ServiceHealth.Status.OK,
            message=None,
        )

        response = self.client.get("/api/helper/v1/actions/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertTrue(payload["results"][0]["is_recommended"])
        self.assertEqual(
            payload["results"][0]["slug"],
            "execute-without-kafka",
        )
