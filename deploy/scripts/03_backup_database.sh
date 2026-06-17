#!/bin/bash

# Script para fazer backup do banco de dados
# Execute este script no servidor ATUAL (finopsSVC01)

set -e

echo "=== Fazendo backup do banco de dados ==="

# Criar diretório de backup se não existir
mkdir -p /tmp/finops_migration

# Fazer backup do banco
echo "Criando backup do banco finopsdatabase..."
sudo -u postgres pg_dump -h localhost -U svc_finops -d finopsdatabase > /tmp/finops_migration/finops_backup.sql

# Compactar o backup
echo "Compactando backup..."
gzip /tmp/finops_migration/finops_backup.sql

# Verificar tamanho do backup
ls -lh /tmp/finops_migration/finops_backup.sql.gz

echo "=== Backup criado com sucesso ==="
echo "Arquivo: /tmp/finops_migration/finops_backup.sql.gz"
echo "Próximo passo: execute o script 04_restore_database.sh no servidor NOVO"
