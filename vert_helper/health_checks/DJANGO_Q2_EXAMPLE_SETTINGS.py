"""
Exemplo de configuração Django-Q2 com VERT_HELPER.

Copie e adapte para seu settings.py
"""

# ============================================================================
# EXEMPLO 1: Django-Q2 com Fila Default + Fila Long
# ============================================================================

# Fila principal
Q_CLUSTER = {
    "name": "default",
    "workers": 4,
    "timeout": 300,
    "retry": 60,
}

# Filas alternativas
ALT_CLUSTERS = {
    "long": {
        "name": "long",
        "workers": 2,
        "timeout": 3600,  # 1 hora para tasks longas
        "retry": 120,
    },
    "priority": {
        "name": "priority",
        "workers": 3,
        "timeout": 60,
        "retry": 30,
    },
}

# VERT_HELPER - Health checks para cada fila
VERT_HELPER = {
    "SCHEDULER": "django_q",
    "HEALTH_CHECK_INTERVAL": 300,  # 5 minutos
    "SERVICES": {
        # Health checks existentes
        "postgres": {
            "function": "vert_helper.health_checks.postgres.check_postgres",
        },
        
        # Novo: Health checks de filas Django-Q2
        "q2_default": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "default",
                "expected_count": 1,  # Esperamos 1 cluster na fila default
            },
        },
        
        "q2_long": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "long",
                "expected_count": 1,
            },
        },
        
        "q2_priority": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "priority",
                "expected_count": 1,
            },
        },
    },
}

# ============================================================================
# EXEMPLO 2: Django-Q2 Simples (apenas fila default)
# ============================================================================

# Q_CLUSTER = {
#     "name": "default",
#     "workers": 4,
# }
#
# VERT_HELPER = {
#     "SCHEDULER": "django_q",
#     "HEALTH_CHECK_INTERVAL": 300,
#     "SERVICES": {
#         "q2_cluster": {
#             "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
#             "context": {
#                 "queue_name": "default",
#             },
#         },
#     },
# }

# ============================================================================
# COMO USAR
# ============================================================================

# 1. Registre o health check (uma única vez)
# python manage.py vert_helper_setup

# 2. Inicie clusters em terminais separados
# Terminal 1: python manage.py qcluster
# Terminal 2: Q_CLUSTER_NAME=long python manage.py qcluster
# Terminal 3: Q_CLUSTER_NAME=priority python manage.py qcluster

# 3. Verifique via Django shell
# from vert_helper.models import ServiceHealth
# health = ServiceHealth.objects.filter(
#     service__name="q2_default"
# ).latest("checked_at")
# print(f"Status: {health.status}, Message: {health.message}")

# 4. Histórico completo
# ServiceHealth.objects.filter(service__name__startswith="q2_").order_by("-checked_at")[:20]
