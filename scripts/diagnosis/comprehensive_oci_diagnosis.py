#!/usr/bin/env python3
"""
Diagnóstico e Correção Completa do Sistema OCI
Identifica problemas e força o processamento correto
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import sys
import os

def comprehensive_oci_diagnosis():
    """Diagnóstico completo do sistema OCI"""
    print("🔍 DIAGNÓSTICO COMPLETO DO SISTEMA OCI")
    print("=" * 60)
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'svc_finops',
        'password': '<sua-senha-do-banco>',
        'dbname': 'finopsdatabase'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. DIAGNÓSTICO DO PROVEDOR
        print("\n1. 🔍 DIAGNÓSTICO DO PROVEDOR OCI:")
        
        cursor.execute("""
            SELECT 
                id_provedor,
                nome,
                tipo,
                regiao,
                datatime_ultimo_update,
                datatime_proximo_update,
                id_contrato,
                jobs_restantes,
                config_de_acesso IS NOT NULL as has_config
            FROM provedor_nuvem 
            WHERE tipo = 'oci'
        """)
        
        provedores = cursor.fetchall()
        
        if not provedores:
            print("   ❌ ERRO: Nenhum provedor OCI encontrado!")
            return False
        
        for prov in provedores:
            print(f"   📋 Provedor ID: {prov['id_provedor']}")
            print(f"      Nome: {prov['nome']}")
            print(f"      Região: {prov['regiao']}")
            print(f"      Contrato ID: {prov['id_contrato']}")
            print(f"      Configuração: {'✅' if prov['has_config'] else '❌'}")
            print(f"      Último update: {prov['datatime_ultimo_update']}")
            print(f"      Próximo update: {prov['datatime_proximo_update']}")
            print(f"      Jobs restantes: {prov['jobs_restantes']}")
            
            # Verificar se está pronto para processamento
            now = datetime.now()
            if prov['datatime_proximo_update'] and prov['datatime_proximo_update'] <= now:
                print("      🟢 Status: PRONTO PARA PROCESSAMENTO")
            else:
                diff = prov['datatime_proximo_update'] - now if prov['datatime_proximo_update'] else None
                print(f"      🔴 Status: AGUARDANDO ({diff} restantes)" if diff else "      🔴 Status: SEM AGENDAMENTO")
        
        # 2. VERIFICAR CONTRATO
        print("\n2. 🔍 VERIFICANDO CONTRATOS:")
        
        cursor.execute("""
            SELECT 
                ct.id_contrato,
                ct.id_cliente,
                ct.nome as contrato_nome
            FROM contrato ct
            JOIN provedor_nuvem pn ON ct.id_contrato = pn.id_contrato
            WHERE pn.tipo = 'oci'
        """)
        
        contratos = cursor.fetchall()
        
        if contratos:
            for contrato in contratos:
                print(f"   📋 Contrato ID: {contrato['id_contrato']}")
                print(f"      Cliente ID: {contrato['id_cliente']}")
                print(f"      Nome: {contrato['contrato_nome']}")
        else:
            print("   ❌ ERRO: Nenhum contrato associado encontrado!")
        
        # 3. VERIFICAR DADOS HISTÓRICOS
        print("\n3. 📊 DADOS HISTÓRICOS OCI:")
        
        cursor.execute("""
            SELECT 
                MIN(data::date) as data_inicio,
                MAX(data::date) as data_fim,
                COUNT(*) as total_registros,
                COUNT(DISTINCT data::date) as dias_com_dados
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
        """)
        
        historico = cursor.fetchone()
        
        if historico and historico['total_registros']:
            print(f"   📅 Período: {historico['data_inicio']} até {historico['data_fim']}")
            print(f"   📊 Total registros: {historico['total_registros']:,}")
            print(f"   📈 Dias com dados: {historico['dias_com_dados']}")
            
            # Verificar últimos 10 dias
            cursor.execute("""
                SELECT 
                    data::date,
                    COUNT(*) as registros
                FROM utilizacao_recurso 
                WHERE cloudproviderid = 3 
                AND data >= CURRENT_DATE - INTERVAL '10 days'
                GROUP BY data::date
                ORDER BY data::date DESC
            """)
            
            ultimos_dias = cursor.fetchall()
            print("   📈 Últimos 10 dias:")
            for dia in ultimos_dias:
                print(f"      {dia['data']}: {dia['registros']:,}")
        else:
            print("   ❌ NENHUM DADO HISTÓRICO ENCONTRADO!")
        
        # 4. FORÇAR MÚLTIPLAS CONFIGURAÇÕES
        print("\n4. 🔧 FORÇANDO CONFIGURAÇÕES PARA PROCESSAMENTO:")
        
        # Configuração 1: Resetar para data bem anterior
        print("   🔄 Configuração 1: Reset para data anterior...")
        cursor.execute("""
            UPDATE provedor_nuvem 
            SET 
                datatime_ultimo_update = '2025-07-17 00:00:00',
                datatime_proximo_update = NOW() - INTERVAL '2 hours',
                jobs_restantes = 0
            WHERE tipo = 'oci'
        """)
        conn.commit()
        
        # Configuração 2: Verificar se processamento foi agendado
        print("   ⏰ Aguardando 5 segundos...")
        import time
        time.sleep(5)
        
        # Executar task múltiplas vezes
        print("   🚀 Executando task 3 vezes...")
        
        sys.path.append('/finops/finops_celery')
        
        try:
            from finops_celery.tasks.get_oci import task_verificar_provedores_oci_para_update
            
            for i in range(3):
                print(f"      Execução {i+1}/3...")
                result = task_verificar_provedores_oci_para_update()
                print(f"      ✅ Resultado: {result}")
                
                # Verificar se jobs foram criados
                cursor.execute("SELECT jobs_restantes FROM provedor_nuvem WHERE tipo = 'oci'")
                jobs = cursor.fetchone()
                if jobs and jobs['jobs_restantes'] > 0:
                    print(f"      🎉 {jobs['jobs_restantes']} jobs criados!")
                    break
                
                time.sleep(3)
            
        except Exception as e:
            print(f"      ❌ Erro na execução: {e}")
        
        # 5. VERIFICAR RESULTADO FINAL
        print("\n5. 📊 VERIFICAÇÃO FINAL:")
        
        # Jobs em andamento
        cursor.execute("SELECT jobs_restantes FROM provedor_nuvem WHERE tipo = 'oci'")
        jobs_final = cursor.fetchone()
        print(f"   ⚙️  Jobs em andamento: {jobs_final['jobs_restantes'] if jobs_final else 0}")
        
        # Arquivos no controle
        cursor.execute("SELECT COUNT(*) FROM oci_file_control")
        files_controle = cursor.fetchone()['count']
        print(f"   📁 Arquivos no controle: {files_controle}")
        
        # Status do provedor após execução
        cursor.execute("""
            SELECT 
                datatime_ultimo_update,
                datatime_proximo_update
            FROM provedor_nuvem 
            WHERE tipo = 'oci'
        """)
        status_final = cursor.fetchone()
        print(f"   📅 Último update: {status_final['datatime_ultimo_update']}")
        print(f"   ⏰ Próximo update: {status_final['datatime_proximo_update']}")
        
        # 6. VERIFICAR SE HÁ DADOS SENDO PROCESSADOS
        print("\n6. ⏳ AGUARDANDO PROCESSAMENTO:")
        print("   Aguardando 60 segundos para verificar processamento...")
        time.sleep(60)
        
        # Verificar novos dados
        cursor.execute("""
            SELECT COUNT(*) FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 AND data >= '2025-07-19'
        """)
        novos_dados = cursor.fetchone()['count']
        
        print(f"   📈 Dados recentes após processamento: {novos_dados:,}")
        
        if novos_dados > 0:
            print("   🎉 SUCESSO! Processamento funcionando!")
            
            # Mostrar detalhes
            cursor.execute("""
                SELECT data::date, COUNT(*) 
                FROM utilizacao_recurso 
                WHERE cloudproviderid = 3 AND data >= '2025-07-19'
                GROUP BY data::date 
                ORDER BY data::date
            """)
            
            for data, count in cursor.fetchall():
                print(f"      {data}: {count:,}")
        else:
            print("   ⚠️  Ainda sem dados. Possíveis causas:")
            print("      • Arquivos OCI não disponíveis na origem")
            print("      • Problema de conectividade com OCI")
            print("      • Configuração de acesso incorreta")
            print("      • Filtros de data muito restritivos")
        
        cursor.close()
        conn.close()
        
        return novos_dados > 0
        
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_monitoring_script():
    """Cria script de monitoramento contínuo"""
    print("\n" + "="*60)
    print("📊 SCRIPT DE MONITORAMENTO CONTÍNUO")
    print("="*60)
    
    script_content = '''
#!/usr/bin/env python3
# Script de monitoramento contínuo do sistema OCI

import psycopg2
import time
from datetime import datetime

def monitor_oci():
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='svc_finops',
        password='<sua-senha-do-banco>',
        dbname='finopsdatabase'
    )
    cursor = conn.cursor()
    
    print(f"🕐 Monitoramento iniciado: {datetime.now()}")
    
    while True:
        try:
            # Status do provedor
            cursor.execute("SELECT jobs_restantes, datatime_proximo_update FROM provedor_nuvem WHERE tipo = 'oci'")
            status = cursor.fetchone()
            
            # Dados recentes
            cursor.execute("SELECT COUNT(*) FROM utilizacao_recurso WHERE cloudproviderid = 3 AND data >= '2025-07-19'")
            dados_recentes = cursor.fetchone()[0]
            
            # Arquivos no controle
            cursor.execute("SELECT COUNT(*) FROM oci_file_control")
            arquivos = cursor.fetchone()[0]
            
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Jobs: {status[0]} | Dados: {dados_recentes:,} | Arquivos: {arquivos} | Próximo: {status[1]}")
            
            time.sleep(60)  # Verificar a cada minuto
            
        except KeyboardInterrupt:
            print("\\n🛑 Monitoramento interrompido")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            time.sleep(30)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    monitor_oci()
'''
    
    # Salvar script
    with open('/root/scripts/monitor_oci.py', 'w') as f:
        f.write(script_content)
    
    print("   ✅ Script salvo em: /root/scripts/monitor_oci.py")
    print("\n   🚀 Para usar:")
    print("   docker exec -it finops-finops_worker_faz-1 python3 /tmp/monitor_oci.py")

def main():
    """Função principal"""
    print(f"🕐 Diagnóstico iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = comprehensive_oci_diagnosis()
    
    if success:
        print("\n🎉 DIAGNÓSTICO CONCLUÍDO - SISTEMA FUNCIONANDO!")
    else:
        print("\n⚠️  DIAGNÓSTICO CONCLUÍDO - PROBLEMAS DETECTADOS")
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("• Verificar conectividade com OCI")
        print("• Validar configurações de acesso")
        print("• Confirmar disponibilidade de arquivos")
        print("• Revisar filtros de data no código")
    
    create_monitoring_script()
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("• Use o script de monitoramento para acompanhar")
    print("• Aguarde processamento por 10-15 minutos")
    print("• Verifique logs do container se necessário")

if __name__ == "__main__":
    main()
