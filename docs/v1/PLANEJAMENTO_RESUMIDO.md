# Planejamento V1 - Django Vert Helper

## 📋 Resumo Executivo

**Objetivo:** Criar uma biblioteca Django que monitora a saúde de serviços (PostgreSQL, S3, Kafka) e oferece um sistema de ações com formulários condicionais, tudo acessível via APIs RESTful.

**Status:** ✅ Planejamento Concluído

---

## 🎯 Decisões Arquiteturais Finais

### 1. Armazenamento
- ✅ **Banco de dados** (mudança de requisito inicial)
- Health checks: armazenados em tabela `ServiceHealth`
- Actions: armazenadas em tabela `Action`
- Formulários: tabela `Question` com relação inversa (parent_question + parent_value)
- Soft delete: campo `is_active` em `Service` para manter histórico

### 2. APIs (3 endpoints)
- ✅ `/api/helper/v1/healthcare/` - Saúde dos serviços
- ✅ `/api/helper/v1/actions/` - Listar e executar ações
- ✅ `/api/helper/v1/app-health/` - Saúde da aplicação (sem Django)

### 3. Serviços Nativos
- ✅ PostgreSQL, S3, Kafka
- ✅ Suporta N serviços custom
- Configuráveis via `settings.py`
- Permite custom health checks

### 4. Sistema de Actions
- ✅ Decorator `@helper_action`
- ✅ Formulários condicionais
- ✅ Command único de setup (`vert_helper_setup`)
- ✅ UUID como PK, SLUG como identificador

### 5. Autenticação
- ✅ `/api/helper/v1/app-health/` - Sem autenticação
- ✅ Demais endpoints - Configurável via settings (padrão: AllowAny)

### 6. Agendamento de Health Checks
- ✅ Suporta Django Q ou Django RQ
- ✅ Auto-registra ao deploy se configurado
- ✅ API para check manual em tempo real

### 7. Docker
- ✅ Cronjob + Script Bash (Opção A)
- ✅ Atualiza arquivo JSON estático a cada 10 minutos
- ✅ Mínimas dependências extras

### 8. Setup & Sincronização
- ✅ **Command único:** `vert_helper_setup` (serviços + ações + task)
- ✅ **Command alternativo:** `vert_helper_sync_actions` (apenas ações)
- ✅ **Soft delete:** Serviços removidos do settings marcados como `is_active=False`
- ✅ **Histórico:** Mantém logs em `ServiceHealth` mesmo após soft delete

---

## 📊 Arquitetura de Banco de Dados

### Tabelas Principais

```
Service
├── id (UUID, PK)
├── name (CharField, unique) - "S3", "POSTGRESQL", "KAFKA"
├── is_active (BooleanField, default=True) - Soft delete
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

ServiceHealth
├── id (UUID, PK)
├── service_id (FK)
├── status (CharField) - "OK", "FAILED", "UNKNOWN"
├── message (TextField, nullable)
├── checked_at (DateTimeField)
└── created_at (DateTimeField)

Action
├── id (UUID, PK)
├── slug (CharField, unique)
├── name (CharField)
├── description (TextField)
├── services (ArrayField de UUID FK)
├── function_path (CharField)
├── status (CharField) - "active", "inactive"
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

Question
├── id (UUID, PK)
├── action_id (FK)
├── label (CharField)
├── type (CharField) - "radio", "text", "textarea", "file", "select"
├── options (JSONField, nullable)
├── is_required (BooleanField)
├── parent_question (FK, nullable) - Relação inversa
├── parent_value (CharField, nullable) - Valor que ativa
├── action_kwarg (CharField, nullable) - Nome do parâmetro
├── is_first (BooleanField)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

ActionExecution
├── id (UUID, PK)
├── action_id (FK)
├── responses (JSONField)
├── result (JSONField)
├── executed_by (FK User, nullable)
└── executed_at (DateTimeField)
```

**Django Admin:** ✅ Todas as tabelas disponíveis

---

## ⚙️ Configuração via Settings

```python
VERT_HELPER = {
    "PERMISSION_CLASS": "rest_framework.permissions.AllowAny",
    "SCHEDULER": "django_q",  # ou "rq" ou None
    "HEALTH_CHECK_INTERVAL": 600,  # segundos
    "HEALTH_CHECK_AUTO_REGISTER": True,
    "SERVICES": {
        "postgres": {...},
        "s3": {...},
        "kafka": {...}
    }
}
```

---

## 🔌 APIs

### Healthcare
**GET** `/api/helper/v1/healthcare/`
- Retorna status de todos os serviços
- Último check mais recente
- Query param: `?force_refresh=true`

### Actions - Listar
**GET** `/api/helper/v1/actions/`
- Paginação, filtros, search
- `is_recommended: true` se serviço falhou
- Ordenação automática: recomendadas primeiro

### Actions - Detalhes + Formulário
**GET** `/api/helper/v1/actions/<slug>/`
- Todas as perguntas da ação
- Estrutura condicional (parent_question, parent_value)

### Actions - Executar
**POST** `/api/helper/v1/actions/<slug>/execute/`
- Request: `{"questions": {"q1": "resposta", ...}}`
- Response: `{"status": "success|error|info", "message": "...", ...}`

