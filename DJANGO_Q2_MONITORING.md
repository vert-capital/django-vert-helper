# 🚀 Django-Q2 Clusters Monitoring - Quick Start

## Problema
Clusters Django-Q2 podem morrer sem aviso. Se 1 cluster fica travado ou cai, a fila degrada. Você precisa saber.

## Solução
Health check integrado com `Service` e `ServiceHealth` existentes, usando **estratégia combinada**:
1. **Stats**: Cluster gerando estatísticas?
2. **Heartbeat**: Tasks sendo processadas?

---

## ⚡ Setup (5 minutos)

### 1. Adicione ao `settings.py`

```python
# Configure suas filas Django-Q2
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

# Configure VERT_HELPER para monitorar cada fila
VERT_HELPER = {
    "SCHEDULER": "django_q",
    "HEALTH_CHECK_INTERVAL": 300,  # 5 minutos
    "SERVICES": {
        # Monitorar fila "default"
        "q2_default": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "default",
                "expected_count": 1,  # Opcional: quantos clusters esperados
            },
        },
        
        # Monitorar fila "long"
        "q2_long": {
            "function": "vert_helper.health_checks.django_q2.check_django_q2_queue",
            "context": {
                "queue_name": "long",
                "expected_count": 1,
            },
        },
        
        # Adicione mais filas conforme necessário
    },
}
```

### 2. Inicie seus clusters

```bash
# Terminal 1: Cluster default
python manage.py qcluster

# Terminal 2: Cluster long
Q_CLUSTER_NAME=long python manage.py qcluster
```

### 3. Registre o health check

```bash
python manage.py vert_helper_setup
```

---

## 📊 O que você vai ver

### Tudo OK
```
Service: "q2_default"
ServiceHealth:
  status: "OK"
  message: "OK: Fila 'default' respondendo"
  checked_at: 2026-07-20 14:30:00
```

### Cluster Travado
```
Service: "q2_default"
ServiceHealth:
  status: "FAILED"
  message: "Fila 'default': Cluster travado? 15 tasks aguardando, nenhuma processada recentemente."
  checked_at: 2026-07-20 14:35:00
```

### Cluster Down
```
Service: "q2_default"
ServiceHealth:
  status: "FAILED"
  message: "Fila 'default': Cluster não respondendo. Sem estatísticas."
  checked_at: 2026-07-20 14:40:00
```

---

## 🔍 Verificar em Tempo Real

### Via Django Shell
```python
from vert_helper.models import ServiceHealth

# Ver último status
health = ServiceHealth.objects.filter(
    service__name="q2_default"
).latest("checked_at")

print(f"Status: {health.status}")
print(f"Message: {health.message}")
```

### Via Django Admin
1. Acesse `/admin/vert_helper/servicehealth/`
2. Filtre por `service.name = "q2_default"` (ou outra fila)
3. Veja histórico de verificações

---

## ⚙️ Estratégia de Detecção

### Passo 1: Verificar Stats
```
Cluster.get_all() retorna dados?
├─ SIM → Cluster respondendo
└─ NÃO → Cluster DOWN (FAILED)
```

### Passo 2: Verificar Heartbeat (últimos 60s)
```
Tasks processadas nos últimos 60 segundos?
├─ SIM → Cluster processando ativamente (OK)
└─ NÃO → Verificar passo 3
```

### Passo 3: Verificar se Há Tasks Pendentes
```
Tasks aguardando na fila?
├─ SIM → Cluster TRAVADO (FAILED) - não está processando!
└─ NÃO → Cluster OK (vazio é normal)
```

---

## 🎯 Casos de Uso

### Caso 1: Verificação Automática (Recomendado)
```bash
# Uma vez registrado no settings, verifica a cada 5 minutos
# Dados em ServiceHealth.objects.latest()
```

### Caso 2: Verificação Manual
```python
from vert_helper.health_checks.django_q2 import check_django_q2_queue

result = check_django_q2_queue({
    "queue_name": "default",
    "expected_count": 1,
})
print(f"{result.status}: {result.message}")
```

### Caso 3: Múltiplas Filas
```python
# settings.py - monitorar cada fila separadamente
VERT_HELPER = {
    "SERVICES": {
        "q2_default": {...},
        "q2_long": {...},
        "q2_priority": {...},
    },
}

# Cada fila terá seu próprio ServiceHealth
```

---

## 🔧 Troubleshooting

### "django_q não instalado"
```bash
pip install django-q2
# Adicione ao INSTALLED_APPS
# Configure Q_CLUSTER em settings.py
```

### "Cluster não respondendo"
```bash
# Verifique se cluster está rodando
ps aux | grep qcluster

# Ou inicie novamente
python manage.py qcluster
```

### "Cluster travado - X tasks aguardando"
```python
# Investigar qual task está travando
from django_q.models import OrmQ
OrmQ.objects.filter(lock=None,).count()

# Ou verificar tasks falhadas
from django_q.models import Task
Task.objects.filter(name="default", success=False).order_by("-stopped")[:5]
```

---

## 📝 Múltiplas Filas vs Múltiplos Clusters

```
Fila "default":
├─ 1 cluster processando todas as tasks

Fila "long":
├─ 1 cluster separado para tasks longas

Fila "priority":
├─ 1 cluster separado para tasks prioritárias

→ Cada fila tem seu próprio health check
→ Se 1 fila cai, outras continuam
```

---

## 📈 Próximas Versões (Futuro)

Quando quiser expandir:
- [ ] Histórico de crashes por cluster
- [ ] Motivo por que clusters morreram
- [ ] Alertas automáticos (Slack/Email)
- [ ] Dashboard com métricas
- [ ] Auto-recovery de clusters

Por enquanto, foco: **Cluster respondendo?**

---

## 📝 Resumo

| Item | Status |
|------|--------|
| Setup | ✅ 5 min |
| Histórico | ✅ Automático (ServiceHealth) |
| Múltiplas Filas | ✅ Suportado |
| Alertas | 🔲 Futuro (você decide como) |
| Complexidade | ✅ Simples |
