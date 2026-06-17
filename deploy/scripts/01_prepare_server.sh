#!/bin/bash

# Script para preparar o novo servidor (178.156.185.182)
# Execute este script no NOVO servidor

set -e

echo "=== Iniciando preparação do novo servidor ==="

# Atualizar sistema
echo "Atualizando sistema..."
apt update && apt upgrade -y

# Instalar Docker
echo "Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Instalar Docker Compose
echo "Instalando Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Instalar PostgreSQL
echo "Instalando PostgreSQL..."
apt install postgresql postgresql-contrib -y

# Instalar outras ferramentas
echo "Instalando ferramentas adicionais..."
apt install git rsync htop nano net-tools -y

# Criar a rede Docker externa com labels corretos
echo "Criando rede Docker..."
docker network create brigde --label com.docker.compose.network=default || echo "Rede brigde já existe"

# Iniciar PostgreSQL
echo "Iniciando PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

echo "=== Preparação do servidor concluída ==="
echo "Próximo passo: execute o script 02_setup_postgresql.sh"
