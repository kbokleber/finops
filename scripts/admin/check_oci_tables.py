#!/usr/bin/env python3
"""
Script para comparar processamento PRD vs DEV e identificar diferenças
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

def analyze_processing_differences():
    """Analisa diferenças entre PRD e DEV"""
    print("🔍 ANÁLISE DE DIFERENÇAS PRD vs DEV")
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
        
        # 1. Status detalhado dos últimos 3 dias
        print("\n📊 1. REGISTROS POR DIA (DEV):")
        cursor.execute("""
            SELECT 
                data::date as data,
                COUNT(*) as registros,
                COUNT(DISTINCT id_do_provedor) as referencias_unicas,
                MIN(data) as primeiro_timestamp,
                MAX(data) as ultimo_timestamp
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND data >= '2025-07-19'
            GROUP BY data::date
            ORDER BY data::date;
        """)
        
        daily_data = cursor.fetchall()
        for day in daily_data:
            print(f"   {day['data']}: {day['registros']:,} registros")
            print(f"      Referências únicas: {day['referencias_unicas']:,}")
            print(f"      Período: {day['primeiro_timestamp']} a {day['ultimo_timestamp']}")
        
        # 2. Verificar arquivos processados hoje
        print(f"\n📂 2. ARQUIVOS PROCESSADOS EM {date.today()}:")
        cursor.execute("""
            SELECT 
                file_name,
                status,
                records_total,
                records_processed,
                records_errors,
                processing_started,
                processing_finished,
                EXTRACT(EPOCH FROM (processing_finished - processing_started)) as tempo_segundos
            FROM oci_file_control 
            WHERE DATE(created_at) = CURRENT_DATE
            AND file_name NOT LIKE '%test%'
            ORDER BY created_at;
        """)
        
        todays_files = cursor.fetchall()
        if todays_files:
            total_processed = 0
            total_errors = 0
            for file in todays_files:
                print(f"   📁 {file['file_name'][:60]}...")
                print(f"      Status: {file['status']}")
                print(f"      Registros: {file['records_total']} total, {file['records_processed']} OK, {file['records_errors']} erros")
                if file['tempo_segundos']:
                    print(f"      Tempo: {file['tempo_segundos']:.2f}s")
                print()
                total_processed += file['records_processed'] or 0
                total_errors += file['records_errors'] or 0
            
            print(f"   📊 RESUMO HOJE:")
            print(f"      Total arquivos: {len(todays_files)}")
            print(f"      Total processados: {total_processed:,}")
            print(f"      Total erros: {total_errors:,}")
        else:
            print("   ❌ Nenhum arquivo processado hoje!")
        
        # 3. Verificar arquivos pendentes/travados
        print("\n⏳ 3. ARQUIVOS PENDENTES/TRAVADOS:")
        cursor.execute("""
            SELECT 
                file_name,
                status,
                created_at,
                processing_started,
                CASE 
                    WHEN processing_started IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (NOW() - processing_started))/60 
                    ELSE NULL 
                END as minutos_processando
            FROM oci_file_control 
            WHERE status IN ('pending', 'processing')
            ORDER BY created_at;
        """)
        
        pending_files = cursor.fetchall()
        if pending_files:
            for file in pending_files:
                print(f"   📁 {file['file_name'][:60]}...")
                print(f"      Status: {file['status']}")
                print(f"      Criado: {file['created_at']}")
                if file['minutos_processando']:
                    print(f"      Processando há: {file['minutos_processando']:.1f} minutos")
                print()
        else:
            print("   ✅ Nenhum arquivo pendente")
        
        # 4. Verificar últimos registros inseridos
        print("\n📝 4. ÚLTIMOS REGISTROS INSERIDOS:")
        cursor.execute("""
            SELECT 
                data,
                quantidade_utilizada,
                custo_total,
                id_do_provedor
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
            ORDER BY data DESC
            LIMIT 10;
        """)
        
        recent_records = cursor.fetchall()
        print("   Últimos 10 registros:")
        for record in recent_records:
            print(f"      {record['data']} - R${record['custo_total']} - Ref: {record['id_do_provedor'][:20]}...")
        
        # 5. Análise de horários
        print("\n⏰ 5. ANÁLISE DE HORÁRIOS (HOJE):")
        cursor.execute("""
            SELECT 
                EXTRACT(HOUR FROM data) as hora,
                COUNT(*) as registros
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
            AND DATE(data) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM data)
            ORDER BY hora;
        """)
        
        hourly_data = cursor.fetchall()
        if hourly_data:
            print("   Registros por hora hoje:")
            for hour in hourly_data:
                print(f"      {int(hour['hora']):02d}:00 - {hour['registros']:,} registros")
        else:
            print("   ❌ Nenhum registro com timestamp de hoje")
        
        # 6. Verificar se há duplicatas sendo bloqueadas
        print("\n🔒 6. VERIFICANDO DUPLICATAS BLOQUEADAS:")
        cursor.execute("""
            SELECT 
                COUNT(*) as arquivos_skipped
            FROM oci_file_control 
            WHERE DATE(created_at) = CURRENT_DATE
            AND status = 'skipped';
        """)
        
        skipped = cursor.fetchone()
        if skipped['arquivos_skipped'] > 0:
            print(f"   ⚠️  {skipped['arquivos_skipped']} arquivos foram pulados (já processados)")
            
            # Ver quais arquivos foram pulados
            cursor.execute("""
                SELECT file_name, created_at
                FROM oci_file_control 
                WHERE DATE(created_at) = CURRENT_DATE
                AND status = 'skipped'
                ORDER BY created_at;
            """)
            
            skipped_files = cursor.fetchall()
            for file in skipped_files:
                print(f"      📁 {file['file_name']} - {file['created_at']}")
        else:
            print("   ✅ Nenhum arquivo foi pulado por duplicação")
        
        # 7. Comparação com expectativa
        print("\n🎯 7. ANÁLISE DA DIFERENÇA:")
        expected_today = 4776  # PRD
        actual_today = 2983    # DEV
        difference = expected_today - actual_today
        
        print(f"   PRD (esperado): {expected_today:,} registros")
        print(f"   DEV (atual): {actual_today:,} registros")
        print(f"   Diferença: {difference:,} registros ({difference/expected_today*100:.1f}%)")
        
        if todays_files:
            files_processed = sum(f['records_processed'] or 0 for f in todays_files)
            print(f"   Registros por arquivos hoje: {files_processed:,}")
            if files_processed != actual_today:
                print(f"   ⚠️  Diferença entre controle e tabela principal: {abs(files_processed - actual_today):,}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_celery_tasks():
    """Verifica status das tasks do Celery"""
    print("\n🔄 VERIFICANDO TASKS DO CELERY:")
    
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
        
        # Verificar status dos provedores
        cursor.execute("""
            SELECT 
                id_provedor,
                tipo,
                jobs_restantes,
                datatime_ultimo_update,
                datatime_proximo_update
            FROM provedor_nuvem 
            WHERE tipo = 'oci';
        """)
        
        providers = cursor.fetchall()
        for provider in providers:
            print(f"   Provedor {provider['id_provedor']}:")
            print(f"      Jobs restantes: {provider['jobs_restantes']}")
            print(f"      Último update: {provider['datatime_ultimo_update']}")
            print(f"      Próximo update: {provider['datatime_proximo_update']}")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    """Função principal"""
    print("🔍 INVESTIGAÇÃO: DIFERENÇA PRD vs DEV")
    print(f"Data de análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if analyze_processing_differences():
        check_celery_tasks()
        
        print("\n" + "="*50)
        print("💡 CONCLUSÕES E RECOMENDAÇÕES:")
        print("="*50)
        print("""
🎯 POSSÍVEIS CAUSAS DA DIFERENÇA:

1. ⏰ TIMING: DEV pode estar processando em horário diferente
2. 🔒 DUPLICATAS: Sistema novo pode estar bloqueando arquivos já processados
3. 📂 PENDÊNCIAS: Arquivos podem estar na fila esperando processamento
4. 🚫 REJEIÇÕES: Arquivos podem estar sendo rejeitados por algum critério

🔧 PRÓXIMOS PASSOS:
1. Verificar se há arquivos pendentes
2. Comparar horários de processamento
3. Verificar logs do Celery
4. Confirmar se não há arquivos duplicados sendo bloqueados
5. Validar se critérios de filtro estão iguais

📊 MONITORAMENTO:
- Acompanhar processamento das próximas horas
- Comparar novamente no final do dia
- Verificar se diferença persiste amanhã
        """)
    else:
        print("Falha na análise.")

if __name__ == "__main__":
    main()
