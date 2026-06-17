#!/bin/bash

echo "🚀 Iniciando Dashboard FinOps com Autenticação Azure AD"
echo "=============================================="

# Verificar se o ambiente virtual existe
if [ ! -d "../dashboard_env" ]; then
    echo "❌ Ambiente virtual não encontrado"
    echo "💡 Criando ambiente virtual..."
    cd ..
    python3 -m venv dashboard_env
    cd dashboard
fi

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source ../dashboard_env/bin/activate

# Verificar se as dependências estão instaladas
echo "🔍 Verificando dependências..."
python3 -c "
try:
    import flask, msal, flask_session, dotenv, psycopg2
    print('✅ Todas as dependências estão instaladas')
except ImportError as e:
    print(f'❌ Dependência faltando: {e}')
    exit(1)
" || {
    echo "📦 Instalando dependências..."
    pip install Flask Flask-Session msal python-dotenv psycopg2-binary
}

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado"
    echo "💡 Criando arquivo .env com autenticação desabilitada..."
    cat > .env << 'EOF'
# Controle de Autenticação
ENABLE_AZURE_AUTH=false

# Configurações Flask
SECRET_KEY=sua-chave-secreta-muito-segura-aqui
FLASK_ENV=development

# Configurações do Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_USER=svc_finops
DB_PASSWORD=<sua-senha-do-banco>
DB_NAME=finopsdatabase

# Configurações do Azure AD (só necessário se ENABLE_AZURE_AUTH=true)
# AZURE_CLIENT_ID=seu-client-id-aqui
# AZURE_CLIENT_SECRET=seu-client-secret-aqui
# AZURE_TENANT_ID=seu-tenant-id-aqui
EOF
    echo "✅ Arquivo .env criado em modo demonstração"
    echo "� Autenticação Azure AD desabilitada - Acesso direto ao dashboard"
fi

# Executar dashboard
echo "🌐 Iniciando dashboard em http://localhost:5000"
echo "🔐 Autenticação Azure AD ativada"
echo "=============================================="
python3 start_dashboard.py
