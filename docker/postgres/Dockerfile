# Postgres 17 com extensoes usadas em producao.
# Necessario porque o dump de producao referencia os schemas `repack` (pg_repack)
# e `partman` (pg_partman). Sem essas extensoes instaladas, o pg_restore
# falha ao recriar funcoes, sequences e tabelas desses schemas.

FROM postgres:17-bookworm

# Evita perguntas interativas do apt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-17-repack \
        postgresql-17-partman \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cria as extensoes no banco default (POSTGRES_DB) na inicializacao.
# O entrypoint oficial do postgres roda todos os scripts .sql em
# /docker-entrypoint-initdb.d/ na primeira subida.
COPY init-extensions.sh /docker-entrypoint-initdb.d/10-extensions.sh

HEALTHCHECK --interval=10s --timeout=5s --retries=10 \
    CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
