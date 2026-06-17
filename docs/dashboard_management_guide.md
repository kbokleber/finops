# 📊 Comandos de Gerenciamento do Dashboard FinOps

## 🔍 **1. VERIFICAR STATUS**

### Opção 1: Script de verificação automática
```bash
/root/scripts/check_dashboard.sh
```

### Opção 2: Verificação manual
```bash
# Verificar processo rodando
ps aux | grep -E "(app\.py|dashboard)" | grep -v grep

# Verificar porta 5000
netstat -tulpn | grep :5000

# Verificar se responde
curl -s http://localhost:5000 | head -c 50
```

### Opção 3: Verificação completa
```bash
# Status detalhado
systemctl --user status dashboard 2>/dev/null || echo "Não há serviço systemd"
pgrep -f "dashboard\|app\.py" && echo "✅ Dashboard rodando" || echo "❌ Dashboard parado"
```

## 🛑 **2. PARAR DASHBOARD**

### Opção 1: Via script de serviço
```bash
/root/scripts/dashboard_service.sh stop
```

### Opção 2: Parar por PID
```bash
# Encontrar PID
PID=$(pgrep -f "dashboard\|app\.py")
echo "PID encontrado: $PID"

# Parar processo
kill $PID

# Forçar parada (se necessário)
kill -9 $PID
```

### Opção 3: Parar todos os dashboards
```bash
# Parar todos os processos relacionados
pkill -f "dashboard"
pkill -f "app\.py.*5000"
```

## 🚀 **3. INICIAR DASHBOARD**

### Opção 1: Sistema completo (Recomendado)
```bash
cd /root/finops
./start_finops.sh
```

### Opção 2: Apenas dashboard integrado
```bash
cd /root/finops
python3 run_dashboard.py
```

### Opção 3: Dashboard em background
```bash
cd /root/finops
nohup python3 run_dashboard.py > dashboard.log 2>&1 &
echo $! > dashboard.pid
```

### Opção 4: Via script de compatibilidade
```bash
/root/scripts/dashboard_service.sh start
```

### Opção 5: Dashboard direto
```bash
cd /root/finops/dashboard
python3 app.py
```

## 🔄 **4. REINICIAR DASHBOARD**

### Reinício completo
```bash
# Parar
/root/scripts/dashboard_service.sh stop

# Aguardar
sleep 2

# Iniciar
cd /root/finops && python3 run_dashboard.py
```

### Reinício rápido via script
```bash
/root/scripts/dashboard_service.sh restart
```

## 📋 **5. COMANDOS ÚTEIS DE MONITORAMENTO**

### Ver logs em tempo real
```bash
# Se rodando em background
tail -f /root/finops/dashboard.log

# Logs do sistema
journalctl -f | grep dashboard
```

### Verificar performance
```bash
# CPU e memória do processo
top -p $(pgrep -f dashboard)

# Conexões ativas
ss -tulpn | grep :5000
```

### Testar conectividade
```bash
# Teste básico
curl http://localhost:5000

# Teste API
curl http://localhost:5000/api/summary

# Teste com tempo
time curl -s http://localhost:5000 > /dev/null
```

## 🎛️ **6. SCRIPT COMPLETO DE GERENCIAMENTO**

Vou criar um script personalizado para você:

```bash
#!/bin/bash
# dashboard_manager.sh - Gerenciador completo do dashboard

case "$1" in
    status)
        echo "🔍 STATUS DO DASHBOARD"
        if pgrep -f "dashboard\|app\.py" > /dev/null; then
            PID=$(pgrep -f "dashboard\|app\.py")
            echo "✅ Dashboard RODANDO (PID: $PID)"
            echo "🌐 URL: http://localhost:5000"
            netstat -tulpn | grep :5000
        else
            echo "❌ Dashboard NÃO está rodando"
        fi
        ;;
    stop)
        echo "🛑 Parando dashboard..."
        pkill -f "dashboard\|app\.py" && echo "✅ Dashboard parado" || echo "⚠️ Nenhum processo encontrado"
        ;;
    start)
        echo "🚀 Iniciando dashboard..."
        cd /root/finops
        nohup python3 run_dashboard.py > dashboard.log 2>&1 &
        echo "✅ Dashboard iniciado em background"
        echo "🌐 Acesse: http://localhost:5000"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    logs)
        echo "📋 Logs do dashboard:"
        tail -f /root/finops/dashboard.log 2>/dev/null || echo "❌ Arquivo de log não encontrado"
        ;;
    *)
        echo "📊 Gerenciador do Dashboard FinOps"
        echo "Uso: $0 {status|start|stop|restart|logs}"
        echo ""
        echo "Comandos:"
        echo "  status   - Verificar se está rodando"
        echo "  start    - Iniciar dashboard"
        echo "  stop     - Parar dashboard"
        echo "  restart  - Reiniciar dashboard"
        echo "  logs     - Ver logs em tempo real"
        ;;
esac
```

## 🔧 **7. SITUAÇÃO ATUAL**

Pelo que vi, você tem um dashboard antigo rodando:
- **PID**: 2063388
- **Processo**: `python3 dashboard_simple.py`
- **Porta**: 5000

### Para migrar para nova estrutura:
```bash
# 1. Parar o antigo
kill 2063388

# 2. Iniciar o novo
cd /root/finops
python3 run_dashboard.py
```

Quer que eu crie esse script gerenciador personalizado para você? 🤔
