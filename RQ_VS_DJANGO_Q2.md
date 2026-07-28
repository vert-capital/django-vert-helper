# 📚 RQ vs Django-Q2 - Guia Comparativo

## Resumo Executivo

| Aspecto | Django-RQ | Django-Q2 |
|---------|-----------|-----------|
| **Health Check** | `check_rq_workers_alive()` | `check_django_q2_queue()` |
| **O que monitora** | Workers nomeados em filas | Clusters respondendo por fila |
| **Múltiplas filas** | ✅ Sim (default, high, low, ...) | ✅ Sim (default, long, ...) |
| **Configuração** | 1 health check geral | 1 health check POR fila |
| **Service Name** | "rq_workers" | "q2_<fila>" |
| **Status** | OK, FAILED | OK, FAILED |
| **Detecção** | Lista workers | Stats + Heartbeat |

---

## 🚀 Implementação Rápida

### Projeto usando Django-RQ

```python
# settings.py
RQ_QUEUES = {
    "default": {"HOST": "localhost", "PORT": 6379, "DB": 0},
    "high": {"HOST": "localhost", "PORT": 6379, "DB": 0},
}

VERT_HELPER = {
    "SCHEDULER": "rq",
    "SERVICES": {
        "rq_workers": {
            "function": "vert_helper.health_checks.rq_workers.check_rq_workers_alive",
            "context": {
                "expected_count": 3,  # Quantos workers você espera
            },
        },
    },
}
```

```bash
# Iniciar workers
python manage.py rqworker default --name worker1
python manage.py rqworker default --name worker2
python manage.py rqworker high --name worker3
```

---

### Projeto usando Django-Q2

```python
# settings.py
Q_CLUSTER = {
    "name": "default",
    "workers": 4,
}

ALT_CLUSTERS = {
    "long": {
        "name": "long",
        "workers": 2,
    },
}

VERT_HELPER = {
    "SCHEDULER": "django_q",
    "SERVICES": {
        "q2_default": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "default",
            },
        },
        "q2_long": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "long",
            },
        },
    },
}
```

```bash
# Iniciar clusters
python manage.py qcluster  # default
Q_CLUSTER_NAME=long python manage.py qcluster  # long
```

---

## 📋 Dados Salvos em ServiceHealth

### RQ
```python
ServiceHealth(
    service__name="rq_workers",
    status="OK" | "FAILED",
    message="3/3 workers ativos" | "2/3 workers ativos. 1 faltando.",
)
```

### Q2
```python
ServiceHealth(
    service__name="q2_default",
    status="OK" | "FAILED",
    message="OK: Fila 'default' respondendo" | "Cluster travado? 10 tasks aguardando...",
)

ServiceHealth(
    service__name="q2_long",
    status="OK" | "FAILED",
    message="OK: Fila 'long' respondendo" | "Cluster não respondendo.",
)
```

---

## 🔍 Comparação de Cenários

### Cenário: 1 Worker/Cluster Morreu

**Django-RQ:**
```
Expected: 3 workers
Alive: 2 workers
Status: FAILED
Message: "2/3 workers ativos. 1 faltando."
```

**Django-Q2:**
```
Fila: "default"
Stats: OK
Heartbeat: Nenhuma task nos últimos 60s
Pending: 5 tasks aguardando
Status: FAILED
Message: "Cluster travado? 5 tasks aguardando, nenhuma processada recentemente."
```

---

### Cenário: Nenhum Worker/Cluster

**Django-RQ:**
```
Expected: 3 workers
Alive: 0 workers
Status: FAILED
Message: "Nenhum worker ativo. Cluster RQ parado."
```

**Django-Q2:**
```
Fila: "default"
Stats: None (sem estatísticas)
Status: FAILED
Message: "Cluster não respondendo. Sem estatísticas."
```

---

### Cenário: Tudo OK

**Django-RQ:**
```
Expected: 3 workers
Alive: 3 workers
Status: OK
Message: "OK: 3/3 workers ativos"
```

**Django-Q2:**
```
Fila: "default"
Stats: OK
Heartbeat: Tasks processadas nos últimos 60s
Status: OK
Message: "OK: Fila 'default' respondendo"
```

---

## ✅ Checklist de Implementação

### Django-RQ
- [ ] Instalar: `pip install django-rq`
- [ ] Adicionar `django_rq` a `INSTALLED_APPS`
- [ ] Configurar `RQ_QUEUES` no settings
- [ ] Adicionar health check em `VERT_HELPER["SERVICES"]`
- [ ] Executar `python manage.py vert_helper_setup`
- [ ] Iniciar workers: `python manage.py rqworker default`

### Django-Q2
- [ ] Instalar: `pip install django-q2`
- [ ] Adicionar `django_q` a `INSTALLED_APPS`
- [ ] Configurar `Q_CLUSTER` e `ALT_CLUSTERS` no settings
- [ ] Adicionar health checks em `VERT_HELPER["SERVICES"]` (1 por fila)
- [ ] Executar `python manage.py vert_helper_setup`
- [ ] Iniciar clusters: `python manage.py qcluster`

---

## 🎯 Quando Usar Qual

### Use Django-RQ se:
- ✅ Precisa processar diferentes tipos de tasks em filas isoladas
- ✅ Quer escalar workers independentemente por fila
- ✅ Quer máxima flexibilidade

### Use Django-Q2 se:
- ✅ Prefere simplicidade com um único cluster
- ✅ Quer task scheduling integrado
- ✅ Já está usando Django-Q2

### Use Ambos (Biblioteca) se:
- ✅ Tem projetos legados que usam ambos
- ✅ Quer padronização de monitoramento

---

## 📞 Documentação Detalhada

- [RQ_WORKERS_MONITORING.md](RQ_WORKERS_MONITORING.md) - Django-RQ
- [DJANGO_Q2_MONITORING.md](DJANGO_Q2_MONITORING.md) - Django-Q2
