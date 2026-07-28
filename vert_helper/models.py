from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveServiceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Service(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    objects = ActiveServiceManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ServiceHealth(models.Model):
    class Status(models.TextChoices):
        OK = "OK", "OK"
        FAILED = "FAILED", "FAILED"
        UNKNOWN = "UNKNOWN", "UNKNOWN"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="health_logs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNKNOWN,
    )
    message = models.TextField(blank=True, null=True)
    checked_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["service", "-checked_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.service.name} - {self.status}"


class Action(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(
        Service,
        related_name="actions",
        blank=True,
    )
    function_path = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.slug


class Question(TimeStampedModel):
    class Type(models.TextChoices):
        RADIO = "radio", "Radio"
        TEXT = "text", "Text"
        TEXTAREA = "textarea", "Textarea"
        FILE = "file", "File"
        SELECT = "select", "Select"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=Type.choices)
    options = models.JSONField(blank=True, null=True)
    is_required = models.BooleanField(default=True)
    parent_question = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
        help_text="Pergunta pai que habilita esta pergunta quando respondida com parent_value.",
    )
    parent_value = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Valor da resposta da pergunta pai que habilita esta pergunta.",
    )
    action_kwarg = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nome do argumento que será passado para a função da action.",
    )
    is_first = models.BooleanField(
        default=False,
        help_text="Indica se esta é a primeira pergunta da action.",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["action", "is_first"]),
            models.Index(fields=["parent_question", "parent_value"]),
        ]

    def clean(self):
        if (
            self.parent_question
            and self.parent_question.action_id != self.action_id
        ):
            raise ValidationError(
                "parent_question deve pertencer a mesma action."
            )

    def __str__(self) -> str:
        return self.label


class ActionExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    responses = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="vert_helper_action_executions",
    )
    executed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["action", "-executed_at"]),
            models.Index(fields=["executed_by"]),
        ]

    def __str__(self) -> str:
        return f"{self.action.slug} @ {self.executed_at.isoformat()}"
