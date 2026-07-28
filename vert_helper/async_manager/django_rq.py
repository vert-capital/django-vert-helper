from __future__ import annotations


def register(interval_seconds: int) -> str:
    try:
        import django_rq
        from django_rq.models import DjangoJob
    except ImportError:
        return "django_rq nao instalado. Nenhuma tarefa registrada."

    from vert_helper.tasks import (
        run_health_checks_task,
        run_health_logs_cleanup_task,
    )

    scheduler = django_rq.get_scheduler("default")
    jobs = [
        (
            "vert_helper_health_checks",
            run_health_checks_task,
            interval_seconds,
        ),
        (
            "vert_helper_health_logs_cleanup",
            run_health_logs_cleanup_task,
            24 * 60 * 60,
        ),
    ]

    for job_id, func, interval in jobs:
        existing = DjangoJob.objects.filter(id=job_id).first()
        if existing:
            existing.delete()

        scheduler.schedule(
            scheduled_time=None,
            func=func,
            interval=interval,
            repeat=None,
            id=job_id,
        )

    return (
        "Scheduler rq configurado. "
        f"Health check: {interval_seconds}s, limpeza: 24h."
    )
