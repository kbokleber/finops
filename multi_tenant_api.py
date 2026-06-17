#!/usr/bin/env python3
"""
Multi-Tenant API Gateway com Flask
Gerencia roteamento e autenticação por tenant
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import jwt
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import redis
from multi_tenant_db_manager import MultiTenantDatabaseManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantResolver:
    """
    Resolve o tenant baseado na requisição
    """
    
    def __init__(self, db_manager: MultiTenantDatabaseManager):
        self.db_manager = db_manager
        self.redis_client = redis.Redis(host='localhost', port=6379, db=4)
    
    def resolve_tenant(self, request) -> Optional[Dict]:
        """
        Resolve tenant por diferentes métodos:
        1. Header X-Tenant-ID
        2. Subdomínio
        3. JWT Token
        4. Query parameter
        """
        
        # Método 1: Header explícito
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return self._get_tenant_by_id(tenant_id)
        
        # Método 2: Subdomínio
        host = request.headers.get('Host', '')
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain and subdomain not in ['www', 'api']:
                return self._get_tenant_by_slug(subdomain)
        
        # Método 3: JWT Token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            tenant_info = self._extract_tenant_from_jwt(token)
            if tenant_info:
                return tenant_info
        
        # Método 4: Query parameter
        tenant_slug = request.args.get('tenant')
        if tenant_slug:
            return self._get_tenant_by_slug(tenant_slug)
        
        return None
    
    def _get_tenant_by_id(self, tenant_id: str) -> Optional[Dict]:
        """Busca tenant por ID"""
        return self.db_manager.get_tenant_config(tenant_id)
    
    def _get_tenant_by_slug(self, slug: str) -> Optional[Dict]:
        """Busca tenant por slug"""
        return self.db_manager.get_tenant_config(slug)
    
    def _extract_tenant_from_jwt(self, token: str) -> Optional[Dict]:
        """Extrai tenant do JWT token"""
        try:
            # Decodificar sem verificar assinatura (apenas para extrair dados)
            payload = jwt.decode(token, options={"verify_signature": False})
            tenant_id = payload.get('tenant_id')
            
            if tenant_id:
                return self._get_tenant_by_id(tenant_id)
                
        except Exception as e:
            logger.warning(f"Erro ao decodificar JWT: {e}")
        
        return None

class MultiTenantAPI:
    """
    API Flask multi-tenant
    """
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configurações
        self.app.config['SECRET_KEY'] = 'your-secret-key-here'
        self.app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
        
        # Inicializar componentes
        self.db_manager = MultiTenantDatabaseManager(
            master_db_config={
                'host': 'localhost',
                'port': 5432,
                'user': 'finops_admin',
                'password': 'admin_password',
                'database': 'finops_master'
            },
            redis_config={
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        )
        
        self.tenant_resolver = TenantResolver(self.db_manager)
        
        # Configurar rotas
        self._setup_routes()
        
        # Middleware de tenant
        self.app.before_request(self._resolve_tenant_middleware)
    
    def _setup_routes(self):
        """Configura todas as rotas da API"""
        
        # Rotas de health check
        self.app.route('/health', methods=['GET'])(self.health_check)
        self.app.route('/health/<tenant_id>', methods=['GET'])(self.tenant_health_check)
        
        # Rotas de administração
        self.app.route('/admin/tenants', methods=['GET'])(self.list_tenants)
        self.app.route('/admin/tenants', methods=['POST'])(self.create_tenant)
        self.app.route('/admin/tenants/<tenant_id>', methods=['GET'])(self.get_tenant)
        
        # Rotas de dados (com tenant)
        self.app.route('/api/dashboard/summary', methods=['GET'])(self.get_dashboard_summary)
        self.app.route('/api/costs/daily', methods=['GET'])(self.get_daily_costs)
        self.app.route('/api/providers', methods=['GET'])(self.get_providers)
        self.app.route('/api/providers', methods=['POST'])(self.add_provider)
        
        # Rotas de relatórios
        self.app.route('/api/reports/monthly', methods=['GET'])(self.get_monthly_report)
        self.app.route('/api/reports/custom', methods=['POST'])(self.generate_custom_report)
    
    def _resolve_tenant_middleware(self):
        """
        Middleware que resolve o tenant para cada requisição
        """
        # Pular resolução para rotas administrativas e health check
        if request.path.startswith('/health') or request.path.startswith('/admin'):
            return
        
        tenant_info = self.tenant_resolver.resolve_tenant(request)
        
        if not tenant_info:
            return jsonify({
                'error': 'Tenant não identificado',
                'message': 'Forneça tenant via header X-Tenant-ID, subdomínio ou JWT token'
            }), 400
        
        # Armazenar tenant info no contexto da requisição
        g.tenant = tenant_info
        g.tenant_id = tenant_info['id']
    
    def require_tenant(self, f):
        """Decorator que exige tenant válido"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant'):
                return jsonify({'error': 'Tenant requerido'}), 400
            return f(*args, **kwargs)
        return decorated_function
    
    def require_admin(self, f):
        """Decorator que exige permissões de admin"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar se usuário é admin (implementar lógica de auth)
            auth_header = request.headers.get('Authorization', '')
            if not self._verify_admin_token(auth_header):
                return jsonify({'error': 'Acesso negado'}), 403
            return f(*args, **kwargs)
        return decorated_function
    
    def _verify_admin_token(self, auth_header: str) -> bool:
        """Verifica se token tem permissões de admin"""
        # Implementar verificação de token de admin
        return True  # Placeholder
    
    # === ROTAS DE HEALTH CHECK ===
    
    def health_check(self):
        """Health check geral da API"""
        try:
            # Testar conexão com Redis
            self.tenant_resolver.redis_client.ping()
            
            # Testar conexão com banco master
            with self.db_manager.get_master_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'redis': 'ok',
                    'database': 'ok'
                }
            })
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    def tenant_health_check(self, tenant_id: str):
        """Health check específico de um tenant"""
        try:
            tenant_config = self.db_manager.get_tenant_config(tenant_id)
            if not tenant_config:
                return jsonify({'error': 'Tenant não encontrado'}), 404
            
            # Testar conexão com banco do tenant
            with self.db_manager.get_tenant_connection(tenant_id) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as total FROM provider_configs")
                    provider_count = cursor.fetchone()[0]
            
            return jsonify({
                'tenant_id': tenant_id,
                'status': 'healthy',
                'providers_configured': provider_count,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'tenant_id': tenant_id,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    # === ROTAS ADMINISTRATIVAS ===
    
    @require_admin
    def list_tenants(self):
        """Lista todos os tenants"""
        try:
            with self.db_manager.get_master_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name, slug, database_name, status, created_at
                        FROM tenants
                        ORDER BY created_at DESC
                    """)
                    tenants = cursor.fetchall()
            
            return jsonify({
                'tenants': [dict(tenant) for tenant in tenants],
                'total': len(tenants)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_admin
    def create_tenant(self):
        """Cria novo tenant"""
        try:
            data = request.get_json()
            tenant_name = data.get('name')
            tenant_slug = data.get('slug')
            
            if not tenant_name or not tenant_slug:
                return jsonify({'error': 'Nome e slug são obrigatórios'}), 400
            
            tenant_id = self.db_manager.create_tenant(tenant_name, tenant_slug)
            
            return jsonify({
                'tenant_id': tenant_id,
                'name': tenant_name,
                'slug': tenant_slug,
                'message': 'Tenant criado com sucesso'
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_admin
    def get_tenant(self, tenant_id: str):
        """Busca informações de um tenant"""
        try:
            tenant_config = self.db_manager.get_tenant_config(tenant_id)
            if not tenant_config:
                return jsonify({'error': 'Tenant não encontrado'}), 404
            
            # Buscar estatísticas do tenant
            providers = self.db_manager.get_tenant_providers(tenant_id)
            
            return jsonify({
                'tenant': tenant_config,
                'providers': providers,
                'provider_count': len(providers)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # === ROTAS DE DADOS (COM TENANT) ===
    
    @require_tenant
    def get_dashboard_summary(self):
        """Busca resumo do dashboard para o tenant"""
        try:
            date_from = request.args.get('date_from', 
                (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
            date_to = request.args.get('date_to', 
                datetime.utcnow().strftime('%Y-%m-%d'))
            
            summary = self.db_manager.get_cost_summary(g.tenant_id, date_from, date_to)
            
            return jsonify({
                'tenant_id': g.tenant_id,
                'date_range': {
                    'from': date_from,
                    'to': date_to
                },
                'summary': summary
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_tenant
    def get_daily_costs(self):
        """Busca custos diários do tenant"""
        try:
            days = int(request.args.get('days', 30))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            summary = self.db_manager.get_cost_summary(
                g.tenant_id, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            return jsonify({
                'tenant_id': g.tenant_id,
                'daily_costs': summary,
                'days': days
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_tenant
    def get_providers(self):
        """Lista provedores configurados do tenant"""
        try:
            providers = self.db_manager.get_tenant_providers(g.tenant_id)
            
            return jsonify({
                'tenant_id': g.tenant_id,
                'providers': providers,
                'total': len(providers)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_tenant
    def add_provider(self):
        """Adiciona novo provedor ao tenant"""
        try:
            data = request.get_json()
            
            # Validações básicas
            required_fields = ['provider_type', 'provider_name', 'credentials']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'{field} é obrigatório'}), 400
            
            # Criptografar credenciais
            encrypted_credentials = self._encrypt_credentials(data['credentials'])
            
            # Salvar no banco do tenant
            with self.db_manager.get_tenant_connection(g.tenant_id) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO provider_configs 
                        (provider_type, provider_name, credentials_encrypted, settings)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data['provider_type'],
                        data['provider_name'],
                        encrypted_credentials,
                        json.dumps(data.get('settings', {}))
                    ))
                    provider_id = cursor.fetchone()[0]
            
            return jsonify({
                'provider_id': provider_id,
                'message': 'Provedor adicionado com sucesso'
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _encrypt_credentials(self, credentials: Dict) -> str:
        """Criptografa credenciais do provedor"""
        # Implementar criptografia real
        import base64
        return base64.b64encode(json.dumps(credentials).encode()).decode()
    
    @require_tenant
    def get_monthly_report(self):
        """Gera relatório mensal do tenant"""
        try:
            month = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
            
            # Implementar lógica de relatório mensal
            # ...
            
            return jsonify({
                'tenant_id': g.tenant_id,
                'month': month,
                'report': 'Relatório mensal aqui'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @require_tenant
    def generate_custom_report(self):
        """Gera relatório customizado"""
        try:
            data = request.get_json()
            
            # Implementar lógica de relatório customizado
            # ...
            
            return jsonify({
                'tenant_id': g.tenant_id,
                'custom_report': 'Relatório customizado aqui'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Executa a aplicação"""
        self.app.run(host=host, port=port, debug=debug)

# Factory function
def create_app():
    """Cria e configura a aplicação Flask"""
    api = MultiTenantAPI()
    return api.app

if __name__ == '__main__':
    # Para desenvolvimento
    api = MultiTenantAPI()
    api.run(debug=True)
