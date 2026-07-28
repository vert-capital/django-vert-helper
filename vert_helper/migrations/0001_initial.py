import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Action",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("name", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("function_path", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="ActionExecution",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("responses", models.JSONField(default=dict)),
                ("result", models.JSONField(default=dict)),
                (
                    "executed_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "action",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="executions",
                        to="vert_helper.action",
                    ),
                ),
                (
                    "executed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="vert_helper_action_executions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-executed_at"],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("label", models.CharField(max_length=255)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("radio", "Radio"),
                            ("text", "Text"),
                            ("textarea", "Textarea"),
                            ("file", "File"),
                            ("select", "Select"),
                        ],
                        max_length=20,
                    ),
                ),
                ("options", models.JSONField(blank=True, null=True)),
                ("is_required", models.BooleanField(default=True)),
                (
                    "parent_value",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "action_kwarg",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                    ),
                ),
                ("is_first", models.BooleanField(default=False)),
                (
                    "action",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="vert_helper.action",
                    ),
                ),
                (
                    "parent_question",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="vert_helper.question",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="ServiceHealth",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("OK", "OK"),
                            ("FAILED", "FAILED"),
                            ("UNKNOWN", "UNKNOWN"),
                        ],
                        default="UNKNOWN",
                        max_length=20,
                    ),
                ),
                ("message", models.TextField(blank=True, null=True)),
                (
                    "checked_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="health_logs",
                        to="vert_helper.service",
                    ),
                ),
            ],
            options={
                "ordering": ["-checked_at"],
            },
        ),
        migrations.AddField(
            model_name="action",
            name="services",
            field=models.ManyToManyField(
                blank=True,
                related_name="actions",
                to="vert_helper.service",
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["action", "is_first"],
                name="vert_helper_action__e62053_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="question",
            index=models.Index(
                fields=["parent_question", "parent_value"],
                name="vert_helper_parent__c9808f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="actionexecution",
            index=models.Index(
                fields=["action", "-executed_at"],
                name="vert_helper_action__f86d59_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="actionexecution",
            index=models.Index(
                fields=["executed_by"],
                name="vert_helper_executed_0f1579_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="servicehealth",
            index=models.Index(
                fields=["service", "-checked_at"],
                name="vert_helper_service_9d888f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="servicehealth",
            index=models.Index(
                fields=["status"],
                name="vert_helper_status_f98fe0_idx",
            ),
        ),
    ]
