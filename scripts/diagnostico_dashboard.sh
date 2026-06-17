#!/bin/bash
# Script de diagnóstico do Dashboard FinOps

echo "🔍 DIAGNÓSTICO COMPLETO DO DASHBOARD FINOPS"
echo "==========================================="

echo ""
echo "1️⃣ Verificando diretórios e arquivos..."
echo "📁 Diretório principal: /root/finops"
if [ -d "/root/finops" ]; then
    echo "   ✅ Diretório existe"
else
    echo "   ❌ Diretório não encontrado"
fi

echo "📄 Arquivo run_dashboard.py:"
if [ -f "/root/finops/run_dashboard.py" ]; then
    echo "   ✅ Arquivo existe"
else
    echo "   ❌ Arquivo não encontrado"
fi

echo "📄 Diretório dashboard:"
if [ -d "/root/finops/dashboard" ]; then
    echo "   ✅ Diretório existe"
    if [ -f "/root/finops/dashboard/app.py" ]; then
        echo "   ✅ app.py existe"
    else
        echo "   ❌ app.py não encontrado"
    fi
else
    echo "   ❌ Diretório dashboard não encontrado"
fi

echo ""
echo "2️⃣ Verificando porta 5000..."
PORT_CHECK=$(netstat -tulpn | grep :5000)
if [ -n "$PORT_CHECK" ]; then
    echo "   ⚠️ Porta 5000 em uso:"
    echo "   $PORT_CHECK"
else
    echo "   ✅ Porta 5000 livre"
fi

echo ""
echo "3️⃣ Verificando processos do dashboard..."
DASHBOARD_PROCESSES=$(pgrep -f "run_dashboard\|app\.py" | head -5)
if [ -n "$DASHBOARD_PROCESSES" ]; then
    echo "   📊 Processos encontrados:"
    for pid in $DASHBOARD_PROCESSES; do
        PROC_INFO=$(ps aux | grep $pid | grep -v grep | head -1)
        echo "      PID $pid: $PROC_INFO"
    done
else
    echo "   ⚠️ Nenhum processo do dashboard encontrado"
fi

echo ""
echo "4️⃣ Testando conectividade..."
if command -v curl > /dev/null; then
    if curl -s --connect-timeout 3 http://localhost:5000 > /dev/null 2>&1; then
        echo "   ✅ Dashboard respondendo em http://localhost:5000"
    else
        echo "   ❌ Dashboard não responde"
    fi
else
    echo "   ⚠️ curl não instalado - não é possível testar conectividade"
fi

echo ""
echo "5️⃣ Verificando logs..."
if [ -f "/root/finops/dashboard.log" ]; then
    echo "   📋 Últimas 5 linhas do log:"
    tail -5 /root/finops/dashboard.log | sed 's/^/      /'
else
    echo "   ⚠️ Arquivo de log não encontrado"
fi

echo ""
echo "6️⃣ Verificando serviço systemd..."
SERVICE_STATUS=$(systemctl is-active finops-dashboard.service 2>/dev/null)
echo "   Status do serviço: $SERVICE_STATUS"

echo ""
echo "7️⃣ Verificando dependências Python..."
echo "   Flask:"
python3 -c "import flask; print(f'      ✅ Flask {flask.__version__}')" 2>/dev/null || echo "      ❌ Flask não encontrado"

echo "   Flask-Session:"
python3 -c "import flask_session; print('      ✅ Flask-Session instalado')" 2>/dev/null || echo "      ❌ Flask-Session não encontrado"

echo "   MSAL:"
python3 -c "import msal; print('      ✅ MSAL instalado')" 2>/dev/null || echo "      ❌ MSAL não encontrado"

echo ""
echo "🎯 RESUMO DO DIAGNÓSTICO"
echo "======================="

# Status geral
if [ -f "/root/finops/run_dashboard.py" ] && [ -d "/root/finops/dashboard" ]; then
    echo "✅ Arquivos principais: OK"
else
    echo "❌ Arquivos principais: PROBLEMA"
fi

if [ -z "$PORT_CHECK" ]; then
    echo "✅ Porta 5000: LIVRE"
else
    echo "⚠️ Porta 5000: EM USO"
fi

if curl -s --connect-timeout 3 http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ Dashboard: FUNCIONANDO"
else
    echo "❌ Dashboard: NÃO RESPONDE"
fi

echo ""
echo "💡 RECOMENDAÇÕES:"
echo "=================="
echo "1. Use: ./dashboard_manager.sh start (método recomendado)"
echo "2. Para logs: ./dashboard_manager.sh logs"
echo "3. Para status: ./dashboard_manager.sh status"
echo "4. Se houver problemas, primeiro: ./dashboard_manager.sh stop"
