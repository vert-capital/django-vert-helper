from __future__ import annotations

from importlib import import_module

from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


def get_permission_class():
    config = getattr(settings, "VERT_HELPER", {}) or {}
    permission_path = config.get("PERMISSION_CLASS")
    jwt_enabled = config.get("JWT_AUTH_ENABLE", True)

    if jwt_enabled:
        return IsAuthenticated

    if not permission_path:
        return AllowAny

    try:
        module_name, class_name = permission_path.rsplit(".", 1)
        module = import_module(module_name)
        permission_class = getattr(module, class_name)
        return permission_class
    except (ValueError, ImportError, AttributeError):
        return AllowAny


def get_authentication_class():
    config = getattr(settings, "VERT_HELPER", {}) or {}
    jwt_enabled = config.get("JWT_AUTH_ENABLE", True)

    if jwt_enabled:
        return JWTAuthentication

    return None
