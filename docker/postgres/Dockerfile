# Postgres 17 com extensoes usadas em producao.
# O dump de producao referencia os schemas repack (pg_repack) e partman
# (pg_partman). Sem essas extensoes, o pg_restore falha.
#
# Estrategia: multi-stage build.
#   Estagio 1 (builder): compila pg_repack do source (mais leve que o
#                        pacote PGDG, que arrasta python3 inteiro)
#   Estagio 2 (final):   postgres:17-bookworm + pg_partman (PGDG) +
#                        pg_repack copiado do builder

# ----------------------------------------------------------------------------
# Estagio 1: builder
# ----------------------------------------------------------------------------
FROM postgres:17-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Dependencias necessarias para compilar pg_repack:
#   - build-essential: gcc, make, etc
#   - libpq-dev: headers do libpq
#   - postgresql-server-dev-17: pg_config + headers do postgres
#   - liblz4-dev, libzstd-dev, zlib1g-dev, libreadline-dev: deps adicionais
#     que o pg_repack precisa (faltavam no build anterior)
#   - ca-certificates: para baixar do GitHub via HTTPS
#   - curl: para o download
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql-server-dev-17 \
        liblz4-dev \
        libzstd-dev \
        zlib1g-dev \
        libreadline-dev \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Baixa e compila pg_repack 1.5.3 (suporta PG 17 segundo release notes).
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
# Estagio 2: imagem final
# ----------------------------------------------------------------------------
FROM postgres:17-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Instala pg_partman via PGDG (binario pre-construido)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-17-partman \
    && rm -rf /var/lib/apt/lists/*

# Copia pg_repack compilado do builder
COPY --from=builder /usr/lib/postgresql/17/lib/pg_repack.so /usr/lib/postgresql/17/lib/
COPY --from=builder /usr/share/postgresql/17/extension/pg_repack.control /usr/share/postgresql/17/extension/
COPY --from=builder /usr/share/postgresql/17/extension/pg_repack--*.sql /usr/share/postgresql/17/extension/

# Cria as extensoes no banco default (POSTGRES_DB) na inicializacao.
COPY docker/postgres/init-extensions.sh /docker-entrypoint-initdb.d/10-extensions.sh

HEALTHCHECK --interval=15s --timeout=10s --retries=30 --start-period=120s \
    CMD pg_isready -U svc_finops -d finopsdatabase
