from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS: dict[str, Any] = {
    "PERMISSION_CLASS": "rest_framework.permissions.AllowAny",
    "SCHEDULER": None,
    "HEALTH_CHECK_INTERVAL": 600,
    "HEALTH_CHECK_AUTO_REGISTER": True,
    "HEALTH_LOG_RETENTION_DAYS": 30,
    "SERVICES": {},
    "JWT_AUTH_ENABLE": True,
}

PREFIX = "VERT_HELPER_"


@dataclass(frozen=True)
class VertHelperSettings:
    permission_class: str
    scheduler: str | None
    health_check_interval: int
    health_check_auto_register: bool
    health_log_retention_days: int
    services: dict[str, Any]
    jwt_auth_enable: bool


def _coerce_int(key: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ImproperlyConfigured(f"VERT_HELPER {key} deve ser inteiro.")
    return value


def _coerce_bool(key: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ImproperlyConfigured(f"VERT_HELPER {key} deve ser booleano.")
    return value


def _coerce_str_or_none(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ImproperlyConfigured(
            f"VERT_HELPER {key} deve ser string ou None."
        )
    return value


def _coerce_mapping(key: str, value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ImproperlyConfigured(f"VERT_HELPER {key} deve ser um dict.")
    return dict(value)


def _load_raw_settings() -> dict[str, Any]:
    raw_group = getattr(django_settings, "VERT_HELPER", {})
    if raw_group is None:
        raw_group = {}

    if not isinstance(raw_group, Mapping):
        raise ImproperlyConfigured(
            "VERT_HELPER deve ser um dict no settings.py."
        )

    merged = DEFAULTS.copy()
    merged.update(raw_group)

    for key in DEFAULTS:
        prefixed_key = f"{PREFIX}{key}"
        if hasattr(django_settings, prefixed_key):
            merged[key] = getattr(django_settings, prefixed_key)

    return merged


@lru_cache
def get_vert_helper_settings() -> VertHelperSettings:
    raw = _load_raw_settings()

    return VertHelperSettings(
        permission_class=_coerce_str_or_none(
            "PERMISSION_CLASS",
            raw["PERMISSION_CLASS"],
        )
        or "rest_framework.permissions.AllowAny",
        scheduler=_coerce_str_or_none("SCHEDULER", raw["SCHEDULER"]),
        health_check_interval=_coerce_int(
            "HEALTH_CHECK_INTERVAL",
            raw["HEALTH_CHECK_INTERVAL"],
        ),
        health_check_auto_register=_coerce_bool(
            "HEALTH_CHECK_AUTO_REGISTER",
            raw["HEALTH_CHECK_AUTO_REGISTER"],
        ),
        health_log_retention_days=_coerce_int(
            "HEALTH_LOG_RETENTION_DAYS",
            raw["HEALTH_LOG_RETENTION_DAYS"],
        ),
        services=_coerce_mapping("SERVICES", raw["SERVICES"]),
        jwt_auth_enable=_coerce_bool("JWT_AUTH_ENABLE", raw["JWT_AUTH_ENABLE"]),
    )


def reload_vert_helper_settings() -> None:
    get_vert_helper_settings.cache_clear()
