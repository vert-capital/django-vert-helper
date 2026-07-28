from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from vert_helper.health_checks.kafka import check_kafka
from vert_helper.health_checks.postgres import check_postgres
from vert_helper.health_checks.types import HealthCheckResult


class PostgresHealthCheckTests(SimpleTestCase):
    def test_postgres_returns_unknown_without_database(self):
        result = check_postgres({"host": "localhost"})

        self.assertEqual(result.status, "UNKNOWN")
        self.assertIn("database", result.message)

    @patch("vert_helper.health_checks.postgres.psycopg2.connect")
    def test_postgres_returns_ok_when_query_succeeds(self, mock_connect):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn

        result = check_postgres(
            {
                "host": "localhost",
                "port": 5432,
                "database": "db",
                "user": "postgres",
                "password": "postgres",
            }
        )

        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.status, "OK")

    @patch("vert_helper.health_checks.postgres.psycopg2.connect")
    def test_postgres_returns_failed_when_connection_errors(
        self,
        mock_connect,
    ):
        mock_connect.side_effect = Exception("boom")

        result = check_postgres({"database": "db"})

        self.assertEqual(result.status, "FAILED")
        self.assertIn("boom", result.message)


class KafkaHealthCheckTests(SimpleTestCase):
    def test_kafka_returns_unknown_without_bootstrap_servers(self):
        result = check_kafka({})

        self.assertEqual(result.status, "UNKNOWN")
        self.assertIn("bootstrap_servers", result.message)

    @patch("vert_helper.health_checks.kafka.AdminClient")
    def test_kafka_returns_ok_when_admin_client_works(self, mock_admin_client):
        admin = MagicMock()
        admin.list_topics.return_value = MagicMock()
        mock_admin_client.return_value = admin

        result = check_kafka({"bootstrap_servers": ["localhost:9092"]})

        self.assertEqual(result.status, "OK")

    @patch("vert_helper.health_checks.kafka.AdminClient")
    def test_kafka_returns_failed_on_exception(self, mock_admin_client):
        admin = MagicMock()
        admin.list_topics.side_effect = Exception("kafka down")
        mock_admin_client.return_value = admin

        result = check_kafka({"bootstrap_servers": ["localhost:9092"]})

        self.assertEqual(result.status, "FAILED")
        self.assertIn("kafka down", result.message)
