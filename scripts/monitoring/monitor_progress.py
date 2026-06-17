#!/usr/bin/env python3
"""
Monitor de progresso do reprocessamento OCI
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time

def monitor_progress():
    """Monitora progresso do reprocessamento"""
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'svc_finops',
        'password': '<sua-senha-do-banco>',
        'dbname': 'finopsdatabase'
    }
    
    prd_expected = {
        '2025-07-22': 7168,
        '2025-07-23': 5671
    }
    
    print("🔍 MONITOR DE PROGRESSO - REPROCESSAMENTO OCI")
    print("=" * 60)
    print("Pressione Ctrl+C para parar o monitoramento")
    print()
    
    try:
        while True:
            try:
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Verificar dados atuais
                cursor.execute("""
                    SELECT 
                        data::date as data,
                        COUNT(*) as registros_atual
                    FROM utilizacao_recurso 
                    WHERE cloudproviderid = 3 
                    AND data >= '2025-07-22'
                    GROUP BY data::date
                    ORDER BY data::date;
                """)
                
                current_data = cursor.fetchall()
                
                # Verificar se há arquivos no controle
                cursor.execute("SELECT COUNT(*) as count FROM oci_file_control")
                files_in_control = cursor.fetchone()['count'] if cursor.fetchone() else 0
                
                # Verificar último processamento do provedor
                cursor.execute("""
                    SELECT datatime_ultimo_update, datatime_proximo_update
                    FROM provedor_nuvem 
                    WHERE tipo = 'oci'
                """)
                provider_info = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                # Mostrar resultados
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"⏰ {timestamp} - Status atual:")
                
                total_atual = 0
                total_esperado = 0
                
                for day_data in current_data:
                    data_str = str(day_data['data'])
                    atual = day_data['registros_atual']
                    esperado = prd_expected.get(data_str, 0)
                    
                    total_atual += atual
                    total_esperado += esperado
                    
                    progresso = (atual / esperado * 100) if esperado > 0 else 0
                    status = "✅" if progresso >= 100 else "🔄" if progresso > 0 else "❌"
                    
                    print(f"   {data_str}: {atual:,}/{esperado:,} ({progresso:.1f}%) {status}")
                
                total_progresso = (total_atual / total_esperado * 100) if total_esperado > 0 else 0
                print(f"   📊 TOTAL: {total_atual:,}/{total_esperado:,} ({total_progresso:.1f}%)")
                
                if files_in_control > 0:
                    print(f"   📋 Arquivos no controle: {files_in_control}")
                
                if provider_info:
                    ultimo = provider_info['datatime_ultimo_update']
                    proximo = provider_info['datatime_proximo_update']
                    agora = datetime.now()
                    
                    if ultimo:
                        print(f"   🕐 Último update: {ultimo}")
                    if proximo:
                        deve_processar = proximo < agora
                        status_proc = "✅ Deve processar" if deve_processar else "⏳ Aguardando"
                        print(f"   🕑 Próximo update: {proximo} - {status_proc}")
                
                print("-" * 60)
                
                # Aguardar 30 segundos
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                time.sleep(10)
                
    except KeyboardInterrupt:
        print("\n👋 Monitoramento finalizado")

if __name__ == "__main__":
    monitor_progress()
