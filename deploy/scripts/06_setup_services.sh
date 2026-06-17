#!/bin/bash

# Script para configurar serviços Docker no novo servidor
# Execute este script no NOVO servidor (178.156.185.182)

set -e

echo "=== Configurando serviços Docker ==="

cd /root

# Extrair arquivos transferidos
if [ -f "/tmp/finops_complete.tar.gz" ]; then
    echo "Extraindo arquivos do projeto..."
    tar -xzf /tmp/finops_complete.tar.gz
else
    echo "Erro: Arquivo finops_complete.tar.gz não encontrado em /tmp/"
    exit 1
fi

# Criar diretório para RabbitMQ
echo "Criando diretório para RabbitMQ..."
mkdir -p /usr/projects/predict-rabbitmq

# Corrigir problema da rede Docker
echo "Corrigindo configuração da rede Docker..."
docker network rm brigde 2>/dev/null || true
docker network create brigde --label com.docker.compose.network=default

# Iniciar Redis
echo "Iniciando Redis..."
cd /root/docker_compose_redis
docker-compose up -d

# Aguardar Redis inicializar
sleep 10

# Verificar Redis
docker ps | grep redis
if [ $? -eq 0 ]; then
    echo "✓ Redis iniciado com sucesso"
else
    echo "✗ Erro ao iniciar Redis"
    exit 1
fi

# Iniciar RabbitMQ
echo "Iniciando RabbitMQ..."
cd /root/docker_compose_rabbit
docker-compose up -d

# Aguardar RabbitMQ inicializar
sleep 15

# Verificar RabbitMQ
docker ps | grep rabbitmq
if [ $? -eq 0 ]; then
    echo "✓ RabbitMQ iniciado com sucesso"
    echo "Interface web disponível em: http://$(hostname -I | awk '{print $1}'):15672"
    echo "Usuário: guest | Senha: guest"
else
    echo "✗ Erro ao iniciar RabbitMQ"
    exit 1
fi

# Configurar certificados para Grafana
echo "Configurando certificados para Grafana..."
if [ -f "/root/service_com_br_full.crt" ] && [ -f "/root/service_com_br_full.key" ]; then
    cp /root/service_com_br_full.crt /root/grafana/certificados/service.com.br.crt
    cp /root/service_com_br_full.key /root/grafana/certificados/service.com.br.key
    chmod 644 /root/grafana/certificados/service.com.br.crt
    chmod 600 /root/grafana/certificados/service.com.br.key
fi

# Iniciar Grafana
echo "Iniciando Grafana..."
cd /root/grafana
docker-compose up -d

# Aguardar Grafana inicializar
sleep 15

# Verificar Grafana
docker ps | grep grafana
if [ $? -eq 0 ]; then
    echo "✓ Grafana iniciado com sucesso"
    echo "Interface web disponível em: https://$(hostname -I | awk '{print $1}'):443"
    echo "Usuário: admin | Senha: admin"
else
    echo "✗ Erro ao iniciar Grafana"
    exit 1
fi

# Verificar status de todos os serviços
echo ""
echo "=== Status dos serviços ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Serviços configurados com sucesso ==="
echo "Próximo passo: execute o script 07_setup_finops.sh"
