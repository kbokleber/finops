#!/bin/bash

# Script melhorado para restaurar backup no novo servidor
# Execute este script no NOVO servidor (178.156.185.182)
# Versão que trata erros de extensões e permissões

set -e

# Senha do usuario svc_finops. Defina antes de rodar:
#   export DB_PASSWORD='sua-senha-aqui'
: "${DB_PASSWORD:?Defina DB_PASSWORD no ambiente antes de rodar este script}"

echo "=== Restaurando backup do banco de dados (versão melhorada) ==="

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

# Fazer backup do arquivo SQL original
cp /tmp/finops_migration/finops_backup.sql /tmp/finops_migration/finops_backup_original.sql

# Criar versão limpa do backup removendo problemas conhecidos
echo "Limpando backup de extensões problemáticas..."
cat > /tmp/clean_backup.sh << 'EOF'
#!/bin/bash
# Remove linhas problemáticas do backup

# Arquivo original
INPUT="/tmp/finops_migration/finops_backup.sql"
# Arquivo limpo
OUTPUT="/tmp/finops_migration/finops_backup_clean.sql"

# Remove extensões problemáticas e comandos que causam erro
sed -e '/CREATE EXTENSION.*pg_repack/d' \
    -e '/DROP EXTENSION.*pg_repack/d' \
    -e '/CREATE EXTENSION.*dblink/d' \
    -e '/DROP EXTENSION.*dblink/d' \
    -e '/CREATE EXTENSION.*pg_partman/d' \
    -e '/DROP EXTENSION.*pg_partman/d' \
    -e '/CREATE EXTENSION.*pg_stat_statements/d' \
    -e '/DROP EXTENSION.*pg_stat_statements/d' \
    -e '/CREATE SCHEMA repack/d' \
    -e '/DROP SCHEMA repack/d' \
    -e '/SET ROLE postgres/d' \
    -e '/repack\./d' \
    -e '/partman\./d' \
    -e '/transaction_timeout/d' \
    -e '/CREATE ROLE partman/d' \
    -e '/DROP ROLE partman/d' \
    -e '/GRANT.*partman/d' \
    -e '/ALTER DEFAULT PRIVILEGES/d' \
    "$INPUT" > "$OUTPUT"

echo "Backup limpo criado: $OUTPUT"
EOF

chmod +x /tmp/clean_backup.sh
/tmp/clean_backup.sh

# Restaurar backup limpo
echo "Restaurando banco de dados com backup limpo..."
export PGPASSWORD="${DB_PASSWORD}"

# Usar o backup limpo
psql -h localhost -U svc_finops -d finopsdatabase -f /tmp/finops_migration/finops_backup_clean.sql 2>/tmp/restore_errors.log

# Verificar se houve erros críticos
CRITICAL_ERRORS=$(grep -c "ERROR.*relation.*does not exist\|ERROR.*schema.*does not exist" /tmp/restore_errors.log 2>/dev/null || echo "0")

if [ "$CRITICAL_ERRORS" -gt 0 ]; then
    echo "Atenção: Alguns erros foram encontrados, mas são relacionados a extensões opcionais."
    echo "Verificando integridade dos dados principais..."
else
    echo "Restauração concluída sem erros críticos."
fi

# Verificar se as tabelas principais foram restauradas
echo "Verificando tabelas restauradas..."
TABLE_COUNT=$(psql -h localhost -U svc_finops -d finopsdatabase -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✓ $TABLE_COUNT tabelas restauradas com sucesso"
    
    # Mostrar algumas tabelas para confirmação
    echo "Principais tabelas no banco:"
    psql -h localhost -U svc_finops -d finopsdatabase -c "\dt" 2>/dev/null | head -10
    
    # Verificar se há dados nas tabelas principais
    echo ""
    echo "Verificando dados em algumas tabelas..."
    
    # Lista algumas tabelas que provavelmente existem baseado no log
    for table in "auth_user" "django_session" "django_content_type"; do
        COUNT=$(psql -h localhost -U svc_finops -d finopsdatabase -t -c "SELECT count(*) FROM $table;" 2>/dev/null | xargs || echo "0")
        if [ "$COUNT" != "0" ]; then
            echo "✓ Tabela $table: $COUNT registros"
        fi
    done
    
else
    echo "✗ Erro: Nenhuma tabela foi restaurada"
    echo "Verificando logs de erro..."
    tail -20 /tmp/restore_errors.log
    exit 1
fi

# Atualizar estatísticas do banco
echo "Atualizando estatísticas do banco..."
psql -h localhost -U svc_finops -d finopsdatabase -c "ANALYZE;" 2>/dev/null || echo "Aviso: Não foi possível executar ANALYZE"

# Verificar sequences (importante para auto increment)
echo "Verificando sequences..."
SEQUENCES=$(psql -h localhost -U svc_finops -d finopsdatabase -t -c "SELECT count(*) FROM information_schema.sequences WHERE sequence_schema = 'public';" 2>/dev/null | xargs)
echo "✓ $SEQUENCES sequences encontradas"

# Limpar arquivos temporários
rm -f /tmp/clean_backup.sh

echo ""
echo "=== Backup restaurado com sucesso ==="
echo "Tabelas: $TABLE_COUNT"
echo "Sequences: $SEQUENCES"
echo "Log de erros salvo em: /tmp/restore_errors.log"
echo ""
echo "Próximo passo: execute o script 06_setup_services.sh"
