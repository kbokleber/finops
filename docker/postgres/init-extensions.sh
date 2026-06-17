#!/bin/bash
# Roda uma vez na inicializacao do data dir (depois do initdb).
# Cria as extensoes no banco padrao (POSTGRES_DB) para que o
# pg_restore possa recriar os objetos dependentes sem erro.

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pg_repack;
    CREATE EXTENSION IF NOT EXISTS pg_partman SCHEMA partman;
EOSQL
