#!/usr/bin/env python3
"""
Inicializador do Dashboard FinOps
"""

import os
import sys
import subprocess
from pathlib import Path

def run_dashboard():
    """Executa o dashboard FinOps"""
    # Definir diretório do dashboard
    dashboard_dir = Path(__file__).parent / "dashboard"
    
    if not dashboard_dir.exists():
        print("❌ Erro: Diretório dashboard não encontrado!")
        return False
    
    # Verificar se app.py existe
    app_file = dashboard_dir / "app.py"
    if not app_file.exists():
        print("❌ Erro: Arquivo dashboard/app.py não encontrado!")
        return False
    
    print("🚀 Iniciando Dashboard FinOps...")
    print(f"📁 Diretório: {dashboard_dir}")
    print(f"🌐 URL: http://localhost:5000")
    
    try:
        # Mudar para o diretório do dashboard
        os.chdir(dashboard_dir)
        
        # Executar o dashboard
        subprocess.run([sys.executable, "app.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar dashboard: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Dashboard interrompido pelo usuário")
        return True
    
    return True

if __name__ == "__main__":
    success = run_dashboard()
    if not success:
        sys.exit(1)