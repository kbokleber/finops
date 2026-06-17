#!/usr/bin/env python3
"""
Script para executar dentro do container finops

Este script deve ser executado dentro do container onde o sistema finops roda.
"""

import sys
import os
from datetime import datetime, timedelta
import traceback

# Adicionar paths necessários para o container
sys.path.insert(0, '/finops_celery')
sys.path.insert(0, '/finops_celery/helpers')

def test_connection():
    """Testa conexão básica com o banco"""
    try:
        from helpers.conexao_banco import ConexaoBancoDeDados
        
        conn = ConexaoBancoDeDados()
        conn.set_cursor()
        cursor = conn.get_cursor()
        
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        conn.close_cursor()
        conn.close_conection()
        
        print("✅ Conexão com banco funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False


def init_control_tables():
    """Inicializa tabelas de controle"""
    try:
        from helpers.conexao_banco import ConexaoBancoDeDados
        
        conn = ConexaoBancoDeDados()
        conn.set_cursor()
        cursor = conn.get_cursor()
        
        print("🔧 Criando tabelas de controle OCI...")
        
        # Tabela de controle de arquivos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oci_file_control (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(500) NOT NULL,
                file_hash VARCHAR(64) UNIQUE NOT NULL,
                size_bytes BIGINT DEFAULT 0,
                modified_date TIMESTAMPTZ NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                id_provedor INTEGER NOT NULL,
                id_cliente INTEGER NOT NULL,
                id_contrato INTEGER NOT NULL,
                records_total INTEGER DEFAULT 0,
                records_processed INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                records_duplicated INTEGER DEFAULT 0,
                processing_start TIMESTAMPTZ,
                processing_end TIMESTAMPTZ,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de controle de registros
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oci_record_control (
                id SERIAL PRIMARY KEY,
                file_control_id INTEGER REFERENCES oci_file_control(id) ON DELETE CASCADE,
                record_hash VARCHAR(64) NOT NULL,
                line_item_reference VARCHAR(255),
                resource_id VARCHAR(255),
                usage_start TIMESTAMPTZ,
                cost_amount DECIMAL(15,6),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                id_utilizacao_recurso INTEGER,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(record_hash)
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_control_hash ON oci_file_control(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_control_status ON oci_file_control(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_control_provedor ON oci_file_control(id_provedor, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_control_hash ON oci_record_control(record_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_control_status ON oci_record_control(status)")
        
        conn.commit()
        conn.close_cursor()
        conn.close_conection()
        
        print("✅ Tabelas de controle criadas com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        traceback.print_exc()
        return False


def check_tables():
    """Verifica se as tabelas existem"""
    try:
        from helpers.conexao_banco import ConexaoBancoDeDados
        
        conn = ConexaoBancoDeDados()
        conn.set_cursor()
        cursor = conn.get_cursor()
        
        # Verificar tabelas de controle
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('oci_file_control', 'oci_record_control')
            AND table_schema = 'public'
        """)
        
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        print("📋 Status das tabelas:")
        print(f"  oci_file_control: {'✅' if 'oci_file_control' in tables else '❌'}")
        print(f"  oci_record_control: {'✅' if 'oci_record_control' in tables else '❌'}")
        
        # Se as tabelas existem, mostrar estatísticas
        if 'oci_file_control' in tables:
            cursor.execute("SELECT COUNT(*) FROM oci_file_control")
            file_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) FROM oci_record_control")
            record_count = cursor.fetchone()['count']
            
            print(f"\n📊 Estatísticas:")
            print(f"  Arquivos controlados: {file_count}")
            print(f"  Registros controlados: {record_count}")
            
            # Status dos arquivos
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM oci_file_control 
                GROUP BY status
            """)
            
            print(f"\n📈 Status dos arquivos:")
            for row in cursor.fetchall():
                print(f"  {row['status']}: {row['count']}")
        
        conn.close_cursor()
        conn.close_conection()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        traceback.print_exc()
        return False


def analyze_existing_data():
    """Analisa dados existentes"""
    try:
        from helpers.conexao_banco import ConexaoBancoDeDados
        
        conn = ConexaoBancoDeDados()
        conn.set_cursor()
        cursor = conn.get_cursor()
        
        print("🔍 Analisando dados existentes...")
        
        # Estatísticas da tabela principal
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT data) as unique_dates,
                MIN(data) as min_date,
                MAX(data) as max_date,
                SUM(custo_total) as total_cost,
                COUNT(DISTINCT id_do_provedor) as unique_references
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
        """)
        
        stats = cursor.fetchone()
        
        print("📊 Tabela principal (utilizacao_recurso):")
        print(f"  Total de registros: {stats['total_records']:,}")
        print(f"  Datas únicas: {stats['unique_dates']:,}")
        print(f"  Período: {stats['min_date']} a {stats['max_date']}")
        print(f"  Custo total: R$ {float(stats['total_cost']):,.2f}")
        print(f"  Referências únicas: {stats['unique_references']:,}")
        
        # Registros por data (últimos 10 dias)
        cursor.execute("""
            SELECT data, COUNT(*) as count, SUM(custo_total) as custo
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3
            GROUP BY data 
            ORDER BY data DESC 
            LIMIT 10
        """)
        
        print(f"\n📅 Últimos 10 dias:")
        for row in cursor.fetchall():
            print(f"  {row['data']}: {row['count']:,} registros - R$ {float(row['custo']):,.2f}")
        
        # Verificar duplicatas óbvias
        cursor.execute("""
            SELECT COUNT(*) as duplicates
            FROM (
                SELECT id_do_provedor, COUNT(*) as count
                FROM utilizacao_recurso 
                WHERE cloudproviderid = 3 
                AND id_do_provedor IS NOT NULL 
                AND id_do_provedor != ''
                GROUP BY id_do_provedor 
                HAVING COUNT(*) > 1
            ) dup
        """)
        
        dup_count = cursor.fetchone()['duplicates']
        
        if dup_count > 0:
            print(f"\n⚠️  {dup_count} possíveis duplicatas por referência encontradas")
        else:
            print(f"\n✅ Nenhuma duplicata óbvia encontrada")
        
        conn.close_cursor()
        conn.close_conection()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        traceback.print_exc()
        return False


def show_usage():
    """Mostra ajuda"""
    print("""
🔧 Setup OCI Container

Comandos:
  test       - Testa conexão com banco
  init       - Inicializa tabelas de controle
  check      - Verifica status das tabelas
  analyze    - Analisa dados existentes
  help       - Mostra esta ajuda

Uso dentro do container:
  python setup_oci_container.py [comando]
""")


def main():
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    print("🔧 Setup OCI Container")
    print("=" * 30)
    
    if command == "test":
        success = test_connection()
    elif command == "init":
        success = init_control_tables()
    elif command == "check":
        success = check_tables()
    elif command == "analyze":
        success = analyze_existing_data()
    elif command == "help":
        show_usage()
        return
    else:
        print(f"❌ Comando desconhecido: {command}")
        show_usage()
        return
    
    if success:
        print("\n🎉 Sucesso!")
    else:
        print("\n💥 Falhou!")


if __name__ == "__main__":
    main()
