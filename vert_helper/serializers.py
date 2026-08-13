from __future__ import annotations

import json

from rest_framework import serializers

from .models import Action, Question


class QuestionSerializer(serializers.ModelSerializer):
    parent_question = serializers.UUIDField(
        source="parent_question_id",
        allow_null=True,
        read_only=True,
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "label",
            "type",
            "options",
            "is_required",
            "parent_question",
            "parent_value",
            "action_kwarg",
            "is_first",
        ]


class ActionListSerializer(serializers.ModelSerializer):
    services = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        read_only=True,
    )
    is_recommended = serializers.BooleanField(read_only=True)

    class Meta:
        model = Action
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "services",
            "status",
            "is_recommended",
            "created_at",
        ]


class ActionDetailSerializer(serializers.ModelSerializer):
    services = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        read_only=True,
    )
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Action
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "services",
            "status",
            "questions",
            "created_at",
            "updated_at",
        ]


class QuestionsField(serializers.Field):
    default_error_messages = {
        "invalid_json": "Formato JSON inválido.",
        "invalid_type": "O campo questions deve ser um objeto.",
    }

    def to_internal_value(self, data):
        if data in (None, ""):
            return {}

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                self.fail("invalid_json")

        if isinstance(data, dict):
            return data

        if hasattr(data, "items"):
            return dict(data.items())

        self.fail("invalid_type")

    def to_representation(self, value):
        return value


class ActionExecuteSerializer(serializers.Serializer):
    questions = QuestionsField(default=dict)
