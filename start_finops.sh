#!/bin/bash

echo "🚀 INICIANDO SISTEMA FINOPS COMPLETO"
echo "===================================="

# Função para verificar se um serviço está rodando
check_service() {
    local service_name=$1
    local port=$2
    
    if netstat -tuln | grep ":$port" > /dev/null; then
        echo "✅ $service_name está rodando na porta $port"
        return 0
    else
        echo "❌ $service_name NÃO está rodando na porta $port"
        return 1
    fi
}

# Verificar dependências
echo "🔍 Verificando dependências..."

# PostgreSQL
if ! check_service "PostgreSQL" "5432"; then
    echo "⚠️ PostgreSQL deve estar rodando. Execute:"
    echo "   sudo systemctl start postgresql"
    echo "   ou"
    echo "   docker-compose up -d postgres"
fi

# Redis (se usando)
if ! check_service "Redis" "6379"; then
    echo "⚠️ Redis deve estar rodando. Execute:"
    echo "   docker-compose -f /root/docker_compose_redis/docker-compose.yml up -d"
fi

echo ""
echo "📦 Iniciando containers FinOps..."

# Construir e iniciar containers
docker-compose up -d --build

echo ""
echo "⏳ Aguardando containers iniciarem..."
sleep 10

echo ""
echo "📊 Iniciando Dashboard..."

# Iniciar dashboard em background
nohup python3 run_dashboard.py > dashboard.log 2>&1 &
DASHBOARD_PID=$!

echo "🆔 Dashboard PID: $DASHBOARD_PID"
echo "$DASHBOARD_PID" > dashboard.pid

echo ""
echo "✅ SISTEMA FINOPS INICIADO!"
echo ""
echo "📊 Serviços Disponíveis:"
echo "   • Dashboard FinOps: http://localhost:5000"
echo "   • Grafana: http://localhost:3000"
echo ""
echo "🔧 Comandos Úteis:"
echo "   • Ver status: docker-compose ps"
echo "   • Ver logs: docker-compose logs -f"
echo "   • Parar tudo: docker-compose down"
echo "   • Parar dashboard: kill \$(cat dashboard.pid)"
echo ""
echo "📄 Logs do dashboard: dashboard.log"