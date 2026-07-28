from __future__ import annotations

from django.conf import settings

from . import django_q as django_q_manager
from . import django_rq as django_rq_manager


def ensure_scheduler_registration() -> str:
    config = getattr(settings, "VERT_HELPER", {}) or {}
    scheduler = config.get("SCHEDULER")
    interval = int(config.get("HEALTH_CHECK_INTERVAL") or 600)

    if not scheduler:
        return "SCHEDULER vazio. Nenhuma tarefa agendada."

    normalized = str(scheduler).strip().lower()
    if normalized == "django_q":
        return django_q_manager.register(interval)
    if normalized == "rq":
        return django_rq_manager.register(interval)

    return f"Scheduler '{normalized}' nao suportado."
