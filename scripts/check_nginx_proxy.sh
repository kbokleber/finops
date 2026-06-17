p#!/bin/bash

# Script de verificação do proxy NGINX FinOps
# Data: $(date +"%Y-%m-%d")

echo "=================================="
echo "   VERIFICAÇÃO PROXY NGINX FINOPS"  
echo "=================================="
echo ""

# Verificar se NGINX está rodando
echo "🔍 Status do NGINX:"
systemctl is-active nginx --quiet && echo "✅ NGINX está ATIVO" || echo "❌ NGINX está INATIVO"
echo ""

# Verificar portas
echo "🌐 Portas do NGINX:"
ss -tlnp | grep nginx | while read line; do
    port=$(echo "$line" | awk '{print $4}' | cut -d: -f2)
    echo "   ✅ Porta $port ativa"
done
echo ""

# Testar domínios
echo "🧪 Testando domínios:"

echo "1. devmonitorfinops.service.com.br -> 178.156.185.182:5000"
status1=$(curl -k -s -w "%{http_code}" -H "Host: devmonitorfinops.service.com.br" https://localhost -o /dev/null)
if [ "$status1" = "200" ]; then
    echo "   ✅ Status: $status1 (OK)"
else
    echo "   ❌ Status: $status1 (ERRO)"
fi

echo "2. devfinops.service.com.br -> 178.156.185.182:3001 (Grafana)"
status2=$(curl -k -s -w "%{http_code}" -H "Host: devfinops.service.com.br" https://localhost -o /dev/null)
if [ "$status2" = "200" ] || [ "$status2" = "302" ]; then
    echo "   ✅ Status: $status2 (OK)"
else
    echo "   ❌ Status: $status2 (ERRO)"
fi

echo ""

# Verificar certificados
echo "🔒 Verificando certificados SSL:"
if [ -f "/etc/ssl/finops/service_com_br_full.crt" ]; then
    echo "   ✅ Certificado encontrado"
    expiry=$(openssl x509 -in /etc/ssl/finops/service_com_br_full.crt -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$expiry" ]; then
        echo "   📅 Expira em: $expiry"
    fi
else
    echo "   ❌ Certificado não encontrado"
fi

echo ""

# Verificar logs recentes
echo "📝 Últimos logs de erro (se houver):"
tail -n 5 /var/log/nginx/error.log 2>/dev/null | grep -v "INFO" | head -3 || echo "   ✅ Nenhum erro recente"

echo ""
echo "=================================="
echo "✅ Verificação concluída!"
echo "=================================="