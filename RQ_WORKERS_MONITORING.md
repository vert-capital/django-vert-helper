# 🚀 RQ Workers Monitoring - Quick Start

## Problema
Workers Django-RQ podem morrer sem aviso. Se 1 de 20 morrer, a fila degrada. Você precisa saber.

## Solução
Health check integrado com `Service` e `ServiceHealth` existentes.

---

## ⚡ Setup (5 minutos)

### 1. Adicione ao `settings.py`

```python
VERT_HELPER = {
    "SCHEDULER": "rq",  # ou "django_q"
    "HEALTH_CHECK_INTERVAL": 300,  # 5 minutos
    "SERVICES": {
        # ... seus outros serviços ...
        
        # Novo: Monitorar workers RQ
        "rq_workers": {
            "function": "vert_helper.health_checks.rq_workers.check_rq_workers_alive",
            "context": {
                "expected_count": 3,  # Quantos workers você espera ter
            },
        },
    },
}
```

### 2. Configure seus workers

```bash
# Terminal 1: Worker default
python manage.py rqworker default --name worker1

# Terminal 2: Worker default  
python manage.py rqworker default --name worker2

# Terminal 3: Worker default
python manage.py rqworker default --name worker3
```

### 3. Registre o health check

```bash
python manage.py vert_helper_setup
```

---

## 📊 O que você vai ver

### Tudo OK
```
Service: "rq_workers"
ServiceHealth:
  status: "OK"
  message: "OK: 3/3 workers ativos"
  checked_at: 2026-07-20 14:30:00
```

### 1 Worker Morreu
```
Service: "rq_workers"
ServiceHealth:
  status: "FAILED"
  message: "2/3 workers ativos. 1 worker(s) faltando."
  checked_at: 2026-07-20 14:35:00
```

### Nenhum Worker
```
Service: "rq_workers"
ServiceHealth:
  status: "FAILED"
  message: "Nenhum worker ativo. Cluster RQ parado."
  checked_at: 2026-07-20 14:40:00
```

---

## 🔍 Verificar em Tempo Real

### Via Django Shell
```python
from vert_helper.models import ServiceHealth

# Ver último status
health = ServiceHealth.objects.filter(
    service__name="rq_workers"
).latest("checked_at")

print(f"Status: {health.status}")
print(f"Message: {health.message}")
print(f"Checked at: {health.checked_at}")
```

### Via API (se configurada)
```bash
curl http://localhost:8000/api/health/
# Retorna todos os serviços com último status
```

### Via Django Admin
1. Acesse `/admin/vert_helper/servicehealth/`
2. Filtre por `service.name = "rq_workers"`
3. Veja histórico de verificações

---

## ⚙️ Opções de Configuração

### Com expected_count (Recomendado)
```python
"rq_workers": {
    "function": "vert_helper.health_checks.rq_workers.check_rq_workers_alive",
    "context": {
        "expected_count": 5,  # Qualquer worker faltando = FAILED
    },
}
```

### Sem expected_count
```python
"rq_workers": {
    "function": "vert_helper.health_checks.rq_workers.check_rq_workers_alive",
}
```
- OK: Se houver pelo menos 1 worker vivo
- FAILED: Se 0 workers
- UNKNOWN: Se django_rq não instalado

---

## 🚨 Casos de Uso

### Caso 1: Verificação Automática (Recomendado)
```bash
# Uma vez registrado no settings, verifica a cada 5 minutos automaticamente
# Dados em ServiceHealth.objects.latest()
# Você pode fazer relatórios/alertas em cima disso
```

### Caso 2: Verificação Manual
```python
from vert_helper.health_checks.rq_workers import check_rq_workers_alive

result = check_rq_workers_alive({"expected_count": 3})
print(f"{result.status}: {result.message}")
```

### Caso 3: Integração com Alertas (Futuro)
```python
# Seu código de alerta pode fazer:
health = ServiceHealth.objects.filter(
    service__name="rq_workers"
).latest("checked_at")

if health.status == "FAILED":
    send_slack_alert(f"⚠️ RQ Workers down: {health.message}")
```

---

## 🔧 Troubleshooting

### "django_rq não instalado"
```bash
pip install django-rq
# Adicione ao INSTALLED_APPS
# Configure RQ_QUEUES em settings.py
```

### "Nenhum worker ativo"
```bash
# Inicie um worker
python manage.py rqworker default

# Ou se usar múltiplas filas
python manage.py rqworker default high low
```

### "expected_count não funciona"
```python
# Certifique-se que todos os workers têm nomes diferentes
python manage.py rqworker default --name worker1
python manage.py rqworker default --name worker2

# Verificar quantos workers estão vivos
from vert_helper.health_checks.rq_workers import check_rq_workers_alive
result = check_rq_workers_alive()
print(result.message)
```

---

## 📈 Próximas Versões (Futuro)

Quando quiser expandir:
- [ ] Histórico de crashes por worker
- [ ] Motivo por que workers morreram
- [ ] Alertas automáticos (Slack/Email)
- [ ] Dashboard com gráficos
- [ ] Auto-recovery de workers

Por enquanto, foco: **Vivo ou Morto?**

---

## 📝 Resumo

| Item | Status |
|------|--------|
| Setup | ✅ 5 min |
| Histórico | ✅ Automático (ServiceHealth) |
| Alertas | 🔲 Futuro (você decide como) |
| Complexidade | ✅ Simples |
