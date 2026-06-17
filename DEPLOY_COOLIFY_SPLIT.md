# Deploy no Coolify - Arquitetura dividida (Infra + App)

## Por que dividir?

O build original (`docker-compose.prod.yml`) reconstruía **tudo** do zero a cada
`git push`:

- `pg_repack` compilado do source: **~10-15 min**
- `pip install` do requirements: **~1-2 min**
- `apt-get` do `pg_partman`: **~1 min**

Total: **~15-20 min por deploy**, mesmo que você só tenha mudado uma linha de HTML.

A solução é separar em **2 stacks** que compartilham uma network Docker:

| Stack | Compose | O que faz | Build por `git push`? |
|-------|---------|-----------|------------------------|
| **finops-infra** | `docker-compose.infra.yml` | Postgres + Redis + RabbitMQ | Não — usa imagens pré-construídas do registry |
| **finops-app** | `docker-compose.app.yml` | Dashboard + 4 workers Celery | Sim — build leve (~1-2 min) |

A imagem do app é reconstruída a cada push, mas o **build é leve** porque:
- Reusa o `python:3.11-slim-bookworm` (cache do Docker Hub)
- Reusa as dependências do `pip` (se `requirements.txt` não mudou, é cacheado)
- Só o `COPY . /finops/finops_celery/` precisa de novo

---

## Setup inicial (UMA VEZ)

### 1. Descobrir o endereço do seu Coolify Registry

No Coolify Cloud (ou self-hosted), o registry interno segue o padrão:

```
registry.<host-coolify>/<project-slug>
```

Exemplos:
- `registry.123.45.67.89.sslip.io/finops`
- `registry.coolify.example.com/finops`
- `ghcr.io/kbokleber` (se você prefere GitHub Container Registry)
- `docker.io/kbokleber` (se você prefere Docker Hub)

Anote esse endereço — vamos chamar de `COOLIFY_REGISTRY`.

### 2. Buildar e pushar as imagens de infra

Da sua máquina local (ou de qualquer host com Docker):

```bash
export COOLIFY_REGISTRY=registry.123.45.67.89.sslip.io/finops

# Builda as 3 imagens e pusha para o registry. Vai demorar ~15min.
./deploy/scripts/build-infra-images.sh
```

Se você só precisa de uma imagem específica:
```bash
./deploy/scripts/build-infra-images.sh postgres   # só rebuilda o postgres
```

> 💡 **Dica:** rode isso na sua máquina local, não no servidor. O push é
> por HTTP/HTTPS, funciona de qualquer lugar.

### 3. Criar a stack "finops-infra" no Coolify

1. Coolify → **New Resource** → **Docker Compose**
2. **Source:** GitHub → `kbokleber/finops`
3. **Branch:** `main`
4. **Compose Path:** `docker-compose.infra.yml`
5. **Environment Variables** (em "Environment Variables" da stack):
   - `COOLIFY_REGISTRY=registry.123.45.67.89.sslip.io/finops`
   - `POSTGRES_USER=svc_finops`
   - `POSTGRES_PASSWORD=<sua-senha-forte>`
   - `POSTGRES_DB=finopsdatabase`
   - `RABBITMQ_USER=guest`
   - `RABBITMQ_PASS=<sua-senha-forte>`
6. **Deploy** → Coolify faz `docker compose pull` (não rebuilda nada) e sobe.

⏱️ Deve estar no ar em **~30s** (já que não há build).

### 4. Criar a stack "finops-app" no Coolify

1. Coolify → **New Resource** → **Docker Compose**
2. **Source:** GitHub → `kbokleber/finops` (mesmo repo)
3. **Branch:** `main`
4. **Compose Path:** `docker-compose.app.yml`
5. **Environment Variables:**
   - `POSTGRES_USER=svc_finops`
   - `POSTGRES_PASSWORD=<mesma-senha-da-stack-infra>`
   - `POSTGRES_DB=finopsdatabase`
   - `SECRET_KEY=<alguma-chave-segura>`
   - `ENABLE_AZURE_AUTH=false`
   - `FLASK_ENV=production`
6. **Deploy** → Coolify faz `git pull` + `docker compose build` (só do app) + `up`.

⏱️ Primeiro deploy demora **~3-5min** (build do `pip install`).
Próximos deploys: **~1-2min** (cache de camadas).

---

## Dia a dia: deploy de uma mudança de código

```bash
# 1. Você edita código
vim dashboard/app.py
git add . && git commit -m "fix: ajusta XYZ" && git push
```

Coolify detecta o push na stack `finops-app`:
1. `git pull` (~5s)
2. `docker compose build` (~1-2min, cache de camadas)
3. `docker compose up -d` (~10s, sem downtime se você usar `restart: unless-stopped`)

**A stack `finops-infra` NÃO é tocada** — postgres, redis, rabbitmq continuam de pé.

---

## Quando rebuildar a infra?

Raramente. Apenas quando:

- Você atualizar a versão do Postgres (ex: `postgres:17` → `postgres:18`)
- Adicionar uma nova extensão ao `docker/postgres/Dockerfile`
- Adicionar uma config custom ao `redis` ou `rabbitmq`

Quando precisar:
```bash
# Rebuilda só o postgres
./deploy/scripts/build-infra-images.sh postgres

# Rebuilda tudo (15min)
./deploy/scripts/build-infra-images.sh
```

Depois, no Coolify, clique em **Redeploy** na stack `finops-infra`. O Coolify vai
fazer `docker compose pull` (puxa a imagem nova) e reiniciar os containers.

---

## Estrutura de arquivos

```
finops-main/
├── docker-compose.infra.yml    # Stack 1: postgres + redis + rabbitmq
├── docker-compose.app.yml      # Stack 2: dashboard + 4 workers
├── docker/
│   ├── postgres/Dockerfile     # Imagem custom do postgres
│   └── app/Dockerfile          # Imagem do app (Flask + Celery)
├── deploy/
│   └── scripts/
│       └── build-infra-images.sh  # Builda+pusha imagens de infra
├── finops_celery/              # Código Python (package)
├── dashboard/                  # Código Flask
├── tasks/                      # Tasks Celery
└── requirements.txt            # Dependências Python
```

---

## Troubleshooting

### "Network finops-infra is declared as external, but could not be found"

A stack `finops-app` foi deployada ANTES da `finops-infra`. Deploy a `finops-infra` primeiro.

### "pull access denied for finops/postgres:17"

O `COOLIFY_REGISTRY` não está configurado na UI do Coolify, ou você não rodou
`build-infra-images.sh` ainda. Veja passo 2.

### "connection refused to postgres:5432"

Os containers do app estão em outra network. Verifique se `finops-infra` aparece
como `external: true` no `docker-compose.app.yml` (já está) e se ambos os stacks
estão na mesma network.

Para debug:
```bash
# No Coolify, abra um terminal de qualquer servico do app e rode:
docker network ls
docker network inspect finops-infra
# Deve mostrar 3 servicos da infra + 5 do app = 8 containers.
```

### Quero voltar pro modelo antigo (1 stack única)

Simples: use `docker-compose.prod.yml` (mas ele foi removido neste commit).
A versão antiga está no histórico do git se você precisar reverter.

---

## Resumo de comandos

```bash
# Build inicial das imagens (1x, ~15min)
export COOLIFY_REGISTRY=<seu-registry>
./deploy/scripts/build-infra-images.sh

# Deploy do dia-a-dia
git push   # Coolify cuida do resto, ~1-2min

# Rebuild da infra (raro)
./deploy/scripts/build-infra-images.sh postgres
```
