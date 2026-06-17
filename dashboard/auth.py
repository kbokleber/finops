#!/usr/bin/env python3
"""
Módulo de autenticação com Azure AD
"""

import msal
import requests
from flask import session, url_for, current_app, request, redirect, jsonify
from functools import wraps

class AzureAuth:
    """Classe para gerenciar autenticação com Azure AD"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa a extensão com a aplicação Flask"""
        self.app = app
        
        # Configurar MSAL
        app.config.setdefault('MSAL_CLIENT_INSTANCE', None)
    
    def _build_msal_app(self, cache=None, authority=None):
        """Constrói uma instância do MSAL confidential client"""
        return msal.ConfidentialClientApplication(
            current_app.config["CLIENT_ID"], 
            authority=authority or current_app.config["AUTHORITY"],
            client_credential=current_app.config["CLIENT_SECRET"], 
            token_cache=cache
        )
    
    def _build_auth_code_flow(self, authority=None, scopes=None):
        """Constrói o fluxo de autorização"""
        return self._build_msal_app(authority=authority).initiate_auth_code_flow(
            scopes or current_app.config["SCOPE"],
            redirect_uri=url_for("auth.authorized", _external=True)
        )
    
    def get_login_url(self):
        """Obtém a URL de login do Azure AD"""
        auth_flow = self._build_auth_code_flow()
        session["flow"] = auth_flow
        return auth_flow["auth_uri"]
    
    def handle_callback(self, request_args):
        """Processa o callback do Azure AD"""
        try:
            cache = self._load_cache()
            result = self._build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
                session.get("flow", {}), 
                request_args
            )
            
            if "error" in result:
                return None, result.get("error_description", "Erro na autenticação")
            
            # Salvar informações do usuário na sessão
            session["user"] = result.get("id_token_claims")
            session["token"] = {
                "access_token": result.get("access_token"),
                "token_type": result.get("token_type", "Bearer")
            }
            
            self._save_cache(cache)
            return result.get("id_token_claims"), None
            
        except Exception as e:
            return None, str(e)
    
    def get_user_info(self):
        """Obtém informações detalhadas do usuário"""
        token = session.get("token")
        if not token:
            return None
        
        try:
            graph_data = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={'Authorization': f'{token["token_type"]} {token["access_token"]}'},
                timeout=30,
            ).json()
            
            return graph_data
        except:
            return session.get("user", {})
    
    def logout(self):
        """Realiza logout do usuário"""
        session.clear()
        
        return (
            f"{current_app.config['AUTHORITY']}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={url_for('dashboard.index', _external=True)}"
        )
    
    def _load_cache(self):
        """Carrega cache de token (para implementação futura)"""
        cache = msal.SerializableTokenCache()
        if session.get("token_cache"):
            cache.deserialize(session["token_cache"])
        return cache
    
    def _save_cache(self, cache):
        """Salva cache de token (para implementação futura)"""
        if cache.has_state_changed:
            session["token_cache"] = cache.serialize()

# Decorador para rotas que requerem autenticação
def login_required(f):
    """Decorador para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se autenticação Azure está desabilitada, simular usuário logado
        if not current_app.config.get('ENABLE_AZURE_AUTH', False):
            if not session.get("user"):
                session["user"] = current_app.config['BYPASS_USER']
            return f(*args, **kwargs)
        
        # Autenticação Azure normal
        if not session.get("user"):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """Decorador alternativo para APIs que retorna JSON"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se autenticação Azure está desabilitada, simular usuário logado
        if not current_app.config.get('ENABLE_AZURE_AUTH', False):
            if not session.get("user"):
                session["user"] = current_app.config['BYPASS_USER']
            return f(*args, **kwargs)
        
        # Autenticação Azure normal
        if not session.get("user"):
            return jsonify({"error": "Acesso não autorizado", "code": 401}), 401
        return f(*args, **kwargs)
    return decorated_function

# Função para verificar se o usuário está autenticado
def is_authenticated():
    """Verifica se o usuário está autenticado"""
    # Se autenticação Azure está desabilitada, sempre considera autenticado
    if not current_app.config.get('ENABLE_AZURE_AUTH', False):
        if not session.get("user"):
            session["user"] = current_app.config['BYPASS_USER']
        return True
    
    # Autenticação Azure normal
    return session.get("user") is not None

# Função para obter o usuário atual
def current_user():
    """Obtém informações do usuário atual"""
    return session.get("user", {})
