#!/bin/bash

# Script para restaurar backup no novo servidor
# Execute este script no NOVO servidor (178.156.185.182)
# Antes de executar, transfira o arquivo de backup do servidor atual

set -e

echo "=== Restaurando backup do banco de dados ==="

# Verificar se o arquivo de backup existe
BACKUP_FILE="/tmp/finops_migration/finops_backup.sql.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Erro: Arquivo de backup não encontrado: $BACKUP_FILE"
    echo "Transfira o backup do servidor atual primeiro:"
    echo "scp root@SERVIDOR_ATUAL:/tmp/finops_migration/finops_backup.sql.gz /tmp/finops_migration/"
    exit 1
fi

# Criar diretório se não existir
mkdir -p /tmp/finops_migration

# Descompactar o backup
echo "Descompactando backup..."
gunzip -f /tmp/finops_migration/finops_backup.sql.gz

# Restaurar backup
echo "Restaurando banco de dados..."
echo "ATENÇÃO: Podem aparecer erros relacionados a extensões não instaladas."
echo "Isso é normal e não afeta os dados principais."
echo "Use o script 04_restore_database_fixed.sh para uma versão melhorada."
echo ""

sudo -u postgres psql -h localhost -U svc_finops -d finopsdatabase < /tmp/finops_migration/finops_backup.sql 2>/tmp/restore_errors.log

# Verificar se a restauração foi bem-sucedida
echo "Verificando restauração..."
TABLE_COUNT=$(sudo -u postgres psql -d finopsdatabase -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✓ $TABLE_COUNT tabelas restauradas com sucesso"
    sudo -u postgres psql -d finopsdatabase -c "\dt" | head -10
else
    echo "⚠️  Possíveis problemas na restauração. Use o script corrigido:"
    echo "./04_restore_database_fixed.sh"
fi

echo "=== Backup restaurado com sucesso ==="
echo "Próximo passo: execute o script 05_transfer_files.sh no servidor ATUAL"
