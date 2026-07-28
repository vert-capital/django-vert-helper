from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from vert_helper.models import Service, ServiceHealth

from .types import HealthCheckResult
from .utils import import_callable, normalize_result


def _get_service_config(service_name: str) -> dict:
    config = getattr(settings, "VERT_HELPER", {}) or {}
    services_cfg = config.get("SERVICES", {})
    if not isinstance(services_cfg, dict):
        return {}
    return services_cfg.get(service_name, {})


def _validate_status(status: str) -> str:
    valid_statuses = {choice[0] for choice in ServiceHealth.Status.choices}
    return status if status in valid_statuses else ServiceHealth.Status.UNKNOWN


def run_health_check_for_service(service_name: str) -> ServiceHealth:
    service_cfg = _get_service_config(service_name)

    service = Service.objects.filter(name=service_name).first()
    if not service:
        service = Service.all_objects.create(name=service_name, is_active=True)

    function_path = service_cfg.get("function")
    if not function_path:
        result = HealthCheckResult(
            status=ServiceHealth.Status.UNKNOWN,
            message="Function de health check nao configurada",
        )
    else:
        try:
            check_callable = import_callable(function_path)
            context = service_cfg.get("context", {})
            raw_result = check_callable(context)
            result = normalize_result(
                raw_result,
                fallback_status=ServiceHealth.Status.UNKNOWN,
            )
        except Exception as exc:
            result = HealthCheckResult(
                status=ServiceHealth.Status.FAILED,
                message=str(exc),
            )

    return ServiceHealth.objects.create(
        service=service,
        status=_validate_status(result.status),
        message=result.message,
        checked_at=timezone.now(),
    )


def run_health_checks(force_only_active: bool = True) -> list[ServiceHealth]:
    queryset = (
        Service.objects.all()
        if force_only_active
        else Service.all_objects.all()
    )

    return [run_health_check_for_service(service.name) for service in queryset]
