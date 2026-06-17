#!/usr/bin/env python3
"""
Script de inicialização das tabelas OCI - versão simplificada
"""

import sys
import os
sys.path.insert(0, '/finops_celery')

from settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    print("🚀 Inicializando sistema de controle OCI")
    
    # Conectar ao banco
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Verificar se as tabelas já existem
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('oci_file_control', 'oci_record_control')
            """)
            existing_tables = [row['table_name'] for row in cursor.fetchall()]
            
            print(f"📊 Tabelas existentes: {existing_tables}")
            
            if 'oci_file_control' not in existing_tables:
                print("🔧 Criando tabela oci_file_control...")
                cursor.execute("""
                    CREATE TABLE oci_file_control (
                        id SERIAL PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_hash TEXT NOT NULL,
                        file_size BIGINT,
                        status VARCHAR(20) DEFAULT 'pending',
                        total_records INTEGER DEFAULT 0,
                        processed_records INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        UNIQUE(file_hash)
                    )
                """)
                print("✅ Tabela oci_file_control criada!")
            else:
                print("✅ Tabela oci_file_control já existe")
            
            if 'oci_record_control' not in existing_tables:
                print("🔧 Criando tabela oci_record_control...")
                cursor.execute("""
                    CREATE TABLE oci_record_control (
                        id SERIAL PRIMARY KEY,
                        file_control_id INTEGER REFERENCES oci_file_control(id),
                        record_hash TEXT NOT NULL,
                        line_number INTEGER,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        error_message TEXT,
                        UNIQUE(record_hash)
                    )
                """)
                print("✅ Tabela oci_record_control criada!")
            else:
                print("✅ Tabela oci_record_control já existe")
            
            # Criar índices se não existirem
            indices = [
                ("idx_oci_file_status", "oci_file_control", "status"),
                ("idx_oci_file_created", "oci_file_control", "created_at"),
                ("idx_oci_file_hash", "oci_file_control", "file_hash"),
                ("idx_oci_record_file", "oci_record_control", "file_control_id"),
                ("idx_oci_record_status", "oci_record_control", "status"),
                ("idx_oci_record_hash", "oci_record_control", "record_hash"),
            ]
            
            for idx_name, table_name, column in indices:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column})")
                    print(f"✅ Índice {idx_name} criado/verificado")
                except Exception as e:
                    print(f"⚠️  Problema com índice {idx_name}: {e}")
            
            conn.commit()
            print("💾 Alterações salvas no banco!")
            
            # Verificar estrutura das tabelas
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('oci_file_control', 'oci_record_control')
                ORDER BY table_name, ordinal_position
            """)
            
            structure = cursor.fetchall()
            current_table = None
            for row in structure:
                if row['table_name'] != current_table:
                    current_table = row['table_name']
                    print(f"\n📋 Estrutura da tabela {current_table}:")
                print(f"  - {row['column_name']}: {row['data_type']}")
            
            # Verificar dados existentes
            cursor.execute("SELECT COUNT(*) as total FROM oci_file_control")
            file_count = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM oci_record_control")
            record_count = cursor.fetchone()['total']
            
            print(f"\n📊 Estado atual:")
            print(f"  - Arquivos controlados: {file_count}")
            print(f"  - Registros controlados: {record_count}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\n🎉 Sistema de controle OCI inicializado com sucesso!")

if __name__ == "__main__":
    main()
