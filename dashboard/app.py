#!/usr/bin/env python3
"""
Dashboard FinOps - Versão com Autenticação Azure AD
"""

import os
from flask import Flask, render_template, jsonify, redirect, url_for, session, Blueprint, request
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz

# Importar módulos de autenticação
from config import config
from auth import AzureAuth, login_required, require_auth, is_authenticated, current_user
from routes.auth_routes import auth_bp

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Configurar ProxyFix para lidar com headers do nginx
    # x_proto=1: Confia no header X-Forwarded-Proto (importante para HTTPS)
    # x_host=1: Confia no header X-Forwarded-Host
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1, x_port=1)
    
    # Inicializar extensões
    Session(app)
    azure_auth = AzureAuth(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    
    # Context processors para templates
    @app.context_processor
    def inject_auth():
        return {
            'is_authenticated': is_authenticated(),
            'current_user': current_user()
        }
    
    return app

# Criar aplicação
app = create_app()

def convert_to_brasilia(dt):
    """Converte datetime UTC para horário de Brasília"""
    if dt is None:
        return 'N/A'
    
    utc = pytz.UTC
    brasilia = pytz.timezone('America/Sao_Paulo')
    
    # Se o datetime não tem timezone, assume UTC
    if dt.tzinfo is None:
        dt = utc.localize(dt)
    
    # Converte para horário de Brasília
    dt_brasilia = dt.astimezone(brasilia)
    return dt_brasilia.strftime('%d/%m/%Y %H:%M:%S')

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(**app.config['DB_CONFIG'])
        return conn
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

# Middleware para verificar autenticação
@app.before_request
def require_authentication():
    """Middleware para verificar autenticação em todas as rotas"""
    from flask import request
    
    # Se autenticação Azure está desabilitada, pular verificação
    if not app.config.get('ENABLE_AZURE_AUTH', False):
        return
    
    # Rotas públicas que não requerem autenticação
    public_routes = [
        'auth.login', 
        'auth.microsoft_login', 
        'auth.authorized', 
        'auth.check',
        'static'
    ]
    
    # Verificar se a rota atual é pública
    if request.endpoint in public_routes:
        return
    
    # Se não está autenticado, redirecionar para login
    if not is_authenticated():
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": "Acesso não autorizado", "code": 401}), 401
        return redirect(url_for('auth.login'))

@app.route('/')
@login_required  
def dashboard():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

# Registrar blueprint do dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

app.register_blueprint(dashboard_bp)

@app.route('/api/summary')
@require_auth
def api_summary():
    """API para resumo dos cards do topo"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'})
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Provedores configurados
            cursor.execute("SELECT COUNT(*) as total FROM provedor_nuvem WHERE tipo = 'oci'")
            provedores = cursor.fetchone()['total']
            
            # Jobs restantes
            cursor.execute("SELECT COALESCE(SUM(jobs_restantes), 0) as total FROM provedor_nuvem WHERE tipo = 'oci'")
            jobs = cursor.fetchone()['total']
            
            # Registros hoje (dia mais recente com dados) - CORRIGIDO: removido filtro cloudproviderid
            cursor.execute("""
                SELECT COUNT(*) as total FROM utilizacao_recurso 
                WHERE data = (
                    SELECT MAX(data) FROM utilizacao_recurso
                )
            """)
            registros = cursor.fetchone()['total']
            
            # Custo hoje (dia mais recente com dados) - CORRIGIDO: removido filtro cloudproviderid
            cursor.execute("""
                SELECT COALESCE(SUM(custo_total), 0) as total FROM utilizacao_recurso 
                WHERE data = (
                    SELECT MAX(data) FROM utilizacao_recurso
                )
            """)
            custo = cursor.fetchone()['total']
            
        conn.close()
        
        return jsonify({
            'provedores': provedores,
            'jobs_restantes': jobs,
            'registros_hoje': registros,
            'custo_hoje': float(custo)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'})

@app.route('/api/oci-status')
@require_auth
def api_oci_status():
    """API para status dos provedores OCI"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'})
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT nome, datatime_ultimo_update, datatime_proximo_update, 
                       jobs_restantes, NOW() as agora,
                       CASE WHEN datatime_proximo_update <= NOW() THEN 'DEVE PROCESSAR' ELSE 'AGUARDANDO' END as status
                FROM provedor_nuvem WHERE tipo = 'oci'
            """)
            result = cursor.fetchone()
            
        conn.close()
        
        if result:
            return jsonify({
                'nome': result['nome'],
                'ultimo_update': result['datatime_ultimo_update'].strftime('%Y-%m-%d %H:%M:%S') if result['datatime_ultimo_update'] else 'N/A',
                'proximo_update': result['datatime_proximo_update'].strftime('%Y-%m-%d %H:%M:%S') if result['datatime_proximo_update'] else 'N/A',
                'status': result['status'],
                'jobs_restantes': result['jobs_restantes'] or 0,
                'intervalo': '15 minutos'
            })
        else:
            return jsonify({'error': 'Nenhum provedor OCI encontrado'})
            
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'})

@app.route('/api/recent-data')
@require_auth
def api_recent_data():
    """API para dados processados recentemente"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Erro de conexão com banco'})
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Dados dos últimos 7 dias - CORRIGIDO: removido filtro cloudproviderid
            cursor.execute("""
                SELECT data as dia, COUNT(*) as registros, 
                       SUM(custo_total) as custo_total
                FROM utilizacao_recurso 
                WHERE data >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY data ORDER BY data DESC
                LIMIT 7
            """)
            dados_dias = cursor.fetchall()
            
        conn.close()
        
        return jsonify({
            'dados_dias': [dict(row) for row in dados_dias]
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'})

@app.route('/api/celery-status')
@require_auth
def api_celery_status():
    """API para status do Celery"""
    try:
        import subprocess
        
        # Verificar se containers estão rodando
        try:
            cmd = "docker exec finops-finops_worker_verifica-1 celery -A finops_celery inspect stats --timeout=10"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "is not running" in error_msg or "No such container" in error_msg:
                    return jsonify({
                        'active_tasks': 0,
                        'scheduled_tasks': 0,
                        'workers_online': 0,
                        'status': 'WORKERS OFFLINE - Containers parados',
                        'last_check': convert_to_brasilia(datetime.utcnow()),
                        'error': 'Containers Docker não estão rodando'
                    })
                else:
                    return jsonify({
                        'active_tasks': 0,
                        'scheduled_tasks': 0,
                        'workers_online': 0,
                        'status': 'ERRO CELERY',
                        'last_check': convert_to_brasilia(datetime.utcnow()),
                        'error': f'Erro ao conectar: {error_msg}'
                    })
            
            # Analisar resultado do Celery
            output = result.stdout
            
            # Contar workers online (cada worker aparece como "->  worker_name@container: OK")
            workers_online = output.count("OK")
            
            # Verificar tarefas ativas
            cmd_active = "docker exec finops-finops_worker_verifica-1 celery -A finops_celery inspect active --timeout=10"
            result_active = subprocess.run(cmd_active, shell=True, capture_output=True, text=True, timeout=15)
            
            active_tasks = 0
            if result_active.returncode == 0:
                active_output = result_active.stdout.lower()
                if "finops_celery.tasks.get_oci" in active_output:
                    active_tasks = 1
            
            # Determinar status
            if workers_online == 0:
                status = "WORKERS OFFLINE"
            elif active_tasks > 0:
                status = "Processamento ATIVO"
            else:
                status = f"{workers_online} Workers Online - Aguardando tarefas"
            
            return jsonify({
                'active_tasks': active_tasks,
                'scheduled_tasks': 0,
                'workers_online': workers_online,
                'status': status,
                'last_check': convert_to_brasilia(datetime.utcnow())
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'active_tasks': 0,
                'scheduled_tasks': 0,
                'workers_online': 0,
                'status': 'TIMEOUT - Workers não respondem',
                'last_check': convert_to_brasilia(datetime.utcnow()),
                'error': 'Timeout ao verificar workers'
            })
            
    except Exception as e:
        return jsonify({
            'active_tasks': 0,
            'scheduled_tasks': 0,
            'workers_online': 0,
            'status': 'ERRO SISTEMA',
            'last_check': convert_to_brasilia(datetime.utcnow()),
            'error': f'Erro: {str(e)}'
        })

@app.route('/api/docker-containers')
@require_auth
def api_docker_containers():
    """API para listar containers Docker"""
    try:
        import subprocess
        
        # Usar formato mais completo com created, status, ports e ID
        cmd = "docker ps -a --format '{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.CreatedAt}}|{{.Ports}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            # Se falhou, tentar comando alternativo
            cmd_alt = "docker ps -a"
            result_alt = subprocess.run(cmd_alt, shell=True, capture_output=True, text=True, timeout=10)
            if result_alt.returncode == 0:
                # Parse manual do output padrão
                lines = result_alt.stdout.strip().split('\n')[1:]  # Pular header
                containers = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            # Extrair informações básicas
                            container_id = parts[0] if len(parts) > 0 else "N/A"
                            name = parts[-1]
                            image = parts[1]
                            status = " ".join(parts[4:-1]) if len(parts) > 5 else "Unknown"
                            containers.append({
                                'id': container_id,
                                'name': name,
                                'image': image,
                                'status': status,
                                'created': 'N/A',
                                'ports': 'N/A'
                            })
                return jsonify(containers)
            return jsonify([])
        
        # Parse do formato personalizado
        lines = result.stdout.strip().split('\n')
        containers = []
        
        for line in lines:
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 6:
                    containers.append({
                        'id': parts[0].strip(),
                        'name': parts[1].strip(),
                        'image': parts[2].strip(),
                        'status': parts[3].strip(),
                        'created': parts[4].strip(),
                        'ports': parts[5].strip() if parts[5].strip() else 'Nenhuma'
                    })
                elif len(parts) >= 3:
                    # Fallback para formato antigo
                    containers.append({
                        'id': 'N/A',
                        'name': parts[0].strip(),
                        'image': parts[1].strip(),
                        'status': parts[2].strip(),
                        'created': 'N/A',
                        'ports': 'N/A'
                    })
        
        return jsonify(containers)
        
    except Exception as e:
        # Fallback: tentar listar containers de forma mais básica
        try:
            cmd_basic = "docker ps --format '{{.ID}}|{{.Names}}'"
            result_basic = subprocess.run(cmd_basic, shell=True, capture_output=True, text=True, timeout=5)
            if result_basic.returncode == 0:
                lines = result_basic.stdout.strip().split('\n')
                containers = []
                for line in lines:
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 2:
                            containers.append({
                                'id': parts[0].strip(),
                                'name': parts[1].strip(),
                                'image': 'N/A',
                                'status': 'Running',
                                'created': 'N/A',
                                'ports': 'N/A'
                            })
                        else:
                            containers.append({
                                'id': 'N/A',
                                'name': line.strip(),
                                'image': 'N/A',
                                'status': 'Running',
                                'created': 'N/A',
                                'ports': 'N/A'
                            })
                return jsonify(containers)
        except:
            pass
        
        return jsonify([])

@app.route('/api/docker-logs/<container_name>')
@require_auth
def api_docker_logs(container_name):
    """API para obter logs de um container específico"""
    try:
        import subprocess
        
        # Obter logs do container
        cmd = f"docker logs --tail=100 {container_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        
        logs = result.stdout if result.returncode == 0 else "Erro ao obter logs"
        errors = result.stderr if result.stderr else None
        
        return jsonify({
            'container': container_name,
            'logs': logs,
            'errors': errors,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'container': container_name,
            'logs': f"Erro: {str(e)}",
            'errors': None,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/control-tables')
@require_auth
def api_control_tables():
    """API para informações das tabelas de controle"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify([])
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Obter informações das principais tabelas
            tables = [
                'provedor_nuvem',
                'utilizacao_recurso',
                'controle_processamento',
                'recurso'
            ]
            
            result = []
            for table in tables:
                try:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    
                    # Obter informações da tabela
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                    """)
                    columns = cursor.fetchall()
                    
                    result.append({
                        'table_name': table,
                        'registros': count,
                        'colunas': len(columns)
                    })
                    
                except Exception as e:
                    result.append({
                        'table_name': table,
                        'registros': 0,
                        'colunas': 0
                    })
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify([])

# Adicionar middleware de erro para autenticação
@app.errorhandler(401)
def unauthorized(error):
    """Handler para erros de autenticação"""
    if request.is_json:
        return jsonify({"error": "Acesso não autorizado", "code": 401}), 401
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard FinOps com Autenticação Azure AD...")
    print("🔐 Certifique-se de configurar as variáveis de ambiente:")
    print("   - AZURE_CLIENT_ID")
    print("   - AZURE_CLIENT_SECRET") 
    print("   - AZURE_TENANT_ID")
    print("🌐 Acesse: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
