# django-vert-helper

Biblioteca para health checks de servicos, acoes operacionais e
configuracao centralizada via `settings.py`.

## Instalacao no projeto Django

1. Adicione app em `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "vert_helper.apps.VertHelperConfig",
]
```

2. Configure via bloco unico (recomendado):

```python
VERT_HELPER = {
    "PERMISSION_CLASS": "rest_framework.permissions.AllowAny",
    "SCHEDULER": "django_q",  # ou "rq" ou None
    "HEALTH_CHECK_INTERVAL": 600,
    "HEALTH_CHECK_AUTO_REGISTER": True,
    "HEALTH_LOG_RETENTION_DAYS": 30,
    "SERVICES": {
        "postgres": {
            "function": "vert_helper.health_checks.postgres.check_postgres",
            "context": {
                "host": "localhost",
                "port": 5432,
                "database": "app_db",
                "user": "postgres",
                "password": "postgres",
            },
        },
        "kafka": {
            "function": "vert_helper.health_checks.kafka.check_kafka",
            "context": {
                "bootstrap_servers": ["localhost:9092"],
                "timeout": 3,
            },
        },
        "s3": {
            "function": "vert_helper.health_checks.s3.check_s3",
            "context": {
                "bucket_name": "my-bucket",
                "aws_access_key_id": "key",
                "aws_secret_access_key": "secret",
                "region_name": "us-east-1",
            },
        },
    },
}
```

3. Ou por chaves prefixadas (sobrescreve o bloco para campos simples):

```python
VERT_HELPER_PERMISSION_CLASS = "rest_framework.permissions.IsAuthenticated"
VERT_HELPER_SCHEDULER = "rq"
VERT_HELPER_HEALTH_CHECK_INTERVAL = 300
VERT_HELPER_HEALTH_CHECK_AUTO_REGISTER = True
VERT_HELPER_HEALTH_LOG_RETENTION_DAYS = 15
```

## Uso

```python
from vert_helper import get_vert_helper_settings

cfg = get_vert_helper_settings()

print(cfg.permission_class)
print(cfg.scheduler)
print(cfg.health_check_interval)
print(cfg.health_check_auto_register)
print(cfg.health_log_retention_days)
print(cfg.services)
```

## Registro das APIs

As rotas da biblioteca ja incluem o caminho default `api/helper/v1/...`.

No `urls.py` do seu projeto, basta incluir as URLs da app sem prefixo extra:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path("", include("vert_helper.urls")),
]
```

Endpoints expostos por padrao:

- `GET /api/helper/v1/healthcare/`
- `GET /api/helper/v1/actions/`
- `GET /api/helper/v1/actions/<slug>/`
- `POST /api/helper/v1/actions/<slug>/execute/`

## Comandos de Management

### 1. Setup completo

```bash
python manage.py vert_helper_setup
```

O que faz:

- Sincroniza `Service` com `VERT_HELPER["SERVICES"]` (cria, reativa, desativa)
- Sincroniza `Action` registradas com `@helper_action`
- Registra/atualiza tarefas agendadas se `SCHEDULER` estiver configurado

### 2. Sincronizar apenas actions

```bash
python manage.py vert_helper_sync_actions
```

O que faz:

- Descobre actions com `@helper_action`
- Cria/atualiza ações no banco
- Remove ações orfãs (que nao existem mais no codigo)

### 3. Limpar logs de health checks

```bash
python manage.py vert_helper_cleanup_health_logs
```

Opcional com retenção custom:

```bash
python manage.py vert_helper_cleanup_health_logs --retention-days 15
```

O que faz:

- Remove registros antigos de `ServiceHealth`
- Usa `HEALTH_LOG_RETENTION_DAYS` quando `--retention-days` nao for informado

## Tarefas Agendadas (quando SCHEDULER estiver preenchido)

Se `VERT_HELPER["SCHEDULER"]` estiver com `"django_q"` ou `"rq"`,
o `vert_helper_setup` registra duas tarefas:

### 1. Health checks periódicos

- Tarefa: `vert_helper.tasks.run_health_checks_task`
- Frequencia: `HEALTH_CHECK_INTERVAL` (padrao 600 segundos)
- O que faz: executa health checks dos serviços ativos e grava em `ServiceHealth`

### 2. Limpeza periódica de logs

- Tarefa: `vert_helper.tasks.run_health_logs_cleanup_task`
- Frequencia: a cada 24 horas
- O que faz: remove logs antigos conforme `HEALTH_LOG_RETENTION_DAYS`

Se `SCHEDULER` estiver vazio (`None`), nenhuma tarefa é agendada automaticamente.

### Mais informações
- Manual de uso: `MANUAL_DE_USO.MD`

## Documentacao Tecnica

- Especificacao tecnica da implementacao atual (V1): `docs/v1/ESPECIFICACAO_TECNICA.md`
- Especificacao tecnica agnostica (framework/linguagem): `docs/v1/ESPECIFICACAO_TECNICA_AGNOSTICA.md`

