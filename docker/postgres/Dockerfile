# Postgres 17 com extensoes usadas em producao.
# Necessario porque o dump referencia os schemas repack (pg_repack)
# e partman (pg_partman). Sem isso o pg_restore falha.
#
# Estrategia de duas etapas:
#   1) Instalar postgresql-17-partman via PGDG (binario pre-construido)
#   2) Compilar pg_repack do source (nao tem binario confiavel no PGDG)

FROM postgres:17-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Etapa 1: instalar pg_partman (binario) e dependencias minimas para
# compilar pg_repack. Mantem python3 fora para nao arrastar 100MB de deps.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-17-partman \
        build-essential \
        libpq-dev \
        postgresql-server-dev-17 \
        ca-certificates \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Etapa 2: compilar pg_repack 1.5.3 do source oficial.
# Limpa o source depois para manter a imagem final pequena.
WORKDIR /tmp
RUN wget -q https://github.com/reorg/pg_repack/archive/refs/tags/ver_1.5.3.tar.gz \
    && tar xzf ver_1.5.3.tar.gz \
    && cd pg_repack-ver_1.5.3 \
    && make \
    && make install \
    && cd .. \
    && rm -rf ver_1.5.3.tar.gz pg_repack-ver_1.5.3 \
    && apt-get purge -y --auto-remove \
        build-essential \
        wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cria as extensoes no banco default (POSTGRES_DB) na inicializacao.
COPY docker/postgres/init-extensions.sh /docker-entrypoint-initdb.d/10-extensions.sh

HEALTHCHECK --interval=15s --timeout=10s --retries=30 --start_period=120s \
    CMD pg_isready -U svc_finops -d finopsdatabase
