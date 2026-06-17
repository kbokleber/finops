#!/bin/bash

# Script para verificação final da migração
# Execute este script no NOVO servidor (178.156.185.182)

set -e

echo "=== Verificação final da migração ==="

# Verificar todos os containers
echo "1. Verificando containers Docker..."
echo "=================================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verificar PostgreSQL
echo ""
echo "2. Verificando PostgreSQL..."
echo "============================"
systemctl status postgresql --no-pager | head -10
sudo -u postgres psql -d finopsdatabase -c "SELECT count(*) as tabelas FROM information_schema.tables WHERE table_schema = 'public';"

# Verificar Redis
echo ""
echo "3. Verificando Redis..."
echo "======================="
docker exec docker_compose_redis-redis-1 redis-cli ping
docker exec docker_compose_redis-redis-1 redis-cli info replication | head -5

# Verificar RabbitMQ
echo ""
echo "4. Verificando RabbitMQ..."
echo "=========================="
curl -s -u guest:guest http://localhost:15672/api/overview | grep -o '"rabbitmq_version":"[^"]*"'

# Verificar Grafana
echo ""
echo "5. Verificando Grafana..."
echo "========================="
curl -k -s https://localhost:443/api/health | grep -o '"database":"[^"]*"'

# Verificar workers Celery
echo ""
echo "6. Verificando workers Celery..."
echo "================================="
docker exec finops-finops_worker_faz-1 celery -A finops_celery inspect active | head -10

# Verificar redes Docker
echo ""
echo "7. Verificando redes Docker..."
echo "=============================="
docker network ls | grep brigde

# Verificar volumes Docker
echo ""
echo "8. Verificando volumes Docker..."
echo "================================"
docker volume ls

# Verificar portas em uso
echo ""
echo "9. Verificando portas em uso..."
echo "==============================="
netstat -tlnp | grep -E "(443|5672|15672|6379|5432)" | head -10

# Verificar espaço em disco
echo ""
echo "10. Verificando espaço em disco..."
echo "=================================="
df -h / | tail -1

# Resumo final
echo ""
echo "=== RESUMO DA MIGRAÇÃO ==="
echo "=========================="

# Contar containers rodando
CONTAINERS_RUNNING=$(docker ps | wc -l)
echo "Containers rodando: $((CONTAINERS_RUNNING - 1))"

# Verificar se todos os serviços principais estão rodando
SERVICES_OK=0

if docker ps | grep -q "redis"; then
    echo "✓ Redis: OK"
    ((SERVICES_OK++))
else
    echo "✗ Redis: FALHA"
fi

if docker ps | grep -q "rabbitmq"; then
    echo "✓ RabbitMQ: OK"
    ((SERVICES_OK++))
else
    echo "✗ RabbitMQ: FALHA"
fi

if docker ps | grep -q "grafana"; then
    echo "✓ Grafana: OK"
    ((SERVICES_OK++))
else
    echo "✗ Grafana: FALHA"
fi

if docker ps | grep -q "finops"; then
    FINOPS_CONTAINERS=$(docker ps | grep finops | wc -l)
    echo "✓ FinOps Workers: OK ($FINOPS_CONTAINERS containers)"
    ((SERVICES_OK++))
else
    echo "✗ FinOps Workers: FALHA"
fi

if systemctl is-active --quiet postgresql; then
    echo "✓ PostgreSQL: OK"
    ((SERVICES_OK++))
else
    echo "✗ PostgreSQL: FALHA"
fi

echo ""
echo "Serviços funcionando: $SERVICES_OK/5"

if [ $SERVICES_OK -eq 5 ]; then
    echo ""
    echo "🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "=================================="
    echo ""
    echo "URLs de acesso:"
    echo "- Grafana: https://$(hostname -I | awk '{print $1}'):443 (admin/admin)"
    echo "- RabbitMQ: http://$(hostname -I | awk '{print $1}'):15672 (guest/guest)"
    echo ""
    echo "Para monitorar os workers FinOps:"
    echo "docker logs finops-finops_worker_faz-1 -f"
    echo ""
    echo "Backup automático configurado em: /root/backup_finops.sh"
else
    echo ""
    echo "⚠️  ATENÇÃO: Alguns serviços não estão funcionando corretamente"
    echo "Verifique os logs dos containers com falha."
fi
