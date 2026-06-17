#!/bin/bash

DASHBOARD_DIR="/root/finops/dashboard"
PID_FILE="/tmp/finops_dashboard.pid"
LOG_FILE="/tmp/finops_dashboard.log"

case "$1" in
    start)
        echo "🚀 Iniciando Dashboard FinOps..."
        
        # Verificar se já está rodando
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "⚠️  Dashboard já está rodando (PID: $PID)"
                echo "   Acesse: http://$(hostname -I | awk '{print $1}'):5000"
                exit 1
            else
                rm -f "$PID_FILE"
            fi
        fi
        
        # Verificar se o diretório existe
        if [ ! -d "$DASHBOARD_DIR" ]; then
            echo "❌ Erro: Diretório $DASHBOARD_DIR não encontrado!"
            echo "   O dashboard agora faz parte do projeto FinOps principal."
            echo "   Use: cd /root/finops && python3 run_dashboard.py"
            exit 1
        fi
        
        # Instalar dependências se necessário
        if ! python3 -c "import flask" 2>/dev/null; then
            echo "📦 Instalando dependências..."
            pip3 install flask psycopg2-binary pytz
        fi
        
        # Iniciar dashboard
        cd "$DASHBOARD_DIR"
        nohup python3 app.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        sleep 2
        if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "✅ Dashboard iniciado com sucesso!"
            echo "   PID: $(cat $PID_FILE)"
            echo "   URL: http://$(hostname -I | awk '{print $1}'):5000"
            echo "   Logs: $LOG_FILE"
        else
            echo "❌ Erro ao iniciar dashboard"
            cat "$LOG_FILE"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        echo "🛑 Parando Dashboard OCI..."
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "✅ Dashboard parado"
            else
                echo "⚠️  Dashboard não estava rodando"
                rm -f "$PID_FILE"
            fi
        else
            echo "⚠️  Arquivo PID não encontrado"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Dashboard está rodando (PID: $PID)"
                echo "   URL: http://$(hostname -I | awk '{print $1}'):5000"
                echo "   Logs: $LOG_FILE"
            else
                echo "❌ Dashboard não está rodando (arquivo PID órfão)"
                rm -f "$PID_FILE"
            fi
        else
            echo "❌ Dashboard não está rodando"
        fi
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📄 Logs do Dashboard OCI:"
            echo "="*40
            tail -f "$LOG_FILE"
        else
            echo "❌ Arquivo de log não encontrado"
        fi
        ;;
        
    *)
        echo "Dashboard OCI - Sistema de Monitoramento"
        echo "="*40
        echo "Uso: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  start   - Iniciar dashboard"
        echo "  stop    - Parar dashboard"
        echo "  restart - Reiniciar dashboard"
        echo "  status  - Verificar status"
        echo "  logs    - Visualizar logs"
        echo ""
        echo "Exemplo:"
        echo "  $0 start"
        exit 1
        ;;
esac
