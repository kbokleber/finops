#!/bin/bash
# Script para testar a persistência do dashboard

echo "🧪 TESTE DE PERSISTÊNCIA DO DASHBOARD"
echo "====================================="

# Verificar status inicial
echo "1️⃣ Status inicial:"
cd /root/finops && ./dashboard_manager.sh status

echo ""
echo "2️⃣ Testando independência do terminal..."
echo "   Simulando fechamento de terminal (SIGHUP)..."

# Obter PID do dashboard
DASHBOARD_PID=$(pgrep -f "run_dashboard\.py" | head -1)

if [ -n "$DASHBOARD_PID" ]; then
    echo "   PID do dashboard: $DASHBOARD_PID"
    
    # Simular SIGHUP (sinal de fechamento de terminal)
    echo "   Enviando SIGHUP para simular fechamento de terminal..."
    kill -HUP $DASHBOARD_PID 2>/dev/null || echo "   Processo não afetado por SIGHUP (bom sinal!)"
    
    sleep 2
    
    # Verificar se ainda está rodando
    echo ""
    echo "3️⃣ Status após simulação de fechamento:"
    cd /root/finops && ./dashboard_manager.sh status
    
    echo ""
    echo "4️⃣ Teste de conectividade:"
    if curl -s --connect-timeout 3 http://localhost:5000 > /dev/null; then
        echo "   ✅ Dashboard ainda respondendo após simulação de fechamento!"
        echo "   🎉 TESTE PASSOU - Dashboard é independente do terminal"
    else
        echo "   ❌ Dashboard não responde"
        echo "   🚨 TESTE FALHOU"
    fi
else
    echo "   ❌ Dashboard não encontrado"
fi

echo ""
echo "5️⃣ Informações do processo:"
if [ -n "$DASHBOARD_PID" ]; then
    ps aux | grep $DASHBOARD_PID | grep -v grep
    echo "   PPID (Processo Pai):" $(ps -o ppid= -p $DASHBOARD_PID | tr -d ' ')
fi
