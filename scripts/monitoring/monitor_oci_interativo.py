#!/usr/bin/env python3
"""
Monitor interativo para acompanhar o processamento OCI em tempo real
"""

import time
import os
import subprocess
from datetime import datetime

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def run_docker_command(cmd):
    """Executa comando no container Docker"""
    full_cmd = f"docker exec finops-finops_worker_faz-1 {cmd}"
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout
        else:
            error_msg = result.stderr.strip()
            if "is not running" in error_msg or "No such container" in error_msg:
                return "❌ CONTAINER PARADO - Workers Offline!"
            return f"Erro: {error_msg}"
    except subprocess.TimeoutExpired:
        return "Timeout: Comando demorou mais que 30 segundos"
    except Exception as e:
        return f"Erro: {e}"

def check_oci_status():
    """Verifica status atual do OCI"""
    cmd = """python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', port=5432, user='svc_finops', password='<sua-senha-do-banco>', dbname='finopsdatabase')
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT nome, datatime_ultimo_update, datatime_proximo_update, NOW() as agora, jobs_restantes,
                   CASE WHEN datatime_proximo_update <= NOW() THEN 'DEVE PROCESSAR' ELSE 'AGUARDANDO' END as status
            FROM provedor_nuvem WHERE tipo = \'oci\'
        ''')
        result = cursor.fetchone()
        if result:
            nome, ultimo, proximo, agora, jobs, status = result
            print(f'Provedor: {nome}')
            print(f'Último: {ultimo}')
            print(f'Próximo: {proximo}')
            print(f'Status: {status}')
            print(f'Jobs: {jobs}')
        else:
            print('Nenhum provedor OCI encontrado')
    conn.close()
except Exception as e:
    print(f'Erro: {e}')
" """
    return run_docker_command(cmd)

def check_recent_data():
    """Verifica dados processados hoje"""
    cmd = """python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', port=5432, user='svc_finops', password='<sua-senha-do-banco>', dbname='finopsdatabase')
    with conn.cursor() as cursor:
        cursor.execute('''
            SELECT COUNT(*) as total, MAX(data) as ultimo_registro
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 AND data >= CURRENT_DATE
        ''')
        result = cursor.fetchone()
        if result:
            total, ultimo = result
            print(f'Registros hoje: {total:,}')
            print(f'Último registro: {ultimo}')
        else:
            print('Nenhum dado encontrado hoje')
    conn.close()
except Exception as e:
    print(f'Erro: {e}')
" """
    return run_docker_command(cmd)

def check_celery_tasks():
    """Verifica tarefas ativas do Celery"""
    cmd = "celery -A finops_celery.celery inspect active --timeout=10"
    result = run_docker_command(cmd)
    
    if "❌ CONTAINER PARADO" in result:
        return "🔴 WORKERS OFFLINE - Containers Docker parados!"
    elif "finops_celery.tasks.get_oci" in result:
        return "🔄 Processamento OCI ATIVO"
    elif "empty" in result.lower():
        return "⏸️  Nenhuma tarefa ativa - Workers online"
    elif "Error:" in result or "Erro:" in result:
        return f"❌ FALHA CELERY: {result[:50]}..."
    else:
        return f"Status: {result[:100]}..."

def main():
    print("🔍 MONITOR OCI - Pressione Ctrl+C para sair")
    print("="*60)
    
    try:
        while True:
            clear_screen()
            
            print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - MONITOR OCI EM TEMPO REAL")
            print("="*60)
            
            print("\n📊 STATUS DO PROVEDOR:")
            print(check_oci_status())
            
            print("\n📈 DADOS PROCESSADOS HOJE:")
            print(check_recent_data())
            
            print("\n🔄 STATUS CELERY:")
            print(check_celery_tasks())
            
            print("\n" + "="*60)
            print("⏰ Atualizando em 30 segundos... (Ctrl+C para sair)")
            print("💡 Configuração atual: Verificação a cada 15 minutos")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor finalizado. Obrigado!")

if __name__ == "__main__":
    main()
