from __future__ import annotations

from importlib import import_module
from typing import Any

from .types import HealthCheckResult


def import_callable(path: str):
    module_name, func_name = path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, func_name)


def normalize_result(result: Any, fallback_status: str) -> HealthCheckResult:
    if isinstance(result, HealthCheckResult):
        return result

    if isinstance(result, tuple) and len(result) == 2:
        status, message = result
        return HealthCheckResult(
            status=str(status),
            message=str(message) if message else None,
        )

    if isinstance(result, dict):
        status = str(result.get("status", fallback_status))
        message = result.get("message")
        return HealthCheckResult(
            status=status,
            message=str(message) if message else None,
        )

    if isinstance(result, str):
        return HealthCheckResult(status=result)

    return HealthCheckResult(
        status=fallback_status,
        message="Invalid health check return type",
    )
