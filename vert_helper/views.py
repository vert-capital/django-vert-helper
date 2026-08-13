from __future__ import annotations

from collections.abc import Mapping

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.functions import Lower
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .health_checks import run_health_checks
from .models import Action, ActionExecution, Question, ServiceHealth
from .permissions import get_authentication_class, get_permission_class
from .registry import get_registered_actions
from .serializers import (
    ActionDetailSerializer,
    ActionExecuteSerializer,
    ActionListSerializer,
)
from .sync import autodiscover_actions


class VertHelperPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class HealthcareView(APIView):
    def get_permissions(self):
        return [AllowAny()]

    def get_authenticators(self):
        return []

    def get(self, request):
        force_refresh = str(
            request.query_params.get("force_refresh", "false")
        ).lower()
        if force_refresh == "true":
            run_health_checks(force_only_active=True)

        latest_logs = {}
        logs = (
            ServiceHealth.objects.select_related("service")
            .filter(service__is_active=True)
            .order_by("service__name", "-checked_at")
        )

        for log in logs:
            service_name = log.service.name
            if service_name in latest_logs:
                continue

            payload = {
                "status": log.status,
                "last_updated": log.checked_at,
            }
            if log.message:
                payload["message"] = log.message

            latest_logs[service_name] = payload

        return Response(latest_logs)


class ActionViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = VertHelperPagination
    lookup_field = "slug"
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    @staticmethod
    def _extract_question_key(field_name: str) -> str:
        if field_name.startswith("questions[") and field_name.endswith("]"):
            return field_name[len("questions[") : -1]
        return field_name

    @classmethod
    def _merge_uploaded_files(cls, responses: dict, files: Mapping[str, UploadedFile]) -> dict:
        merged = dict(responses)
        for field_name, uploaded in files.items():
            question_key = cls._extract_question_key(field_name)
            merged[question_key] = uploaded
        return merged

    @classmethod
    def _to_json_safe(cls, value):
        if isinstance(value, UploadedFile):
            return {
                "name": value.name,
                "size": value.size,
                "content_type": value.content_type,
            }

        if isinstance(value, dict):
            return {
                key: cls._to_json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [cls._to_json_safe(item) for item in value]

        if isinstance(value, tuple):
            return [cls._to_json_safe(item) for item in value]

        return value

    def get_permissions(self):
        return [get_permission_class()()]

    def get_authenticators(self):
        auth_class = get_authentication_class()
        if auth_class:
            return [auth_class()]
        return []

    def get_queryset(self):
        failed_actions = ServiceHealth.objects.filter(
            service__actions=OuterRef("pk"),
            service__is_active=True,
            status=ServiceHealth.Status.FAILED,
        )

        qs = (
            Action.objects.filter(status=Action.Status.ACTIVE)
            .prefetch_related(
                "services",
                Prefetch(
                    "questions",
                    queryset=Question.objects.order_by("created_at"),
                ),
            )
            .annotate(
                is_recommended=Exists(
                    failed_actions
                ),
            )
            .distinct()
            .order_by("-is_recommended", Lower("name"))
        )

        service_name = self.request.query_params.get("service")
        if service_name:
            qs = qs.filter(services__name=service_name)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ActionDetailSerializer
        return ActionListSerializer

    @action(detail=True, methods=["post"], url_path="execute")
    def execute(self, request, slug=None):
        action_obj = self.get_object()
        serializer = ActionExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        responses = serializer.validated_data["questions"]
        responses_with_files = self._merge_uploaded_files(
            responses,
            request.FILES,
        )
        persisted_responses = self._to_json_safe(responses_with_files)

        autodiscover_actions()
        registered = get_registered_actions().get(action_obj.slug)
        if registered:
            try:
                # Responses it's a kwargs dict, so we can unpack it directly into the function call
                action_function = registered.function
                result = action_function(responses_with_files)
            except Exception as exc:
                result = {
                    "status": "error",
                    "message": "Erro ao executar action.",
                    "details": str(exc),
                }
        else:
            result = {
                "status": "info",
                "message": (
                    "Action registrada no banco, "
                    "mas nao carregada no registry. "
                    "Execute o comando vert_helper_setup para sincronizar."
                ),
            }

        execution = ActionExecution.objects.create(
            action=action_obj,
            responses=persisted_responses,
            result=result,
            executed_by=(
                request.user
                if request.user.is_authenticated
                else None
            ),
        )

        return Response(
            execution.result,
            status=status.HTTP_200_OK,
        )
