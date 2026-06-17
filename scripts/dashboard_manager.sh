#!/bin/bash
# Dashboard Manager - Gerenciador completo do dashboard FinOps

DASHBOARD_DIR="/root/finops"
LOG_FILE="/root/finops/logs/dashboard.log"
PID_FILE="/root/finops/logs/dashboard.pid"

case "$1" in
    status)
        echo "🔍 STATUS DO DASHBOARD FINOPS"
        echo "=============================="
        
        # Verificar processo
        DASHBOARD_PID=$(pgrep -f "run_dashboard\.py" | head -1)
        FLASK_PID=$(pgrep -f "app\.py" | head -1)
        PORT_ACTIVE=$(netstat -tulpn | grep :5000)
        
        # Determinar qual processo está realmente ativo
        ACTIVE_PID=""
        PROCESS_TYPE=""
        
        if [ -n "$DASHBOARD_PID" ]; then
            ACTIVE_PID=$DASHBOARD_PID
            PROCESS_TYPE="run_dashboard.py"
        elif [ -n "$FLASK_PID" ] && [ -n "$PORT_ACTIVE" ]; then
            ACTIVE_PID=$FLASK_PID
            PROCESS_TYPE="app.py"
        fi
        
        if [ -n "$ACTIVE_PID" ] && [ -n "$PORT_ACTIVE" ]; then
            PROCESS=$(ps aux | grep $ACTIVE_PID | grep -v grep | awk '{print $11, $12}')
            echo "✅ Dashboard RODANDO"
            echo "   PID: $ACTIVE_PID"
            echo "   Processo: $PROCESS_TYPE"
            echo "   Comando: $PROCESS"
            echo "   🌐 URL: http://localhost:5000"
            
            # Verificar porta
            if netstat -tulpn | grep :5000 > /dev/null; then
                echo "   ✅ Porta 5000 ativa"
            else
                echo "   ⚠️  Porta 5000 não encontrada"
            fi
            
            # Teste de conectividade
            if curl -s --connect-timeout 3 http://localhost:5000 > /dev/null; then
                echo "   ✅ Dashboard respondendo"
            else
                echo "   ❌ Dashboard não responde"
            fi
        else
            echo "❌ Dashboard NÃO está rodando"
            echo "   Para iniciar: $0 start"
        fi
        ;;
        
    stop)
        echo "🛑 Parando Dashboard FinOps..."
        
        # Detectar todos os processos relacionados ao dashboard
        DASHBOARD_PID=$(pgrep -f "run_dashboard\.py" | head -1)
        FLASK_PID=$(pgrep -f "app\.py" | head -1)
        PORT_PID=$(netstat -tulpn | grep :5000 | awk '{print $7}' | cut -d'/' -f1)
        
        # Lista de PIDs para parar
        PIDS_TO_STOP=""
        
        if [ -n "$DASHBOARD_PID" ]; then
            PIDS_TO_STOP="$PIDS_TO_STOP $DASHBOARD_PID"
            echo "   Encontrado processo run_dashboard.py: $DASHBOARD_PID"
        fi
        
        if [ -n "$FLASK_PID" ]; then
            PIDS_TO_STOP="$PIDS_TO_STOP $FLASK_PID"
            echo "   Encontrado processo app.py: $FLASK_PID"
        fi
        
        if [ -n "$PORT_PID" ] && [ "$PORT_PID" != "$DASHBOARD_PID" ] && [ "$PORT_PID" != "$FLASK_PID" ]; then
            PIDS_TO_STOP="$PIDS_TO_STOP $PORT_PID"
            echo "   Encontrado processo na porta 5000: $PORT_PID"
        fi
        
        if [ -n "$PIDS_TO_STOP" ]; then
            for PID in $PIDS_TO_STOP; do
                if ps -p $PID > /dev/null 2>&1; then
                    echo "   Parando processo PID: $PID"
                    kill $PID
                fi
            done
            
            # Aguardar processos pararem
            sleep 2
            
            # Verificar se ainda estão rodando e forçar se necessário
            for PID in $PIDS_TO_STOP; do
                if ps -p $PID > /dev/null 2>&1; then
                    echo "   ⚠️ Forçando parada do PID: $PID"
                    kill -9 $PID
                fi
            done
            
            sleep 1
            
            # Verificar se realmente pararam
            STILL_RUNNING=""
            for PID in $PIDS_TO_STOP; do
                if ps -p $PID > /dev/null 2>&1; then
                    STILL_RUNNING="$STILL_RUNNING $PID"
                fi
            done
            
            if [ -n "$STILL_RUNNING" ]; then
                echo "   ❌ Não foi possível parar os processos: $STILL_RUNNING"
            else
                echo "   ✅ Dashboard parado completamente"
            fi
            
            rm -f "$PID_FILE"
        else
            echo "   ⚠️ Nenhum dashboard estava rodando"
        fi
        ;;
        
    start)
        echo "🚀 Iniciando Dashboard FinOps..."
        
        # Verificar se já está rodando (verificar ambos os tipos de processo)
        DASHBOARD_PID=$(pgrep -f "run_dashboard\.py" | head -1)
        FLASK_PID=$(pgrep -f "app\.py" | head -1)
        PORT_ACTIVE=$(netstat -tulpn | grep :5000)
        
        if ([ -n "$DASHBOARD_PID" ] || [ -n "$FLASK_PID" ]) && [ -n "$PORT_ACTIVE" ]; then
            ACTIVE_PID=${DASHBOARD_PID:-$FLASK_PID}
            echo "   ⚠️ Dashboard já está rodando (PID: $ACTIVE_PID)"
            echo "   Use: $0 status para verificar"
            exit 1
        fi
        
        # Verificar diretório
        if [ ! -d "$DASHBOARD_DIR" ]; then
            echo "   ❌ Diretório $DASHBOARD_DIR não encontrado"
            exit 1
        fi
        
        # Iniciar dashboard
        cd "$DASHBOARD_DIR"
        echo "   📁 Diretório: $DASHBOARD_DIR"
        echo "   📄 Log: $LOG_FILE"
        
        # Método 1: Usando setsid para completa independência do terminal
        setsid bash -c "cd '$DASHBOARD_DIR' && python3 run_dashboard.py < /dev/null > '$LOG_FILE' 2>&1 &"
        sleep 1
        
        # Capturar PID do processo Python
        NEW_PID=$(pgrep -f "run_dashboard\.py" | head -1)
        if [ -n "$NEW_PID" ]; then
            echo $NEW_PID > "$PID_FILE"
        fi
        
        # Verificar se iniciou
        sleep 3
        NEW_DASHBOARD_PID=$(pgrep -f "run_dashboard\.py" | head -1)
        if [ -n "$NEW_DASHBOARD_PID" ] && netstat -tulpn | grep :5000 > /dev/null; then
            echo "   ✅ Dashboard iniciado com sucesso!"
            echo "   🆔 PID: $NEW_DASHBOARD_PID"
            echo "   🌐 URL: http://localhost:5000"
            echo "   📋 Logs: tail -f $LOG_FILE"
        else
            echo "   ❌ Erro ao iniciar dashboard"
            echo "   📋 Verificar logs: cat $LOG_FILE"
            rm -f "$PID_FILE"
        fi
        ;;
        
    restart)
        echo "🔄 Reiniciando Dashboard FinOps..."
        $0 stop
        sleep 3
        $0 start
        ;;
        
    logs|log)
        echo "📋 LOGS DO DASHBOARD (Ctrl+C para sair)"
        echo "========================================"
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ Arquivo de log não encontrado: $LOG_FILE"
            echo "   Dashboard pode não ter sido iniciado ainda"
        fi
        ;;
        
    test)
        echo "🧪 TESTANDO DASHBOARD"
        echo "===================="
        
        echo "📡 Teste de conectividade..."
        if curl -s --connect-timeout 5 http://localhost:5000 > /dev/null; then
            echo "   ✅ Dashboard respondendo"
        else
            echo "   ❌ Dashboard não responde"
        fi
        
        echo "🔌 Teste API Summary..."
        RESPONSE=$(curl -s --connect-timeout 5 http://localhost:5000/api/summary)
        if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
            echo "   ✅ API funcionando"
        else
            echo "   ❌ API não responde"
        fi
        
        echo "⚡ Teste de performance..."
        time curl -s http://localhost:5000 > /dev/null 2>&1 && echo "   ✅ Resposta rápida" || echo "   ⚠️ Resposta lenta"
        ;;
        
    install-service)
        echo "⚙️ Instalando serviço systemd..."
        
        # Copiar arquivo de serviço
        cp /root/finops/finops-dashboard.service /etc/systemd/system/
        
        # Recarregar systemd
        systemctl daemon-reload
        
        # Habilitar o serviço
        systemctl enable finops-dashboard.service
        
        echo "   ✅ Serviço instalado e habilitado"
        echo "   📋 Para usar: sudo systemctl {start|stop|status} finops-dashboard"
        ;;
        
    service-start)
        echo "🚀 Iniciando serviço systemd..."
        systemctl start finops-dashboard.service
        sleep 2
        systemctl status finops-dashboard.service --no-pager
        ;;
        
    service-stop)
        echo "🛑 Parando serviço systemd..."
        systemctl stop finops-dashboard.service
        systemctl status finops-dashboard.service --no-pager
        ;;
        
    service-status)
        echo "📊 Status do serviço systemd..."
        systemctl status finops-dashboard.service --no-pager
        ;;
        
    cleanup)
        echo "🧹 LIMPEZA FORÇADA - Parando todos os processos relacionados..."
        
        # Matar todos os processos relacionados
        echo "   🔍 Procurando processos Python relacionados ao dashboard..."
        pkill -f "run_dashboard" 2>/dev/null && echo "   ✅ Processos run_dashboard finalizados"
        pkill -f "app\.py" 2>/dev/null && echo "   ✅ Processos app.py finalizados"
        
        # Liberar porta 5000 se estiver ocupada
        echo "   🔍 Verificando porta 5000..."
        PORT_PID=$(netstat -tulpn | grep :5000 | awk '{print $7}' | cut -d'/' -f1 2>/dev/null)
        if [ -n "$PORT_PID" ]; then
            echo "   🔧 Liberando porta 5000 (PID: $PORT_PID)..."
            kill -9 $PORT_PID 2>/dev/null
            sleep 1
        fi
        
        # Remover arquivos de controle
        rm -f "$PID_FILE" 2>/dev/null
        
        # Verificar resultado
        if netstat -tulpn | grep :5000 > /dev/null; then
            echo "   ❌ Porta 5000 ainda ocupada"
        else
            echo "   ✅ Porta 5000 liberada"
        fi
        
        echo "   🎯 Limpeza concluída. Agora você pode usar: $0 start"
        ;;
        
    *)
        echo "📊 DASHBOARD MANAGER - FinOps"
        echo "============================="
        echo ""
        echo "Uso: $0 {comando}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  📊 status          - Verificar se dashboard está rodando"
        echo "  🚀 start           - Iniciar dashboard em background"
        echo "  🛑 stop            - Parar dashboard"
        echo "  🔄 restart         - Reiniciar dashboard"
        echo "  📋 logs (ou log)   - Ver logs em tempo real"
        echo "  🧪 test            - Testar conectividade e APIs"
        echo "  🧹 cleanup         - Limpeza forçada (resolve problemas)"
        echo ""
        echo "Comandos de serviço (recomendado):"
        echo "  ⚙️ install-service  - Instalar como serviço systemd"
        echo "  🚀 service-start    - Iniciar via systemd"
        echo "  🛑 service-stop     - Parar via systemd"
        echo "  📊 service-status   - Status do serviço systemd"
        echo ""
        echo "Exemplos:"
        echo "  $0 install-service  # Primeiro uso - instalar serviço"
        echo "  $0 service-start    # Iniciar dashboard persistente"
        echo "  $0 service-status   # Verificar status"
        echo ""
        echo "🌐 URL do Dashboard: http://localhost:5000"
        echo "📁 Localização: $DASHBOARD_DIR"
        ;;
esac
