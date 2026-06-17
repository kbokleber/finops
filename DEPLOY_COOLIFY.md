# Deploy no Coolify - Stack única (app) + recursos one-click

## Arquitetura

```
┌──────────────────────────────────────────────────────────┐
│  VPS Hetzner                                              │
│                                                           │
│  Recursos one-click (separados, cada um em sua network): │
│  ┌────────────────────┐ network: ywq8py7anh5lmq2gfzb1xpva│
│  │ postgresql-xxx     │ (10.0.2.2)                       │
│  │ svc_finops / nShn  │                                   │
│  └────────────────────┘                                   │
│  ┌────────────────────┐ network: coolify                  │
│  │ coolify-redis      │ (10.0.1.2)                       │
│  │ default / r32r...  │                                   │
│  └────────────────────┘                                   │
│  ┌────────────────────┐ network: s10h0gqm0uqy9jvywig5qrp2│
│  │ rabbitmq-xxx       │ (10.0.3.2)                       │
│  │ guest / guest      │                                   │
│  └────────────────────┘                                   │
│                                                           │
│  Stack do app (este docker-compose.app.yml):              │
│  ┌──────────────┐                                         │
│  │ dashboard    │  ── conectam-se às 3 networks acima ──> │
│  │ workers x4   │                                         │
│  └──────────────┘                                         │
└──────────────────────────────────────────────────────────┘
```

Os serviços do app se conectam às 3 networks dos recursos one-click do Coolify
e usam `extra_hosts` para mapear `postgres`/`redis`/`rabbitmq` para os nomes
reais dos containers.

## Setup inicial (1x)

1. **Recursos one-click já criados** (postgres, redis, rabbitmq) no Coolify.
   Anote:
   - Postgres: container `postgresql-ywq8py7anh5lmq2gfzb1xpva`, network `ywq8py7anh5lmq2gfzb1xpva`
   - Redis: container `coolify-redis`, network `coolify`
   - RabbitMQ: container `rabbitmq-s10h0gqm0uqy9jvywig5qrp2`, network `s10h0gqm0uqy9jvywig5qrp2`

2. **Criar a stack do app** no Coolify:
   - Source: GitHub → `kbokleber/finops` (branch `main`)
   - Docker Compose Location: `/docker-compose.app.yml`

3. **Environment Variables** (na UI do Coolify → aba Environment Variables):

   | Key | Value |
   |-----|-------|
   | `POSTGRES_USER` | `svc_finops` |
   | `POSTGRES_PASSWORD` | `nShn9RP#-RfrpcEUraInyy` |
   | `POSTGRES_DB` | `finopsdatabase` |
   | `RABBITMQ_USER` | `guest` |
   | `RABBITMQ_PASS` | `guest` |
   | `REDIS_PASSWORD` | `r32rYsBpYqovJxFwNn4NxqhhHYlFelIFtNirKHlcmapCf7Jdc4CdTuwmCMOFF2gm` |
   | `SECRET_KEY` | `<alguma-chave-segura>` |
   | `ENABLE_AZURE_AUTH` | `false` |
   | `FLASK_ENV` | `production` |

4. **Deploy** → Coolify faz `git pull` + `docker compose build` + `up`. Demora **~3-5min** no primeiro deploy, **~1-2min** nos seguintes (cache de camadas).

## Dia a dia

```bash
git push
```

Coolify detecta → rebuilda app → redeploy. A infra (postgres, redis, rabbitmq) não é tocada.

## Troubleshooting

### "network ywq8py7anh5lmq2gfzb1xpva not found"

A stack do app foi deployada antes dos recursos one-click. Deploy a stack do app
**depois** dos recursos one-click existirem.

### "connection refused" para postgres/redis/rabbitmq

Verifique se o recurso one-click está rodando e saudável:
```bash
docker ps | grep -E "postgres|redis|rabbitmq"
```

Se o nome do container mudou (Coolify gera nomes aleatórios), atualize os
`extra_hosts` no `docker-compose.app.yml` com o novo nome e faça push.

### Descobrir o nome real do container

Na VPS:
```bash
docker ps --format "{{.Names}}" | grep -E "postgres|redis|rabbitmq"
```
