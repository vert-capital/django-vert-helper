from __future__ import annotations

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


class ActionExecuteSerializer(serializers.Serializer):
    questions = serializers.DictField(
        child=serializers.JSONField(),
        required=True,
        allow_empty=False,
    )
