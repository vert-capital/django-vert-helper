from __future__ import annotations

from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.functions import Lower
from rest_framework import status, viewsets
from rest_framework.decorators import action
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

        autodiscover_actions()
        registered = get_registered_actions().get(action_obj.slug)
        if registered:
            try:
                result = registered.function(responses)
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
            responses=responses,
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
