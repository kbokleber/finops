#!/bin/bash

# Script para corrigir conectividade externa do PostgreSQL
# Execute este script no servidor NOVO (178.156.185.182)

set -e

# Senha do usuario svc_finops. Defina antes de rodar:
#   export DB_PASSWORD='sua-senha-aqui'
: "${DB_PASSWORD:?Defina DB_PASSWORD no ambiente antes de rodar este script}"

echo "=== Configurando acesso externo ao PostgreSQL ==="

# Identificar versão do PostgreSQL
PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
echo "Versão do PostgreSQL: $PG_VERSION"

# Caminhos dos arquivos de configuração
PG_HBA_FILE="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
PG_CONF_FILE="/etc/postgresql/$PG_VERSION/main/postgresql.conf"

echo "Arquivo pg_hba.conf: $PG_HBA_FILE"
echo "Arquivo postgresql.conf: $PG_CONF_FILE"

# Fazer backup dos arquivos originais
echo "Fazendo backup das configurações..."
cp $PG_HBA_FILE $PG_HBA_FILE.backup.$(date +%Y%m%d_%H%M%S)
cp $PG_CONF_FILE $PG_CONF_FILE.backup.$(date +%Y%m%d_%H%M%S)

# Configurar pg_hba.conf para permitir conexões externas
echo "Configurando pg_hba.conf..."

# Adicionar entrada para o IP específico do DBeaver
echo "# Acesso para DBeaver" >> $PG_HBA_FILE
echo "host    finopsdatabase    svc_finops    187.122.59.3/32    md5" >> $PG_HBA_FILE

# Adicionar entrada para containers Docker (se ainda não existir)
if ! grep -q "172.17.0.0/16" $PG_HBA_FILE; then
    echo "host    finopsdatabase    svc_finops    172.17.0.0/16    md5" >> $PG_HBA_FILE
fi

# Adicionar entrada para rede local (opcional, para administração)
echo "host    finopsdatabase    svc_finops    10.0.0.0/8       md5" >> $PG_HBA_FILE
echo "host    finopsdatabase    svc_finops    192.168.0.0/16   md5" >> $PG_HBA_FILE

# Configurar postgresql.conf para aceitar conexões externas
echo "Configurando postgresql.conf..."

# Verificar se listen_addresses já está configurado
if grep -q "^listen_addresses" $PG_CONF_FILE; then
    # Substituir linha existente
    sed -i "s/^listen_addresses.*/listen_addresses = '*'/" $PG_CONF_FILE
else
    # Adicionar nova linha
    echo "listen_addresses = '*'" >> $PG_CONF_FILE
fi

# Configurar SSL (opcional, mas recomendado)
if grep -q "^ssl = " $PG_CONF_FILE; then
    sed -i "s/^ssl = .*/ssl = on/" $PG_CONF_FILE
else
    echo "ssl = on" >> $PG_CONF_FILE
fi

# Mostrar as configurações adicionadas
echo ""
echo "=== Configurações adicionadas ==="
echo "Entradas no pg_hba.conf:"
tail -10 $PG_HBA_FILE

echo ""
echo "Configuração do postgresql.conf:"
grep -E "^listen_addresses|^ssl = " $PG_CONF_FILE

# Reiniciar PostgreSQL para aplicar as configurações
echo ""
echo "Reiniciando PostgreSQL..."
systemctl restart postgresql

# Verificar se o serviço está rodando
sleep 5
systemctl status postgresql --no-pager

# Verificar se está escutando na porta 5432
echo ""
echo "Verificando porta 5432..."
netstat -tlnp | grep :5432

# Testar conexão local
echo ""
echo "Testando conexão local..."
export PGPASSWORD="${DB_PASSWORD}"
psql -h localhost -U svc_finops -d finopsdatabase -c "SELECT version();"

# Verificar firewall
echo ""
echo "=== Verificando firewall ==="
ufw status | grep 5432 || echo "Porta 5432 não está aberta no firewall"

echo ""
echo "=== Configuração concluída ==="
echo ""
echo "📋 Dados para conectar no DBeaver:"
echo "Host: 178.156.185.182"
echo "Porta: 5432"
echo "Database: finopsdatabase"
echo "Usuário: svc_finops"
echo "Senha: \$DB_PASSWORD (definida no ambiente)"
echo "SSL: Requerido"
echo ""
echo "⚠️  Se ainda não conseguir conectar, execute:"
echo "sudo ufw allow 5432/tcp"
echo ""
echo "Para reverter as configurações, use os backups:"
echo "ls -la /etc/postgresql/$PG_VERSION/main/*.backup.*"
