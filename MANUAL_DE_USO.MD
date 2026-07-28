# Django Vert Helper - Manual de Uso V1

## 📖 Introdução

O `django-vert-helper` é uma biblioteca Django que monitora a saúde de seus serviços (PostgreSQL, S3, Kafka) e oferece um sistema de ações com formulários condicionais.

## 🚀 Instalação

### 1. Adicione a app ao Django

Em `settings.py`:

```python
INSTALLED_APPS = [
    # ... suas outras apps ...
    "vert_helper.apps.VertHelperConfig",
]
```

### 2. Configure a biblioteca

Em `settings.py`, adicione a configuração:

```python
VERT_HELPER = {
    # Autenticação (opcional, padrão: AllowAny)
    "PERMISSION_CLASS": "rest_framework.permissions.IsAuthenticated",
    
    # Agendamento (opcional)
    "SCHEDULER": "django_q",  # ou "rq", ou deixe vazio para desabilitar
    "HEALTH_CHECK_INTERVAL": 600,  # 10 minutos em segundos
    "HEALTH_CHECK_AUTO_REGISTER": True,
    
    # Serviços a monitorar
    "SERVICES": {
        "postgres": {
            "label": "PostgreSQL Principal",
            "enabled": True,
            "function": "vert_helper.health_checks.postgres.check_postgres",
            "context": {
                "host": "localhost",
                "port": 5432,
                "database": "my_database",
                "user": "postgres",
                "password": "your_password"
            }
        },
        "s3": {
            "label": "AWS S3",
            "enabled": True,
            "function": "vert_helper.health_checks.s3.check_s3",
            "context": {
                "aws_access_key_id": "your_key",
                "aws_secret_access_key": "your_secret",
                "bucket_name": "your_bucket",
                "region_name": "us-east-1"
            }
        },
        "kafka": {
            "label": "Apache Kafka",
            "enabled": True,
            "function": "vert_helper.health_checks.kafka.check_kafka",
            "context": {
                "bootstrap_servers": ["kafka:9092"],
                "timeout": 5
            }
        }
    }
}
```

### 3. Migre o banco de dados

```bash
python manage.py migrate vert_helper
```

### 4. Executar Setup da Biblioteca

Execute o comando de setup para sincronizar serviços, ações e registrar task agendada:

```bash
python manage.py vert_helper_setup
```

Esse comando:
- ✅ Sincroniza todos os **serviços** configurados no settings (nativos + custom)
- ✅ Descobre e registra todas as **ações** decoradas com `@helper_action`
- ✅ Registra a **task de health check** (se scheduler configurado)
- ✅ Soft delete de serviços removidos (mantém histórico)

## 💻 Uso

### Criar uma Ação

Use o decorator `@helper_action` para registrar uma ação:

```python
# app/actions.py
from vert_helper import helper_action

@helper_action(
    slug="generate-report",
    name="Gerar Relatório",
    description="Gera um relatório em PDF ou CSV",
    services=["S3", "POSTGRESQL"],  # Serviços relacionados
    questions=[
        {
            "label": "Qual é o formato do relatório?",
            "type": "radio",
            "options": ["PDF", "CSV"],
            "is_required": True,
            "action_kwarg": "format_type",
            "children": [
                {
                    "label": "Qual período?",
                    "type": "select",
                    "options": ["monthly", "yearly"],
                    "is_required": True,
                    "action_kwarg": "report_type",
                    "parent_value": "PDF"
                },
                {
                    "label": "Incluir gráficos?",
                    "type": "radio",
                    "options": ["Sim", "Não"],
                    "is_required": True,
                    "action_kwarg": "include_charts",
                    "parent_value": "CSV"
                }
            ]
        }
    ]
)
def generate_report(responses):
    """
    Args:
        responses: Dict com respostas do formulário
        Exemplo: {"q1": "PDF", "q2": "monthly", "q3": "2024-06"}
    
    Returns:
        Dict com status e mensagem
        {
            "status": "success|error|info",
            "message": "...",
            "data": {...},  # opcional
            "steps": [...]  # opcional (apenas para info)
        }
    """
    format_type = responses.get("q1")  # PDF ou CSV
    report_type = responses.get("q2")  # monthly ou yearly
    period = responses.get("q3")       # 2024-06
    
    try:
        # Sua lógica aqui
        report_id = f"report_{period}_{report_type}"
        
        return {
            "status": "success",
            "message": f"Relatório {report_type} gerado com sucesso",
            "data": {
                "report_id": report_id,
                "download_url": f"s3://bucket/{report_id}.{format_type.lower()}"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Erro ao gerar relatório",
            "details": str(e)
        }
```

