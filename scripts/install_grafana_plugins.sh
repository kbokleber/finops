#!/bin/bash

# Script para instalar plugins VolkovLabs no Grafana
# Data: $(date +"%Y-%m-%d")

echo "========================================"
echo "  INSTALAÇÃO PLUGINS VOLKOVLABS GRAFANA"
echo "========================================"
echo ""

CONTAINER_NAME="grafana-grafana-1"

# Verificar se o container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    echo "   Execute: cd /root/grafana && docker-compose up -d"
    exit 1
fi

echo "✅ Container Grafana encontrado: $CONTAINER_NAME"
echo ""

# Lista de plugins VolkovLabs essenciais
PLUGINS=(
    "volkovlabs-variable-panel"
    "volkovlabs-form-panel"
    "volkovlabs-image-panel" 
    "volkovlabs-table-panel"
    "volkovlabs-echarts-panel"
)

echo "🔄 Instalando plugins VolkovLabs..."
echo ""

for plugin in "${PLUGINS[@]}"; do
    echo "📦 Instalando: $plugin"
    if docker exec "$CONTAINER_NAME" grafana cli plugins install "$plugin" 2>/dev/null; then
        echo "   ✅ $plugin instalado com sucesso"
    else
        echo "   ⚠️  $plugin já instalado ou erro na instalação"
    fi
done

echo ""
echo "🔄 Reiniciando Grafana para aplicar plugins..."

cd /root/grafana && docker-compose restart grafana

echo ""
echo "⏳ Aguardando inicialização..."
sleep 10

echo ""
echo "📋 Plugins instalados:"
docker exec "$CONTAINER_NAME" grafana cli plugins ls

echo ""
echo "🌐 Testando conectividade:"
status=$(curl -k -s -w "%{http_code}" -H "Host: devfinops.service.com.br" https://localhost -o /dev/null)
if [ "$status" = "302" ] || [ "$status" = "200" ]; then
    echo "   ✅ Grafana respondendo (Status: $status)"
    echo "   🌍 Acesse: https://devfinops.service.com.br"
else
    echo "   ❌ Grafana não está respondendo (Status: $status)"
fi

echo ""
echo "========================================"
echo "✅ Instalação concluída!"
echo "========================================"