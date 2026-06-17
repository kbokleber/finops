#!/bin/bash

# Script opcional para instalar extensões PostgreSQL
# Execute este script no NOVO servidor se quiser todas as funcionalidades

set -e

echo "=== Instalando extensões PostgreSQL (opcional) ==="

# Verificar versão do PostgreSQL
PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
echo "Versão do PostgreSQL detectada: $PG_VERSION"

# Instalar extensões via apt
echo "Instalando extensões via apt..."
apt update

# Instalar contrib (inclui dblink e pg_stat_statements)
apt install postgresql-contrib-$PG_VERSION -y

# Tentar instalar pg_partman se disponível
apt install postgresql-$PG_VERSION-partman -y 2>/dev/null || echo "pg_partman não disponível via apt"

# Tentar instalar pg_repack se disponível  
apt install postgresql-$PG_VERSION-repack -y 2>/dev/null || echo "pg_repack não disponível via apt"

# Reiniciar PostgreSQL para carregar extensões
systemctl restart postgresql

# Habilitar extensões no banco como superuser
echo "Habilitando extensões no banco de dados..."
sudo -u postgres psql -d finopsdatabase << 'EOF'
-- Extensões básicas que geralmente estão disponíveis
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Verificar extensões instaladas
\dx
EOF

echo "=== Instalação de extensões concluída ==="
echo "Execute novamente o restore se necessário:"
echo "./04_restore_database_fixed.sh"