### Configurar Questions no decorator (recomendado)

Defina o formulário da action no campo `questions` do decorator e sincronize com o comando de setup/sync.

Campos aceitos por pergunta:

- `label` (obrigatório)
- `type` (obrigatório): `radio`, `text`, `textarea`, `file`, `select`
- `options` (opcional)
- `is_required` (opcional)
- `action_kwarg` (opcional)
- `children` (opcional)

Campos extras em cada item de `children`:

- `parent_value`: valor da resposta da pergunta pai que habilita a filha

**Exemplo prático:**

```
Pergunta 1 (is_first=True):
├─ Label: "Qual é o formato do relatório?"
├─ Type: "radio"
├─ Options: ["PDF", "CSV"]
├─ is_required: True
├─ action_kwarg: "format_type"
└─ Action: "generate-report"

    ↓ Se resposta = "PDF"
    Pergunta 2:
    ├─ Label: "Qual período?"
    ├─ Type: "select"
    ├─ Options: ["monthly", "yearly"]
    ├─ parent_question: "q1"
    ├─ parent_value: "PDF"
    ├─ action_kwarg: "report_type"
    └─ is_required: True
    
    ↓ Se resposta = "CSV"
    Pergunta 3:
    ├─ Label: "Incluir gráficos?"
    ├─ Type: "radio"
    ├─ Options: ["Sim", "Não"]
    ├─ parent_question: "q1"
    ├─ parent_value: "CSV"
    ├─ action_kwarg: "include_charts"
    └─ is_required: True
```

**Sincronização:**
- Execute `python manage.py vert_helper_setup` para sincronizar serviços, ações e questions
- Ou execute `python manage.py vert_helper_sync_actions` para sincronizar apenas ações e questions
- Na sincronização, as questions persistidas da action são substituídas pela árvore definida no decorator

### Configurar Formulário via Admin (opcional)

Se você preferir ajuste manual:

1. Acesse `http://localhost:8000/admin/`
2. Vá para `Vert Helper > Questions`
3. Crie a primeira pergunta com `is_first = True`
4. Crie perguntas filhas com `parent_question` e `parent_value`

Observação: ao executar sync de actions, as questions da action podem ser sobrescritas pela definição de `questions` no código.

### Sincronizar Actions

Sempre que adicionar um novo `@helper_action`, você pode:

**Opção A - Setup Completo (Recomendado):**
```bash
python manage.py vert_helper_setup
```
Sincroniza tudo: serviços, ações e task agendada.

**Opção B - Apenas Ações:**
```bash
python manage.py vert_helper_sync_actions
```
Sincroniza apenas as ações (útil se só alterou ações).

## 🔗 APIs

### 1. Verificar Saúde dos Serviços

**GET** `/api/helper/v1/healthcare/`

```bash
curl http://localhost:8000/api/helper/v1/healthcare/
```

**Resposta:**
```json
{
    "POSTGRESQL": {
        "status": "OK",
        "last_updated": "2024-06-10T12:34:56Z"
    },
    "S3": {
        "status": "FAILED",
        "message": "Connection timeout",
        "last_updated": "2024-06-10T12:35:00Z"
    },
    "KAFKA": {
        "status": "UNKNOWN",
        "message": "Service not configured",
        "last_updated": null
    }
}
```

**Force refresh imediato:**
```bash
curl http://localhost:8000/api/helper/v1/healthcare/?force_refresh=true
```

### 2. Listar Ações

**GET** `/api/helper/v1/actions/`

