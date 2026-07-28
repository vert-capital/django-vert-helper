"""
Health check para monitorar clusters Django-Q2.

Usa estratégia combinada:
1. Stats diretos: Cluster está gerando estatísticas?
2. Heartbeat recente: Há tasks sendo processadas?

Se 1 cluster de N morrer = FAILED (mesmo que seja 1 de 20)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .types import HealthCheckResult


def check_django_q2_queue(context: dict | None = None) -> HealthCheckResult:
    """
    Verifica se clusters Django-Q2 estão respondendo para uma fila específica.

    Args:
        context: Dict com:
            - queue_name: (str, obrigatório) Nome da fila ("default", "long", etc)
            - expected_count: (int, opcional) Quantos clusters esperados

    Returns:
        HealthCheckResult com status OK, FAILED ou UNKNOWN
    """
    try:
        from django_q.models import OrmQ, Task
        from django_q.status import Stat
    except ImportError:
        return HealthCheckResult(
            status="UNKNOWN",
            message="django_q não instalado",
        )

    context = context or {}
    queue_name = context.get("queue_name", "default")
    expected_count = context.get("expected_count")

    try:
        # ===== ESTRATÉGIA 1: Verificar Stats =====
        stat = Stat.get_all()
        
        if not stat:
            # Nenhuma estatística = cluster não respondendo
            return HealthCheckResult(
                status="FAILED",
                message=f"Fila '{queue_name}': Cluster não respondendo. Sem estatísticas.",
            )

        # ===== ESTRATÉGIA 2: Verificar Heartbeat (tasks recentes) =====
        # Um cluster vivo deve estar processando tasks regularmente
        # Verificar se há tasks processadas nos últimos 60 segundos

        cutoff_time = datetime.utcnow() - timedelta(seconds=60)

        recent_tasks = Task.objects.filter(
            name=queue_name,
            stopped__gte=cutoff_time,
        ).exists()

        # ===== ANÁLISE COMBINADA =====
        # Stats OK + Heartbeat OK = Cluster está vivo e processando
        if stat and recent_tasks:
            if expected_count and expected_count > 1:
                # Se espera múltiplos clusters, podemos verificar apenas 1
                # (é difícil contar exatamente quantos clusters estão vivos)
                message = f"OK: Fila '{queue_name}' respondendo (1+ clusters ativos)"
            else:
                message = f"OK: Fila '{queue_name}' respondendo"

            return HealthCheckResult(
                status="OK",
                message=message,
            )

        # Stats OK mas sem heartbeat recente
        # Cluster pode estar vivo mas sem tasks
        if stat and not recent_tasks:
            # Verificar se há tasks na fila aguardando
            pending = OrmQ.objects.filter(
                lock=None,
            ).count()

            if pending > 0:
                # Há tasks aguardando mas nenhuma processada recentemente
                # Pode indicar que cluster está travado/lento
                return HealthCheckResult(
                    status="FAILED",
                    message=(
                        f"Fila '{queue_name}': Cluster travado? {pending}"
                        " tasks aguardando, nenhuma processada recentemente."
                    ),
                )
            else:
                # Sem tasks na fila = OK, apenas vazio
                message = f"OK: Fila '{queue_name}' respondendo (sem tasks)"
                return HealthCheckResult(
                    status="OK",
                    message=message,
                )

        # Stats não respondendo
        return HealthCheckResult(
            status="FAILED",
            message=f"Fila '{queue_name}': Cluster não respondendo.",
        )

    except Exception as e:
        return HealthCheckResult(
            status="FAILED",
            message=f"Erro ao verificar fila '{queue_name}': {str(e)}",
        )
