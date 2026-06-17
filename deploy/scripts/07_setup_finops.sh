#!/bin/bash

# Script LEGADO para configurar e iniciar o projeto FinOps.
# Este script assume um setup manual (systemd + docker-compose local)
# e referenciava o IP 172.17.0.1 (Docker Desktop Linux antigo).
# Para deploy novo, use o docker-compose.prod.yml com Coolify
# (ver DEPLOY_COOLIFY.md).
#
# Mantido aqui apenas para referencia historica.

set -e

echo "=== Configurando projeto FinOps ==="

cd /root/finops

# Verificar se arquivo .env existe e está correto
if [ ! -f ".env" ]; then
    echo "Erro: Arquivo .env não encontrado!"
    exit 1
fi

echo "Verificando configurações do .env..."
cat .env

# Verificar conectividade com banco de dados
echo "Testando conectividade com PostgreSQL..."
timeout 10 bash -c "until pg_isready -h \${DB_HOST:-localhost} -p \${DB_PORT:-5432} -U \${DB_USER:-svc_finops}; do sleep 1; done"

if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL acessível"
else
    echo "✗ Erro: PostgreSQL não está acessível"
    exit 1
fi

# Verificar conectividade com Redis
echo "Testando conectividade com Redis..."
if docker exec docker_compose_redis-redis-1 redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis acessível"
else
    echo "✗ Erro: Redis não está acessível"
    exit 1
fi

# Verificar conectividade com RabbitMQ
echo "Testando conectividade com RabbitMQ..."
if curl -s -u guest:guest http://localhost:15672/api/overview > /dev/null 2>&1; then
    echo "✓ RabbitMQ acessível"
else
    echo "✗ Erro: RabbitMQ não está acessível"
    exit 1
fi

# Construir e iniciar o projeto FinOps
echo "Construindo e iniciando projeto FinOps..."
docker-compose up -d --build

# Aguardar containers inicializarem
echo "Aguardando containers inicializarem..."
sleep 30

# Verificar se todos os containers estão rodando
echo "Verificando status dos containers FinOps..."
docker-compose ps

# Verificar logs para erros
echo "Verificando logs dos workers..."
docker logs finops-finops_worker_faz-1 --tail 20
echo ""
docker logs finops-finops_worker_faz2-1 --tail 20
echo ""
docker logs finops-finops_worker_verifica-1 --tail 20
echo ""
docker logs finops-finops_celery_beat-1 --tail 20

# Testar Celery dentro do container
echo "Testando status do Celery..."
docker exec finops-finops_worker_faz-1 celery -A finops_celery inspect ping || echo "Aviso: Celery ainda inicializando..."

echo ""
echo "=== Projeto FinOps configurado ==="
echo "Próximo passo: execute o script 08_final_verification.sh para verificações finais"
