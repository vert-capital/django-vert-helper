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


class ActionExecuteSerializer(serializers.Serializer):
    questions = serializers.DictField(required=True, allow_empty=False)

    def to_internal_value(self, data):
        if hasattr(data, "dict"):
            mutable_data = data.dict()
        else:
            mutable_data = dict(data)

        questions = mutable_data.get("questions")

        if isinstance(questions, str):
            try:
                mutable_data["questions"] = json.loads(questions)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError(
                    {"questions": "Campo questions deve conter um JSON valido."}
                ) from exc

        return super().to_internal_value(mutable_data)