### App-Health
**GET** `/api/helper/v1/app-health/`
- Sem autenticação
- JSON estático do Docker

---

## 🎯 Decorator e Sincronização

```python
@helper_action(
    slug="execute-action",
    name="Executar Ação",
    services=["S3", "KAFKA"]
)
def execute_action(responses):
    return {
        "status": "success|error|info",
        "message": "...",
        "data": {...},
        "steps": [...]  # opcional
    }
```

**Management Commands:**

**1. Setup Inicial (executar no deploy):**
```bash
python manage.py vert_helper_setup
```

**Sincroniza:**
1. ✅ Sincroniza Services (nativos + custom) do settings
   - Cria novos serviços
   - Ativa serviços já existentes
   - Soft delete (is_active=False) serviços removidos do settings
2. ✅ Sincroniza Actions (discover @helper_action)
   - Cria novos @helper_action
   - Atualiza existentes
   - Deleta orfãs (removidos do código)
3. ✅ Registra task agendada (se SCHEDULER configurado)

**2. Apenas Sincronizar Actions:**
```bash
python manage.py vert_helper_sync_actions
```

---

## 🐳 Docker - App Health

**Implementação:** Cronjob + Script Bash
- `/app/health_check.sh`
- Executado a cada 10 minutos
- Atualiza `/app/health.json`
- Nginx serve arquivo estático

**Dockerfile:**
```dockerfile
RUN chmod +x /app/health_check.sh
RUN apt-get install -y cron
RUN echo "*/10 * * * * /app/health_check.sh" | crontab -
CMD service cron start && gunicorn ...
```

---

## 📋 Formulários Condicionais - Exemplo Prático

**Estrutura:** Relação inversa (parent_question + parent_value)

```
Q1 (first=true)
├─ label: "O arquivo é CSV ou JSON?"
├─ type: "radio"
├─ options: ["CSV", "JSON"]
└─ action_kwarg: "file_type"

├─ Q2 (parent="Q1", parent_value="CSV")
│  ├─ label: "Arquivo ou URL?"
│  ├─ options: ["Arquivo", "URL"]
│  └─ action_kwarg: "csv_source"
│
└─ Q3 (parent="Q1", parent_value="JSON")
   ├─ label: "ID do workflow?"
   ├─ type: "text"
   └─ action_kwarg: "workflow_id"
   
   └─ Q4 (parent="Q3", parent_value=null)
      ├─ label: "Mensagem JSON?"
      ├─ type: "textarea"
      └─ action_kwarg: "json_text"
```

**API POST:**
```json
{
    "questions": {
        "Q1": "CSV",
        "Q2": "Arquivo",
        "Q3": null,
        "Q4": null
    }
}
```

---

## ✅ Checklist de Implementação

- [ ] Criar models (Service, ServiceHealth, Action, Question, ActionExecution)
- [ ] Criar serializers para todos os models
- [ ] Criar views/viewsets das APIs
- [ ] Implementar health checks (postgres, s3, kafka)
- [ ] Criar task agendada (Django Q ou RQ)
- [ ] Implementar decorator `@helper_action`
- [ ] Criar management command `vert_helper_setup` (único)
- [ ] Criar management command `vert_helper_sync_actions` (apenas actions)
- [ ] Implementar soft delete para Service (is_active)
- [ ] Django Admin configuration (filtrar is_active=True por default)
- [ ] Docker integration (cronjob + health.json)
- [ ] Testes unitários
- [ ] Testes de integração
- [ ] Documentação final

---

## 📚 Documentação

- ✅ **ESPECIFICACAO_TECNICA.md** - Referência técnica completa
- ✅ **MANUAL_DE_USO.MD** - Guia prático de uso
- 📝 **objetivo.txt** - Objetivo inicial (mantém para referência)

---

## 🚀 Próximos Passos

1. **Criar Models** (Service, ServiceHealth, Action, Question, ActionExecution)
2. **Criar Migrations**
3. **Implementar Serializers** (DRF)
4. **Criar Views/APIs**
5. **Implementar Health Checks Functions** (postgres, s3, kafka)
6. **Criar Decorator** `@helper_action`
7. **Criar Management Commands:**
   - `vert_helper_setup` (serviços + ações + task)
   - `vert_helper_sync_actions` (apenas ações)
8. **Implementar Task Agendada** (Django Q ou RQ)
9. **Django Admin Configuration** (filtrar is_active=True)
10. **Docker Integration** (cronjob + health.json)
11. **Testes Unitários e de Integração**
12. **Documentação Final**

---

## 📝 Notas Importantes

- **Setup Command:** `vert_helper_setup` deve ser executado no pipeline de deploy
- **Soft Delete:** Serviços removidos do settings → is_active=False (mantém histórico)
- **Health Checks:** Se `SCHEDULER` vazio, não agenda automaticamente
- **App-Health:** Arquivo JSON estático, sem dependência Django
- **Security:** `/api/helper/v1/app-health/` sem autenticação (acessível)
- **Escalabilidade:** ArrayField para services (PostgreSQL), normalizável em V2
- **Custom Services:** Suporta n serviços custom além dos 3 nativos (PostgreSQL, S3, Kafka)

---

**Data de Criação:** 2026-07-15  
**Status:** Pronto para Implementação ✅