```bash
# Listar todas
curl http://localhost:8000/api/helper/v1/actions/

# Filtrar por serviço
curl "http://localhost:8000/api/helper/v1/actions/?service=S3"

# Buscar por nome
curl "http://localhost:8000/api/helper/v1/actions/?search=report"

# Paginação
curl "http://localhost:8000/api/helper/v1/actions/?page=2&page_size=5"
```

**Resposta:**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid-123",
            "slug": "generate-report",
            "name": "Gerar Relatório",
            "description": "Gera relatórios em PDF ou CSV",
            "services": ["S3", "POSTGRESQL"],
            "status": "active",
            "is_recommended": false,
            "created_at": "2024-06-01T10:00:00Z"
        }
    ]
}
```

### 3. Detalhes da Ação + Formulário

**GET** `/api/helper/v1/actions/<slug>/`

```bash
curl http://localhost:8000/api/helper/v1/actions/generate-report/
```

**Resposta:** (inclui todas as perguntas)
```json
{
    "id": "uuid-123",
    "slug": "generate-report",
    "name": "Gerar Relatório",
    "description": "Gera relatórios em PDF ou CSV",
    "services": ["S3", "POSTGRESQL"],
    "status": "active",
    "questions": [
        {
            "id": "q1",
            "label": "Qual é o formato?",
            "type": "radio",
            "options": ["PDF", "CSV"],
            "is_required": true,
            "parent_question": null,
            "parent_value": null,
            "action_kwarg": "format_type"
        },
        {
            "id": "q2",
            "label": "Qual período?",
            "type": "select",
            "options": ["monthly", "yearly"],
            "is_required": true,
            "parent_question": "q1",
            "parent_value": "PDF",
            "action_kwarg": "report_type"
        }
    ],
    "created_at": "2024-06-01T10:00:00Z"
}
```

### 4. Executar Ação

**POST** `/api/helper/v1/actions/<slug>/execute/`

```bash
curl -X POST http://localhost:8000/api/helper/v1/actions/generate-report/execute/ \
  -H "Content-Type: application/json" \
  -d '{
    "questions": {
      "q1": "PDF",
      "q2": "monthly"
    }
  }'
```

**Resposta (sucesso):**
```json
{
    "status": "success",
    "message": "Relatório gerado com sucesso",
    "data": {
        "report_id": "report_2024-06_monthly",
        "download_url": "s3://bucket/report_2024-06_monthly.pdf"
    }
}
```

**Resposta (erro):**
```json
{
    "status": "error",
    "message": "Falha ao gerar relatório",
    "details": "S3 bucket not accessible"
}
```

**Resposta (info):**
```json
{
    "status": "info",
    "message": "Relatório não pode ser gerado no momento",
    "steps": [
        "Verifique se o bucket S3 está acessível",
        "Confirme se o banco de dados está online",
        "Tente novamente em alguns minutos"
    ]
}
```

### 5. Saúde da Aplicação (sem Django)

**GET** `/api/helper/v1/app-health/`

```bash
curl http://localhost:8000/api/helper/v1/app-health/
```

**Resposta:**
```json
{
    "status": "stable",
}
```

## 🔧 Configurações Avançadas

### Usar Custom Health Check

Em `settings.py`:

```python
VERT_HELPER = {
    "SERVICES": {
        "my_api": {
            "label": "Minha API Custom",
            "enabled": True,
            "function": "myapp.health_checks.check_my_api",
            "context": {
                "url": "https://api.example.com",
                "timeout": 5
            }
        }
    }
}
```

Em `myapp/health_checks.py`:

```python
def check_my_api(context):
    """
    Args:
        context: Dict com configuração do serviço
    
    Returns:
        Tuple[str, str | None] - (status, message)
        Status: "OK", "FAILED", "UNKNOWN"
    """
    import requests
    
    try:
        response = requests.get(
            context["url"],
            timeout=context["timeout"]
        )
        
        if response.status_code == 200:
            return "OK", None
        else:
            return "FAILED", f"HTTP {response.status_code}"
    except Exception as e:
        return "FAILED", str(e)
```

### Agendamento com Django Q

Em `settings.py`:

```python
Q_CLUSTER = {
    'name': 'vert_helper',
    'workers': 4,
    'timeout': 300,
    'retry': 360,
    'orm': 'default'
}

