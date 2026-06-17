#!/bin/bash

echo "🚀 CONFIGURANDO DASHBOARD FINOPS"
echo "="*40

echo "⚠️  AVISO: O Dashboard agora está integrado ao projeto FinOps!"
echo "Nova localização: /root/finops/dashboard/"
echo ""

# Instalar dependências Python
echo "📦 Instalando dependências..."
pip3 install flask psycopg2-binary pytz

# Verificar se o Flask foi instalado
if python3 -c "import flask" 2>/dev/null; then
    echo "✅ Flask instalado com sucesso"
else
    echo "❌ Erro na instalação do Flask"
    exit 1
fi

# Verificar se psycopg2 foi instalado
if python3 -c "import psycopg2" 2>/dev/null; then
    echo "✅ psycopg2 instalado com sucesso"
else
    echo "❌ Erro na instalação do psycopg2"
    exit 1
fi

# Verificar se pytz foi instalado  
if python3 -c "import pytz" 2>/dev/null; then
    echo "✅ pytz instalado com sucesso"
else
    echo "❌ Erro na instalação do pytz"
    exit 1
fi

echo -e "\n🎯 DASHBOARD FINOPS PRONTO!"
echo "="*40
echo "Para iniciar o dashboard:"
echo "  Opção 1 (Recomendado):"
echo "    cd /root/finops"
echo "    ./start_finops.sh"
echo ""
echo "  Opção 2 (Apenas dashboard):"
echo "    cd /root/finops"
echo "    python3 run_dashboard.py"
echo ""
echo "  Opção 3 (Service script):"
echo "    /root/scripts/dashboard_service.sh start"
echo ""
echo "Acesse no navegador:"
echo "  http://localhost:5000"
echo ""
echo "Funcionalidades disponíveis:"
echo "  ✅ Status dos provedores OCI em tempo real"
echo "  ✅ Dados processados dos últimos 7 dias"
echo "  ✅ Status dos containers Docker"
echo "  ✅ Tabelas de controle OCI"
echo "  ✅ Status das tarefas Celery"
echo "  ✅ Logs dos containers em tempo real"
echo "  ✅ Atualização automática a cada 30 segundos"
echo ""
echo "💡 Dica: Use Ctrl+C para parar o servidor"
