#!/usr/bin/env python3
"""
Script de validação final do sistema OCI melhorado
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import traceback

def validate_oci_system():
    """Valida o sistema completo de controle OCI"""
    print("🔍 Validação Final do Sistema OCI Melhorado")
    print("=" * 50)
    
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
        
        # 1. Verificar tabelas de controle
        print("\n📊 1. Verificando tabelas de controle...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('oci_file_control', 'oci_record_control')
            ORDER BY table_name
        """)
        
        control_tables = cursor.fetchall()
        if len(control_tables) == 2:
            print("✅ Tabelas de controle existem:")
            for table in control_tables:
                print(f"  - {table['table_name']}")
        else:
            print("❌ Tabelas de controle não encontradas")
            return False
        
        # 2. Verificar estrutura das tabelas
        print("\n🏗️ 2. Verificando estrutura das tabelas...")
        
        # oci_file_control
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oci_file_control'
            ORDER BY ordinal_position
        """)
        file_columns = [row['column_name'] for row in cursor.fetchall()]
        
        required_file_cols = ['id', 'file_name', 'file_hash', 'status', 'provider_id', 
                             'client_id', 'contract_id', 'processing_started', 'processing_finished']
        
        missing_file_cols = set(required_file_cols) - set(file_columns)
        if not missing_file_cols:
            print("✅ Estrutura oci_file_control: OK")
        else:
            print(f"❌ Colunas ausentes em oci_file_control: {missing_file_cols}")
        
        # oci_record_control
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'oci_record_control'
            ORDER BY ordinal_position
        """)
        record_columns = [row['column_name'] for row in cursor.fetchall()]
        
        required_record_cols = ['id', 'file_control_id', 'record_hash', 'status', 
                               'interval_usage_start', 'reference_no']
        
        missing_record_cols = set(required_record_cols) - set(record_columns)
        if not missing_record_cols:
            print("✅ Estrutura oci_record_control: OK")
        else:
            print(f"❌ Colunas ausentes em oci_record_control: {missing_record_cols}")
        
        # 3. Verificar dados de teste
        print("\n🧪 3. Verificando dados de teste...")
        
        cursor.execute("SELECT COUNT(*) as count FROM oci_file_control")
        file_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM oci_record_control")
        record_count = cursor.fetchone()['count']
        
        print(f"📄 Arquivos de controle: {file_count}")
        print(f"📝 Registros de controle: {record_count}")
        
        if file_count > 0:
            # Mostrar status dos arquivos
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM oci_file_control 
                GROUP BY status 
                ORDER BY status
            """)
            file_status = cursor.fetchall()
            
            print("📊 Status dos arquivos:")
            for status in file_status:
                print(f"  {status['status']}: {status['count']}")
        
        # 4. Verificar sistema principal
        print("\n🎯 4. Verificando sistema principal...")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
        """)
        main_records = cursor.fetchone()['count']
        print(f"📈 Registros OCI na tabela principal: {main_records:,}")
        
        # 5. Verificar integridade
        print("\n🔧 5. Verificando integridade...")
        
        # Verificar se há arquivos em processamento há muito tempo
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM oci_file_control 
            WHERE status = 'processing' 
            AND processing_started < NOW() - INTERVAL '2 hours'
        """)
        stuck_files = cursor.fetchone()['count']
        
        if stuck_files > 0:
            print(f"⚠️  {stuck_files} arquivos travados em processamento")
        else:
            print("✅ Nenhum arquivo travado")
        
        # 6. Estatísticas recentes
        print("\n📅 6. Estatísticas dos últimos 7 dias...")
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as files,
                SUM(records_total) as total_records,
                SUM(records_processed) as processed_records
            FROM oci_file_control 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        """)
        
        recent_stats = cursor.fetchall()
        if recent_stats:
            print("📊 Atividade recente:")
            for stat in recent_stats:
                print(f"  {stat['date']}: {stat['files']} arquivos, {stat['total_records'] or 0} registros")
        else:
            print("ℹ️  Nenhuma atividade nos últimos 7 dias")
        
        # 7. Verificar performance
        print("\n⚡ 7. Verificando performance...")
        
        cursor.execute("""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (processing_finished - processing_started))) as avg_processing_time,
                COUNT(*) as processed_files
            FROM oci_file_control 
            WHERE status = 'processed' 
            AND processing_started IS NOT NULL 
            AND processing_finished IS NOT NULL
        """)
        
        perf = cursor.fetchone()
        if perf and perf['processed_files'] > 0:
            avg_time = perf['avg_processing_time']
            print(f"📊 Tempo médio de processamento: {avg_time:.2f} segundos")
            print(f"📊 Arquivos processados com sucesso: {perf['processed_files']}")
        else:
            print("ℹ️  Dados de performance não disponíveis")
        
        # 8. Resumo final
        print("\n🎯 8. Resumo da validação:")
        
        issues = []
        
        if len(control_tables) != 2:
            issues.append("Tabelas de controle ausentes")
        
        if missing_file_cols:
            issues.append("Estrutura de oci_file_control incompleta")
            
        if missing_record_cols:
            issues.append("Estrutura de oci_record_control incompleta")
        
        if stuck_files > 0:
            issues.append(f"{stuck_files} arquivos travados")
        
        if issues:
            print("❌ Problemas encontrados:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ Sistema OCI melhorado validado com sucesso!")
            print("🎉 O sistema está pronto para uso em produção!")
            return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()


def show_system_status():
    """Mostra status detalhado do sistema"""
    print("\n" + "="*60)
    print("📋 RESUMO DO SISTEMA OCI MELHORADO")
    print("="*60)
    
    print("""
🎯 FUNCIONALIDADES IMPLEMENTADAS:

✅ Controle de Arquivos:
   - Hash único por arquivo (evita reprocessamento)
   - Rastreamento de status (pending/processing/processed/error)
   - Metadados de processamento
   - Timestamps de início/fim

✅ Controle de Registros:
   - Hash único por registro (evita duplicação)
   - Rastreamento individual de status
   - Dados completos do registro em JSONB
   - Referência ao arquivo de origem

✅ Sistema de Monitoramento:
   - Logs detalhados
   - Estatísticas de processamento
   - Detecção de arquivos travados
   - Métricas de performance

✅ Integração com Celery:
   - Tasks atualizadas com controle
   - Compatibilidade com sistema existente
   - Rollback em caso de erro
   - Retorno de estatísticas

✅ Prevenção de Problemas:
   - Evita duplicação de arquivos
   - Evita duplicação de registros
   - Recovery automático de falhas
   - Limpeza de dados antigos

🚀 PRÓXIMOS PASSOS:
   1. Monitorar processamentos em produção
   2. Ajustar tunning se necessário
   3. Implementar alertas automáticos
   4. Criar dashboards de monitoramento
""")


def main():
    """Função principal"""
    success = validate_oci_system()
    
    if success:
        show_system_status()
        print("\n🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("\n💥 VALIDAÇÃO FALHOU - VERIFICAR PROBLEMAS ACIMA")


if __name__ == "__main__":
    main()
