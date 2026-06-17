#!/bin/bash

# Script para configurar PostgreSQL no novo servidor
# Execute este script no NOVO servidor

set -e

# Senha do usuario svc_finops. Defina antes de rodar:
#   export DB_PASSWORD='sua-senha-aqui'
: "${DB_PASSWORD:?Defina DB_PASSWORD no ambiente antes de rodar este script}"

echo "=== Configurando PostgreSQL ==="

# Configurar usuário e banco de dados
echo "Criando usuário e banco de dados..."
sudo -u postgres psql << EOF
CREATE USER svc_finops WITH PASSWORD '${DB_PASSWORD}';
CREATE DATABASE finopsdatabase OWNER svc_finops;
GRANT ALL PRIVILEGES ON DATABASE finopsdatabase TO svc_finops;
\q
EOF

# Fazer backup das configurações atuais
cp /etc/postgresql/*/main/pg_hba.conf /etc/postgresql/*/main/pg_hba.conf.backup
cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup

# Configurar acesso ao PostgreSQL para containers Docker
echo "Configurando acesso para containers Docker..."
echo "host    finopsdatabase    svc_finops    172.17.0.0/16    md5" >> /etc/postgresql/*/main/pg_hba.conf

# Configurar PostgreSQL para aceitar conexões externas
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf

# Reiniciar PostgreSQL
echo "Reiniciando PostgreSQL..."
systemctl restart postgresql

# Verificar se está funcionando
echo "Testando conexão..."
sudo -u postgres psql -d finopsdatabase -c "SELECT version();"

# Verificar status
systemctl status postgresql --no-pager

echo "=== PostgreSQL configurado com sucesso ==="
echo "Próximo passo: execute o script 03_backup_database.sh no servidor ATUAL"
