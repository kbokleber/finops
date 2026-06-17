#!/usr/bin/env python3
"""
Configurações para autenticação Azure AD

Em producao (Coolify/Docker), as env vars sao injetadas direto pelo Coolify
na UI, entao NAO precisamos carregar .env. O arquivo .env.example no repo
serve apenas como template/documentacao das variaveis.
"""

import os
from datetime import timedelta

# As credenciais DB, SECRET_KEY, etc vem direto das env vars injetadas
# pelo Coolify (ou do .env em dev local). Nao carregamos .env aqui.

class Config:
    """Configurações da aplicação"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-muito-segura-aqui')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True  # Manter sessão ativa
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'finops_'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = True  # Renovar sessão a cada requisição
    
    # Configurações de Cookie para HTTPS com Nginx
    # SESSION_COOKIE_SECURE precisa ser False porque o Flask vê HTTP do proxy,
    # mesmo que o nginx termine o SSL. O nginx garante a segurança.
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True  # Prevenir acesso via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Permitir cookies em navegação normal
    SESSION_COOKIE_PATH = '/'  # Cookie válido para todo o site
    SESSION_COOKIE_DOMAIN = None  # Deixar None para usar o domínio da requisição automaticamente
    
    # Forçar HTTPS para URLs externas e configuração dinâmica de domínio
    PREFERRED_URL_SCHEME = 'https'
    
    # SERVER_NAME NÃO deve ser definido em produção com proxy reverso
    # Isso causa problemas com cookies e redirecionamentos
    SERVER_NAME = None  # Removido para compatibilidade com nginx
    APPLICATION_ROOT = '/'
    
    # Ambiente Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Controle de autenticação - NOVO!
    ENABLE_AZURE_AUTH = os.getenv('ENABLE_AZURE_AUTH', 'false').lower() == 'true'
    
    # Azure AD (só usado se ENABLE_AZURE_AUTH=true)
    CLIENT_ID = os.getenv('AZURE_CLIENT_ID', '')
    CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET', '')
    TENANT_ID = os.getenv('AZURE_TENANT_ID', '')
    
    # URLs de redirecionamento
    REDIRECT_PATH = "/auth/callback"
    
    # Scopes do Azure AD
    SCOPE = ["User.ReadBasic.All"]
    
    # Authority URL
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    
    # Usuário fictício para modo bypass - NOVO!
    BYPASS_USER = {
        'name': 'Usuário Demo',
        'email': 'demo@empresa.com',
        'id': 'demo-user-id',
        'jobTitle': 'Administrador FinOps',
        'department': 'TI'
    }
    
    # Configuração do banco
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'svc_finops'),
        'password': os.getenv('DB_PASSWORD', ''),
        'dbname': os.getenv('DB_NAME', 'finopsdatabase')
    }

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    TESTING = False

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
