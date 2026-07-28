"""
Health check para monitorar workers Django-RQ.

Se 1 worker de 20 morrer, é FAILED.
Se todos estão vivos, é OK.
Se django_rq não está instalado, é UNKNOWN.
"""

from __future__ import annotations

from .types import HealthCheckResult


def check_rq_workers_alive(context: dict | None = None) -> HealthCheckResult:
    """
    Verifica se workers Django-RQ estão vivos.

    Args:
        context: Dict com:
            - expected_count: (int, opcional) Quantos workers são esperados

    Returns:
        HealthCheckResult com status OK, FAILED ou UNKNOWN
    """
    try:
        import django_rq
    except ImportError:
        return HealthCheckResult(
            status="UNKNOWN",
            message="django_rq não instalado",
        )

    context = context or {}
    expected_count = context.get("expected_count")

    try:
        connection = django_rq.get_connection()
        workers = django_rq.Worker.all(connection=connection)

        active_count = len(workers)

        # Se nenhum worker ativo
        if active_count == 0:
            return HealthCheckResult(
                status="FAILED",
                message="Nenhum worker ativo. Cluster RQ parado.",
            )

        # Se expected_count foi fornecido e está faltando workers
        if expected_count is not None:
            if active_count < expected_count:
                missing = expected_count - active_count
                return HealthCheckResult(
                    status="FAILED",
                    message=f"{active_count}/{expected_count} workers ativos. {missing} worker(s) faltando.",
                )

        if expected_count:
            message = f"OK: {active_count}/{expected_count} workers ativos"
        else:
            message = f"OK: {active_count} worker(s) ativo(s)"

        return HealthCheckResult(
            status="OK",
            message=message,
        )

    except Exception as e:
        return HealthCheckResult(
            status="FAILED",
            message=f"Erro ao conectar ao Redis/RQ: {str(e)}",
        )
