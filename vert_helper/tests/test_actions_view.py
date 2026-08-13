from __future__ import annotations

import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from vert_helper.models import Action, Service, ServiceHealth
from vert_helper.registry import (
    RegisteredAction,
    clear_registered_actions,
    register_action,
)


class ActionViewSetTests(TestCase):
    def setUp(self):
        clear_registered_actions()

    def tearDown(self):
        clear_registered_actions()

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

    def test_execute_accepts_multipart_with_file_upload(self):
        action = Action.objects.create(
            slug="import-users",
            name="Import Users",
            description="",
            function_path="app.actions.import_users",
            status=Action.Status.ACTIVE,
        )

        captured = {}

        def import_users(payload):
            captured["payload"] = payload
            file_obj = payload["csv_file"]
            return {
                "status": "success",
                "filename": file_obj.name,
                "has_content": bool(file_obj.read()),
            }

        register_action(
            RegisteredAction(
                slug=action.slug,
                name=action.name,
                description=action.description,
                services=(),
                function_path=action.function_path,
                function=import_users,
            )
        )

        upload = SimpleUploadedFile(
            "users.csv",
            b"name,email\nJane,jane@example.com\n",
            content_type="text/csv",
        )

        response = self.client.post(
            f"/api/helper/v1/actions/{action.slug}/execute/",
            {
                "questions": json.dumps({"operation": "upsert"}),
                "csv_file": upload,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["filename"], "users.csv")
        self.assertTrue(payload["has_content"])
        self.assertEqual(captured["payload"]["operation"], "upsert")
        self.assertEqual(captured["payload"]["csv_file"].name, "users.csv")

        action.refresh_from_db()
        execution = action.executions.first()
        self.assertEqual(execution.responses["operation"], "upsert")
        self.assertEqual(execution.responses["csv_file"]["name"], "users.csv")
        self.assertEqual(execution.responses["csv_file"]["content_type"], "text/csv")
