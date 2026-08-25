# Manual 2.0 de Implementacao (baseado na PR 939)

## 1. Objetivo

Este manual descreve a implementacao operacional do `vert_helper` em container, baseada no fluxo da PR 939 do backend `vertc-gerador-documentos-backend`.

Foco deste documento:
- `Dockerfile`
- `entrypoint-otel.sh`
- `health_check.sh`
- configuracoes `nginx`

A configuracao de `settings.py` permanece alinhada com o manual atual (`MANUAL_DE_USO.MD`) e nao e repetida aqui.

---

## 2. Visao Geral da Arquitetura de Runtime

No modo producao descrito pela PR:

1. O processo principal continua sendo o `gunicorn` (app Django/ASGI).
2. O `entrypoint-otel.sh` inicia processos auxiliares em background:
   - `nginx`
   - loop de atualizacao de `health.json`
3. O `health_check.sh` consulta `GET /api/helper/v1/healthcare/` no backend local.
4. O script escreve `/app/health.json` com status:
   - `stable` quando o endpoint responde
   - `failed` quando o endpoint falha
5. O `nginx` publica `GET /api/helper/v1/app-health/` lendo diretamente `/app/health.json`.

Resultado:
- monitoria externa pode consultar `app-health` sem depender de autenticao da API de negocio.
- o status exposto e simples e desacoplado da aplicacao principal.

---

## 3. Implementacao do Dockerfile

## 3.1 Pacotes obrigatorios no container

Garanta que a imagem tenha:
- `nginx`
- `curl`
- `git` (usado no fluxo da PR; manter se seu build/runtime exigir)

Exemplo de bloco no build:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       nginx \
       curl \
       git
```

## 3.2 Copia dos arquivos operacionais

No stage final/runtime:

```dockerfile
COPY ./health_check.sh /app/health_check.sh
COPY ./docker_assets/nginx.prd.conf /etc/nginx/conf.d/default.conf
RUN chmod +x /app/health_check.sh
```

No repositorio `django-vert-helper`, a mesma ideia pode usar:
- `./health_check.sh`
- `./nginx/nginx.prd.conf`

## 3.3 Entrypoint e comando final

Padrao da PR:

```dockerfile
ENTRYPOINT ["sh", "./entrypoint-otel.sh", "gunicorn"]
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 conf.asgi:application -c gunicorn.config.py"]
```

Observacao:
- no fluxo da PR, o `entrypoint` intercepta `gunicorn` e prepara sidecars/rotinas antes do `exec` final.

---

## 4. Implementacao do entrypoint-otel.sh

## 4.1 Setup da aplicacao

Antes de subir o servidor, o setup roda:
- `migrate`
- `collectstatic`
- `createcachetable`
- `vert_helper_setup`
- `init_helper`

Esse trecho garante que:
- recursos do helper estejam sincronizados
- dados/minima inicializacao estejam aplicados no boot

## 4.2 Sidecars de runtime

A PR adiciona uma funcao equivalente a:

```bash
start_runtime_sidecars() {
  nginx -g 'daemon off;' &

  (
    sleep "${HEALTH_CHECK_INITIAL_DELAY:-60}"
    bash /app/health_check.sh || true
    while true; do
      sleep "${HEALTH_CHECK_INTERVAL:-600}"
      bash /app/health_check.sh || true
    done
  ) &
}
```

Comportamento:
- espera inicial de 60s (default) antes do primeiro check
- revalida a cada 600s (default)
- nunca derruba o container por falha no check (`|| true`)

## 4.3 Bind do Gunicorn

A PR fixa bind interno em `:8000`:

```bash
exec opentelemetry-instrument gunicorn conf.asgi:application -c gunicorn.config.py --bind :8000
```

Isso precisa estar alinhado com o `proxy_pass` do nginx de producao.

## 4.4 Exemplo minimo de entrypoint (foco na biblioteca)

O exemplo abaixo remove detalhes de observabilidade e deixa apenas o essencial para o `vert_helper`:

```bash
#!/bin/bash
set -e

start_runtime_sidecars() {
  nginx -g 'daemon off;' &

  (
    sleep "${HEALTH_CHECK_INITIAL_DELAY:-60}"
    bash /app/health_check.sh || true
    while true; do
      sleep "${HEALTH_CHECK_INTERVAL:-600}"
      bash /app/health_check.sh || true
    done
  ) &
}

setup_vert_helper() {
  python manage.py migrate --no-input
  python manage.py collectstatic --no-input
  python manage.py createcachetable

  # Passos essenciais da biblioteca
  python manage.py vert_helper_setup
  python manage.py init_helper
}

start_runtime_sidecars
setup_vert_helper

exec gunicorn conf.asgi:application -c gunicorn.config.py --bind :8000
```

Pontos obrigatorios deste fluxo:

- executar `vert_helper_setup` no boot
- executar `init_helper` no boot
- manter loop que atualiza `/app/health.json`
- manter nginx servindo `GET /api/helper/v1/app-health/`

---

## 5. Implementacao do health_check.sh

Script de referencia:

```bash
#!/bin/bash
set -e

HEALTH_STATUS="stable"

if ! curl -fsS http://localhost:8000/api/helper/v1/healthcare/ > /dev/null 2>&1; then
    HEALTH_STATUS="failed"
fi