VERT_HELPER = {
    "SCHEDULER": "django_q",
    "HEALTH_CHECK_INTERVAL": 300,  # 5 minutos
}
```

Inicie o cluster:

```bash
python manage.py qcluster
```

### Agendamento com Django RQ

Em `settings.py`:

```python
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    }
}

VERT_HELPER = {
    "SCHEDULER": "rq",
    "HEALTH_CHECK_INTERVAL": 300,
}
```

Inicie o worker:

```bash
python manage.py rqworker
```

## 🐳 Docker

Consulte o `Dockerfile-example` para integração com Docker e cronjob de health check.

### Expor app-health via Nginx

Para garantir que `GET /api/helper/v1/app-health/` funcione mesmo se o Django estiver indisponível, o JSON deve ser servido diretamente pelo Nginx.

1. Gere/atualize o arquivo `/app/health.json` no container (via script periódico).
2. Configure o Nginx para responder esse arquivo sem proxy para Django.

Exemplo de bloco no Nginx:

```nginx
location /api/helper/v1/app-health/ {
    alias /app/health.json;
    default_type application/json;
    add_header Cache-Control "no-store";
}
```

### Integração no Dockerfile (app + Nginx)

Exemplo mínimo de integração no Dockerfile:

```dockerfile
FROM python:3.12-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app
COPY ./health_check.sh /app/health_check.sh
RUN chmod +x /app/health_check.sh

# Configuração do Nginx com endpoint estático de app-health
COPY ./docker/nginx/default.conf /etc/nginx/conf.d/default.conf

# Atualiza /app/health.json no boot e a cada 10 min (sem cron de sistema)
CMD ["bash", "-lc", "(sleep 60; bash /app/health_check.sh || true; while true; do sleep 600; bash /app/health_check.sh || true; done) & nginx && exec gunicorn --bind 0.0.0.0:8000 main.wsgi"]
```

Arquivo de configuração do Nginx (`docker/nginx/default.conf`):

```nginx
server {
    listen 8080;
    server_name _;

    location /api/helper/v1/app-health/ {
        alias /app/health.json;
        default_type application/json;
        add_header Cache-Control "no-store";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Docker compose
```docker compose
services:
  app:
    build:
      context: ./src
      args:
        GIT_COMMIT: ${GIT_COMMIT:-unknown}
    env_file: ./src/.env
    environment:
      - PYTHONUNBUFFERED=1
```

Observações:
- O endpoint de app-health deve apontar para o Nginx (porta publicada do container).
- Se já existir reverse proxy externo (Ingress/Nginx/Traefik), mantenha a mesma lógica: rota de app-health servindo arquivo estático e demais rotas indo para a aplicação.

## 📊 Django Admin

Todas as tabelas são disponibilizadas no Django Admin:

- **Services** - Gerenciar serviços
- **ServiceHealth** - Histórico de checks (read-only)
- **Actions** - Gerenciar ações
- **Questions** - Gerenciar perguntas dos formulários
- **ActionExecutions** - Histórico de execuções (read-only)

Acesse: `http://localhost:8000/admin/`

## ❓ Troubleshooting

### Health check não está sendo executado

1. Execute `python manage.py vert_helper_setup`
2. Verifique se `SCHEDULER` está configurado em settings.py
3. Verifique se o cluster/worker está rodando

### Ação não aparece na lista

1. Execute `python manage.py vert_helper_setup`
2. Verifique se a ação tem status `active`

### Serviço foi removido mas ainda aparece

1. Execute `python manage.py vert_helper_setup`
2. Isso vai fazer soft delete (is_active=False) e remover das APIs

### Formulário não está exibindo perguntas

1. Verifique se a action tem `questions` declaradas no decorator
2. Execute `python manage.py vert_helper_setup` ou `python manage.py vert_helper_sync_actions`
3. Se usar fluxo manual no admin, verifique se há ao menos uma pergunta com `is_first = True`
4. Verifique se `parent_question` e `parent_value` estão corretos

## 📞 Suporte

Para issues ou dúvidas, consulte a documentação em `docs/v1/ESPECIFICACAO_TECNICA.md`
