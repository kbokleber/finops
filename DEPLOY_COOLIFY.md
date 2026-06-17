# Deploy FinOps no Coolify Cloud

Guia passo-a-passo para subir a stack FinOps (dashboard Flask + 4 workers Celery + Postgres 17 + Redis + RabbitMQ) no Coolify Cloud usando GitHub como origem do codigo.

## Pre-requisitos

- Repositorio no GitHub com este codigo
- Conta no Coolify Cloud (https://app.coolify.io)
- Dominio configurado para apontar para o Coolify (opcional, ver passo 6)

## 1. Subir o codigo para o GitHub

```bash
cd finops-main
git init
git add .
git commit -m "feat: stack completa para Coolify Cloud"
git branch -M main
git remote add origin git@github.com:<sua-org>/finops.git
git push -u origin main
```

> **Atencao**: nao commitar `.env` real. O arquivo `.env.production.example` vai pro repo como template.

## 2. Criar projeto no Coolify

1. Acesse https://app.coolify.io
2. Va em **Projects** > **+ Add Project** > nome sugerido: `finops`
3. Dentro do projeto, clique **+ Add Resource**
4. Escolha **Docker Compose**
5. Selecione **GitHub** como source e autorize o acesso ao repositorio
6. Escolha o repo `finops` e branch `main`

## 3. Configurar Build

Na tela de configuracao do Docker Compose:

- **Build Pack**: `Dockerfile` (NAO marque Nixpacks - ele ignora o compose)
- **Docker Compose Location**: `docker-compose.prod.yml`
- **Base Directory**: deixe vazio (a raiz do repo)
- **Port Mapping**: apenas `5000` (Coolify escuta e gera HTTPS)

> O Coolify constroi cada `image:` declarada com `build:`. Postgres usa `docker/postgres/Dockerfile`. Dashboard e workers usam `docker/app/Dockerfile` (mesma imagem, comando diferente).

## 4. Configurar Environment Variables (Secrets)

Va em **Configuration > Environment Variables** e adicione:

| Variavel | Exemplo | Obrigatorio |
|---|---|---|
| `POSTGRES_DB` | `finopsdatabase` | sim |
| `POSTGRES_USER` | `svc_finops` | sim |
| `POSTGRES_PASSWORD` | gerar com `openssl rand -hex 24` | sim |
| `RABBITMQ_USER` | `guest` | sim |
| `RABBITMQ_PASS` | gerar com `openssl rand -hex 16` | sim |
| `SECRET_KEY` | gerar com `openssl rand -hex 32` | sim |
| `FLASK_ENV` | `production` | recomendado |
| `ENABLE_AZURE_AUTH` | `false` | recomendado (desabilita login Microsoft) |

> Os valores sao passados via `${VAR}` no `docker-compose.prod.yml`. O servico `env-init` junta tudo em um arquivo `.env` que os demais servicos consomem.

## 5. Deploy

1. Clique **Deploy**
2. Acompanhe em **Deployments > Logs**. O build demora ~5 min na primeira vez (imagem do app com 90+ deps Python).
3. Quando todos os servicos estiverem `healthy`, o dashboard estara disponivel.

## 6. Configurar Dominio

Na aba **Configuration > Domains** do recurso:

- **Opcao A - Subdominio do Coolify**: clique **+ Generate Domain`. Sera algo como `https://finops-<hash>.coolify.app`. Gratis, com HTTPS automatico.
- **Opcao B - Dominio proprio**: adicione `finops.empresa.com.br`. O Coolify mostra um CNAME target. Configure o DNS no seu provedor e aguarde a propagacao.

## 7. Validar

```bash
curl https://<seu-dominio>/api/summary
# Esperado: {"custo_hoje": 0.0, "jobs_restantes": 0, "provedores": 0, "registros_hoje": 0}

curl https://<seu-dominio>/api/celery-status
# Esperado: {"workers_online": 3, "status": "3 Workers Online - Aguardando tarefas", ...}
```

## 8. Restaurar dump de producao

> Fazer **uma unica vez** apos o primeiro deploy bem-sucedido.

### Opcao A: Upload direto pelo painel

1. Va em **Resources > postgres > Exec**
2. Faca upload do arquivo `.dump` no terminal do Coolify (drag-and-drop ou wget de uma URL publica)
3. Rode o comando de restore manualmente:

```bash
export POSTGRES_PASSWORD=<valor-da-env-var-no-Coolify>
/scripts/restore_prod_dump.sh /tmp/finops.dump
```

### Opcao B: Via Exec local

Se voce tem acesso a URL publica do Postgres:

```bash
POSTGRES_HOST=<host-publico> \
POSTGRES_PASSWORD=<pwd> \
./scripts/restore_prod_dump.sh /caminho/do/finops.dump
```

### Validar restore

```bash
curl https://<seu-dominio>/api/summary
# Esperado agora: {"custo_hoje": 2585.55, "provedores": 1, "registros_hoje": 5936, ...}
```

## 9. Atualizar a aplicacao depois

1. Faca push no GitHub
2. No Coolify, va no recurso e clique **Redeploy**
3. O Coolify rebuilda as imagens e reinicia os servicos (mantem volumes = dados preservados)

## Troubleshooting

### Workers nao conectam no RabbitMQ

Verifique nos logs do worker (`Resources > worker_verifica > Logs`):

```
kombu.exceptions.OperationalError: [Errno -2] Name or service not known
```

O servico RabbitMQ precisa estar com o nome exato `rabbitmq` no compose (o `celery.py` tem o hostname hardcoded).

### Dashboard retorna 500 em /api/summary

Provavelmente `CONEXAO_DB_URL` errado. No `Resources > env-init > Logs` deve aparecer o `.env` gerado. Confirme que o servico postgres se chama `postgres`.

### Erro `extension "pg_repack" is not available`

O `init-extensions.sh` nao rodou. Isso acontece quando o volume `postgres_data` ja existia antes da instalacao das extensoes. Solucao:

1. Va em **Resources > postgres > Configuration**
2. Delete o volume `postgres_data` (CUIDADO: apaga todos os dados)
3. Redeploy
4. O `initdb` roda do zero, instala as extensoes e restaura o dump novamente

### Porta 5000 nao responde externamente

Confirme em **Configuration > Ports** que apenas `5000:5000` esta mapeada. O Coolify redireciona HTTP/HTTPS para essa porta.

## Estrutura de arquivos adicionados por este deploy

```
docker/
  postgres/
    Dockerfile          # Postgres 17 + pg_repack + pg_partman
    init-extensions.sh  # Cria extensoes no startup
  app/
    Dockerfile          # Imagem Python 3.11 compartilhada
dashboard/
  wsgi.py               # Entrypoint gunicorn
docker-compose.prod.yml # Stack completa
.env.production.example # Template de env vars
scripts/
  restore_prod_dump.sh  # Restore do dump de producao
DEPLOY_COOLIFY.md       # Este arquivo
```
