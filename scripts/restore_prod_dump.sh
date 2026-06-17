#!/bin/bash
# Restaura o dump de producao no Postgres do Coolify.
#
# Uso:
#   1. Faca upload do dump para o servidor (ex: scp, Coolify volume, etc.)
#   2. No Coolify, va no servico postgres > Exec
#   3. Cole o conteudo deste script (ou copie o dump via Coolify Exec UI)
#
# OU rode localmente apontando para o Postgres do Coolify:
#   POSTGRES_HOST=<host> POSTGRES_PASSWORD=<pwd> ./scripts/restore_prod_dump.sh /caminho/do/dump.dump
#
# O dump eh do pg_dump custom format (PGDMP). Formato 1.16+ requer
# Postgres 16 ou superior (estamos rodando Postgres 17).

set -euo pipefail

DUMP_PATH="${1:-/tmp/finops.dump}"

# Parametros de conexao (lidos do env ou defaults do compose).
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-svc_finops}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD obrigatorio}"
POSTGRES_DB="${POSTGRES_DB:-finopsdatabase}"

export PGPASSWORD="$POSTGRES_PASSWORD"

if [ ! -f "$DUMP_PATH" ]; then
    echo "ERRO: arquivo de dump nao encontrado: $DUMP_PATH"
    echo "Uso: $0 /caminho/do/dump.dump"
    exit 1
fi

echo "Dump: $DUMP_PATH ($(du -h "$DUMP_PATH" | cut -f1))"
echo "Destino: $POSTGRES_USER@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
echo ""

# Confirma que estamos conectados no servidor certo.
SERVER_VERSION=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -tAc "SELECT version()")
echo "Servidor: $SERVER_VERSION"
echo ""

read -p "Isso vai APAGAR o banco $POSTGRES_DB atual. Continuar? (s/N) " CONFIRM
if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Abortado."
    exit 0
fi

echo ""
echo "[1/3] Dropando e recriando banco $POSTGRES_DB..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" \
    -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

echo "[2/3] Rodando pg_restore (pode levar varios minutos)..."
# --no-owner e --no-privileges evitam erros de role mismatch entre prod e o
# Postgres do Coolify (que tem apenas o usuario configurado).
# -j 4 paraleliza. Aumente se o Coolify tiver mais vCPU.
pg_restore \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    -j 4 \
    "$DUMP_PATH" 2>&1 | grep -vE "^(pg_restore: warning: errors ignored|pg_restore: from TOC entry)" || true

echo ""
echo "[3/3] Validando restore..."
TABLES=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')")
ROWS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT COALESCE(SUM(n_live_tup), 0) FROM pg_stat_user_tables")

echo ""
echo "Restore concluido:"
echo "  - Tabelas: $TABLES"
echo "  - Linhas (estimativa): $ROWS"
echo ""
echo "AVISO: se houveram warnings sobre 'extension pg_repack/pg_partman not available',"
echo "       verifique se as extensoes foram instaladas no startup do container postgres."