cat > /app/health.json <<EOF
{
  "status": "$HEALTH_STATUS",
  "timestamp": "$(TZ=America/Sao_Paulo date +"%Y-%m-%dT%H:%M:%S%:z")"
}
EOF
```

Pontos importantes:
- endpoint consultado: `/api/helper/v1/healthcare/`
- saida padrao para monitoria: `/app/health.json`
- timezone explicita no timestamp

---

## 6. Implementacao do Nginx

## 6.1 Producao (`nginx.prd.conf`)

Padrao da PR:
- `listen 8080`
- `location /api/helper/v1/app-health/` le `health.json`
- `location /` faz proxy para `127.0.0.1:8000`

Trechos-chave:

```nginx
location = /api/helper/v1/app-health {
    return 301 /api/helper/v1/app-health/;
}

location = /api/helper/v1/app-health/ {
    root /app;
    try_files /health.json =503;
    default_type application/json;
    add_header Cache-Control "no-store";
}
```

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 6.2 Desenvolvimento (`nginx.dev.conf`)

Padrao da PR:
- `listen 8000`
- app-health igual
- proxy para backend em `127.0.0.1:8001`

Use esse arquivo apenas quando seu processo Django/Gunicorn estiver realmente em `8001` no ambiente de dev.

## 6.3 Como subir local com Dockerfile-dev + nginx

Este fluxo reflete o padrao da PR de referencia:

- `nginx` escuta em `8000`
- Django (`runserver`) sobe em `127.0.0.1:8001`
- `nginx.dev.conf` faz proxy `8000 -> 8001`
- `health_check.sh` consulta `/api/helper/v1/healthcare/` via `localhost:8000`

### Build da imagem de desenvolvimento

```bash
docker build -f Dockerfile-dev -t vert-helper:dev .
```

### Subir container local

```bash
docker run --rm -it \
  -p 8000:8000 \
  -e HEALTH_CHECK_INITIAL_DELAY=10 \
  -e HEALTH_CHECK_INTERVAL=60 \
  vert-helper:dev
```

No fluxo padrao, o container usa:

```bash
ENTRYPOINT ["sh", "./docker_assets/entrypoint-dev.sh"]
CMD ["bash", "-lc", "(sleep 60; bash /app/health_check.sh || true; while true; do sleep 600; bash /app/health_check.sh || true; done) & nginx -g 'daemon off;' & python manage.py runserver 127.0.0.1:8001"]
```

### Validar localmente

```bash
# health externo (via nginx)
curl -i http://127.0.0.1:8000/api/helper/v1/app-health/

# api do helper (via nginx -> django)
curl -i http://127.0.0.1:8000/api/helper/v1/healthcare/
```

Esperado:

- `app-health` responde JSON de `/app/health.json`
- `healthcare` responde a API Django atraves do proxy

### Ajuste de caminho no pacote `django-vert-helper`

Se seu projeto local usa a estrutura deste pacote (com `nginx/nginx.dev.conf`), ajuste apenas o caminho de copia da conf no Dockerfile para:

```dockerfile
COPY ./nginx/nginx.dev.conf /etc/nginx/conf.d/default.conf
```

---

## 7. Checklist de Implementacao

1. Incluir `nginx` e `curl` na imagem.
2. Copiar `health_check.sh` para `/app` e marcar executavel.
3. Copiar `nginx.prd.conf` para `/etc/nginx/conf.d/default.conf`.
4. Ajustar `entrypoint-otel.sh` para:
   - iniciar nginx em background
   - iniciar loop do health check
   - rodar `vert_helper_setup` e `init_helper` no setup
5. Garantir Gunicorn bindando em `:8000`.
6. Garantir `proxy_pass` do nginx apontando para a porta interna correta.
7. Validar endpoint publico `/api/helper/v1/app-health/`.

---

## 8. Validacao Pos-Deploy

## 8.1 Teste de health interno

```bash
curl -i http://127.0.0.1:8000/api/helper/v1/healthcare/
```

Esperado:
- HTTP 200 quando aplicacao estiver saudavel.

## 8.2 Teste de health externo (via nginx)

```bash
curl -i http://127.0.0.1:8080/api/helper/v1/app-health/
```

Esperado:
- HTTP 200 e JSON com `status: stable`.
- HTTP 503 quando `/app/health.json` ainda nao existir.

## 8.3 Validar arquivo gerado

```bash
cat /app/health.json
```

Esperado (exemplo):

```json
{
  "status": "stable",
  "timestamp": "2026-08-25T10:30:00-03:00"
}
```

---

## 9. Troubleshooting Rapido

## 9.1 `app-health` retorna 503 constante

Verificar:
1. se `health_check.sh` existe e esta executavel
2. se o loop no entrypoint iniciou
3. se `curl localhost:8000/api/helper/v1/healthcare/` responde no container

## 9.2 `app-health` retorna `failed`

Verificar:
1. erro nas migracoes/setup que impediu app de subir
2. bind do gunicorn diferente de `8000`
3. rota `/api/helper/v1/healthcare/` bloqueada por erro de app

## 9.3 Nginx no ar, backend indisponivel

Verificar:
1. `proxy_pass` aponta para porta certa
2. processo do gunicorn esta ativo
3. configuracao de listen e porta exposta no ambiente

---

## 10. Compatibilidade com o Manual Atual

A parte de configuracao de `settings.py` e endpoints de negocio do `vert_helper` continua coberta por `MANUAL_DE_USO.MD`.

Este manual 2.0 complementa o manual atual, detalhando o padrao de implantacao em container com health endpoint externo via nginx e arquivo `health.json`.
