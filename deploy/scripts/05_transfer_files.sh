#!/bin/bash

# Script para transferir arquivos do projeto
# Execute este script no servidor ATUAL (finopsSVC01)

set -e

NEW_SERVER="178.156.185.182"

echo "=== Transferindo arquivos do projeto ==="

# Verificar se o novo servidor está acessível
echo "Testando conectividade com o novo servidor..."
ping -c 3 $NEW_SERVER

cd /root

# Criar arquivo compactado com todos os projetos
echo "Criando arquivo compactado..."
tar -czf /tmp/finops_complete.tar.gz \
    finops/ \
    finops_upload/ \
    docker_compose_redis/ \
    docker_compose_rabbit/ \
    grafana/ \
    *.crt \
    *.key \
    scripts/

# Verificar tamanho do arquivo
ls -lh /tmp/finops_complete.tar.gz

# Transferir arquivo para novo servidor
echo "Transferindo arquivo para o novo servidor..."
scp /tmp/finops_complete.tar.gz root@$NEW_SERVER:/tmp/

# Transferir backup do banco (se ainda não foi transferido)
if [ -f "/tmp/finops_migration/finops_backup.sql.gz" ]; then
    echo "Transferindo backup do banco..."
    ssh root@$NEW_SERVER "mkdir -p /tmp/finops_migration"
    scp /tmp/finops_migration/finops_backup.sql.gz root@$NEW_SERVER:/tmp/finops_migration/
fi

echo "=== Transferência concluída ==="
echo "Próximo passo: execute o script 06_setup_services.sh no servidor NOVO"
