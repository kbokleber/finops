#!/bin/bash
"""
Script para verificar e instalar dependências
"""

echo "🔍 Verificando dependências do Dashboard FinOps..."

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale o Python 3.8 ou superior."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Verificar se pip está instalado
if ! command -v pip &> /dev/null; then
    echo "❌ pip não encontrado. Instalando pip..."
    python3 -m ensurepip --default-pip
fi

echo "✅ pip encontrado"

# Instalar dependências específicas para autenticação
echo "📦 Instalando dependências para autenticação Azure AD..."

pip install Flask-Session==0.8.0
pip install msal==1.29.0
pip install python-dotenv==1.0.1

echo "✅ Dependências de autenticação instaladas"

# Verificar se as dependências principais existem
echo "🔍 Verificando dependências principais..."

python3 -c "
import sys
modules = ['flask', 'msal', 'flask_session', 'dotenv', 'psycopg2']
missing = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        missing.append(module)
        print(f'❌ {module}')

if missing:
    print(f'\n❌ Módulos faltando: {missing}')
    print('Execute: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('\n✅ Todas as dependências estão instaladas!')
"

echo "🎉 Verificação concluída!"
echo "💡 Para iniciar o dashboard:"
echo "   cd /root/finops/dashboard"
echo "   python start_dashboard.py"
