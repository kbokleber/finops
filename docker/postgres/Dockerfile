# Postgres 17 com extensoes usadas em producao.
# Build em duas etapas para isolar falhas e minimizar o tamanho final.
#
# O dump de producao referencia os schemas:
#   - repack  (pg_repack) - funcoes, sequences e tabelas
#   - partman (pg_partman) - funcoes, sequences e tabelas
# Sem essas extensoes instaladas, o pg_restore falha.

# ----------------------------------------------------------------------------
# Etapa 1: builder com toolchain de compilacao
# Instala pg_repack do source (PGDG traz python3.11 inteiro como dep,
# o que infla demais a imagem final).
# ----------------------------------------------------------------------------
FROM postgres:17-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-server-dev-17 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Baixa e compila pg_repack 1.5.3 (suporta PG 17)
WORKDIR /tmp
RUN curl -fsSL -o pg_repack.tar.gz \
        https://github.com/reorg/pg_repack/archive/refs/tags/ver_1.5.3.tar.gz \
    && tar xzf pg_repack.tar.gz \
    && cd pg_repack-ver_1.5.3 \
    && make \
    && make install \
    && cd /tmp \
    && rm -rf pg_repack.tar.gz pg_repack-ver_1.5.3

# ----------------------------------------------------------------------------
# Etapa 2: imagem final
# - Copia pg_repack compilado do builder
# - Instala pg_partman via PGDG (binario pre-construido)
# ----------------------------------------------------------------------------
FROM postgres:17-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-17-partman \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/lib/postgresql/17/lib/pg_repack.so /usr/lib/postgresql/17/lib/
COPY --from=builder /usr/share/postgresql/17/extension/pg_repack.control /usr/share/postgresql/17/extension/
COPY --from=builder /usr/share/postgresql/17/extension/pg_repack--*.sql /usr/share/postgresql/17/extension/

# Cria as extensoes no banco default (POSTGRES_DB) na inicializacao.
COPY docker/postgres/init-extensions.sh /docker-entrypoint-initdb.d/10-extensions.sh

HEALTHCHECK --interval=15s --timeout=10s --retries=30 --start-period=120s \
    CMD pg_isready -U svc_finops -d finopsdatabase
