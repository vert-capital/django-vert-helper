from __future__ import annotations


def register(interval_seconds: int) -> str:
    try:
        from django_q.models import Schedule
        from django_q.tasks import schedule
    except ImportError:
        return "django_q nao instalado. Nenhuma tarefa registrada."

    entries = [
        (
            "vert_helper_health_checks",
            "vert_helper.tasks.run_health_checks_task",
            max(1, interval_seconds // 60),
        ),
        (
            "vert_helper_health_logs_cleanup",
            "vert_helper.tasks.run_health_logs_cleanup_task",
            24 * 60,
        ),
    ]

    for schedule_name, task_path, minutes in entries:
        existing = Schedule.objects.filter(name=schedule_name).first()
        if existing:
            existing.schedule_type = Schedule.MINUTES
            existing.minutes = minutes
            existing.func = task_path
            existing.save(
                update_fields=["schedule_type", "minutes", "func"]
            )
            continue

        schedule(
            task_path,
            name=schedule_name,
            schedule_type=Schedule.MINUTES,
            minutes=minutes,
            repeats=-1,
        )

    return (
        "Scheduler django_q configurado. "
        f"Health check: {interval_seconds}s, limpeza: 24h."
    )
