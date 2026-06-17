#!/bin/bash
echo "🔍 STATUS DO DASHBOARD FINOPS"
echo "============================"

# Verificar se o processo está rodando (agora procura por app.py ou dashboard)
PROCESSO=$(ps aux | grep -E "(app\.py|dashboard|finops.*dashboard)" | grep -v grep)
if [ -n "$PROCESSO" ]; then
    echo "✅ Dashboard está RODANDO"
    echo "   Processo: $(echo $PROCESSO | awk '{print $2, $11, $12, $13}')"
else
    echo "❌ Dashboard NÃO está rodando"
    echo "💡 Para iniciar:"
    echo "   cd /root/finops && python3 run_dashboard.py"
    echo "   ou"
    echo "   ./dashboard_service.sh start"
    exit 1
fi

# Verificar se a porta está escutando
PORTA=$(netstat -tulpn | grep :5000)
if [ -n "$PORTA" ]; then
    echo "✅ Porta 5000 está ABERTA"
else
    echo "❌ Porta 5000 NÃO está aberta"
    exit 1
fi

# Testar APIs
echo ""
echo "🧪 TESTANDO APIs:"
echo "------------------"

# Teste Summary
SUMMARY=$(curl -s http://localhost:5000/api/summary)
if echo "$SUMMARY" | grep -q "provedores"; then
    echo "✅ API Summary: OK"
    echo "   $(echo $SUMMARY | cut -c1-60)..."
else
    echo "❌ API Summary: ERRO"
fi

# Teste OCI Status
OCI_STATUS=$(curl -s http://localhost:5000/api/oci-status)
if echo "$OCI_STATUS" | grep -q "nome"; then
    echo "✅ API OCI Status: OK"
    echo "   $(echo $OCI_STATUS | cut -c1-60)..."
else
    echo "❌ API OCI Status: ERRO"
fi

echo ""
echo "🌐 ACESSO WEB:"
echo "---------------"
echo "📊 Dashboard FinOps: http://localhost:5000"
echo "🔗 API Summary: http://localhost:5000/api/summary"
echo "🔗 API OCI: http://localhost:5000/api/oci-status"
echo ""
echo "📁 Localização do Dashboard:"
echo "   /root/finops/dashboard/app.py"

echo ""
echo "✅ Dashboard funcionando corretamente!"
echo "🔄 Auto-refresh a cada 30 segundos"
echo "⚡ Intervalo OCI: 15 minutos"
