#!/usr/bin/env python3
"""
Inicializador do Dashboard FinOps com Autenticação Azure AD
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Configura o ambiente para o dashboard"""
    # Verificar se estamos em um ambiente virtual
    venv_path = Path(__file__).parent.parent / 'dashboard_env'
    
    if venv_path.exists() and not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("⚠️  Ambiente virtual detectado mas não ativado.")
        print("💡 Para ativar o ambiente virtual:")
        print(f"   source {venv_path}/bin/activate")
        print("   python dashboard/start_dashboard.py")
        return False
    
    # Carregar variáveis de ambiente
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print("✅ Arquivo .env carregado com sucesso")
        else:
            print("⚠️  Arquivo .env não encontrado. Usando variáveis do sistema.")
    except ImportError:
        print("⚠️  python-dotenv não instalado. Usando variáveis do sistema.")
    
    # Verificar variáveis obrigatórias do Azure
    enable_azure = os.getenv('ENABLE_AZURE_AUTH', 'false').lower() == 'true'
    
    if enable_azure:
        required_vars = ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Variáveis de ambiente do Azure AD não configuradas:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Para configurar:")
            print("   1. Copie .env.example para .env")
            print("   2. Configure suas credenciais do Azure AD")
            print("   3. Execute novamente")
            return False
        
        print("✅ Variáveis do Azure AD configuradas")
    else:
        print("⚠️  Autenticação Azure AD DESABILITADA")
        print("💡 Para habilitar: defina ENABLE_AZURE_AUTH=true no arquivo .env")
    return True

def main():
    """Função principal"""
    print("🚀 Dashboard FinOps - Inicialização")
    print("=" * 50)
    
    if not setup_environment():
        sys.exit(1)
    
    # Importar e executar a aplicação
    try:
        from app import app
        print("📱 Aplicação carregada com sucesso")
        print("🔐 Autenticação Azure AD ativada")
        print("🌐 URL: http://localhost:5000")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Erro ao importar aplicação: {e}")
        print("💡 Verifique se todas as dependências estão instaladas:")
        print("   source ../dashboard_env/bin/activate")
        print("   pip install Flask Flask-Session msal python-dotenv psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
