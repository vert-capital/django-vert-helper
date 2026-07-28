"""
Exemplo de configuração RQ Workers com VERT_HELPER.

Copie e adapte para seu settings.py
"""

# ============================================================================
# EXEMPLO: Django-RQ com Health Check de Workers
# ============================================================================

# 1. Configure RQ_QUEUES (Django-RQ)
RQ_QUEUES = {
    "default": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 0,
        "DEFAULT_RESULT_TTL": 500,
    },
    "high": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 0,
    },
    "low": {
        "HOST": "localhost",
        "PORT": 6379,
        "DB": 0,
    },
}

# 2. Configure VERT_HELPER com health check de workers
VERT_HELPER = {
    "SCHEDULER": "rq",
    "HEALTH_CHECK_INTERVAL": 300,  # 5 minutos
    "SERVICES": {
        # Health checks existentes
        "postgres": {
            "function": "vert_helper.health_checks.postgres.check_postgres",
        },
        
        # Novo: Health check de workers RQ
        "rq_workers": {
            "function": "vert_helper.health_checks.rq_workers.check_rq_workers_alive",
            "context": {
                "expected_count": 3,  # Você espera 3 workers
            },
        },
        
        # Outras funções de health check...
    },
}

# ============================================================================
# COMO USAR
# ============================================================================

# 1. Registre o health check (uma única vez)
# python manage.py vert_helper_setup

# 2. Inicie workers em terminais separados
# Terminal 1: python manage.py rqworker default --name worker1
# Terminal 2: python manage.py rqworker default --name worker2
# Terminal 3: python manage.py rqworker default --name worker3

# 3. Verifique via Django shell
# from vert_helper.models import ServiceHealth
# health = ServiceHealth.objects.filter(
#     service__name="rq_workers"
# ).latest("checked_at")
# print(f"Status: {health.status}, Message: {health.message}")

# 4. Histórico completo
# from vert_helper.models import ServiceHealth
# ServiceHealth.objects.filter(service__name="rq_workers").order_by("-checked_at")[:10]
