#!/usr/bin/env python3
"""
Script para listar todas as tabelas e encontrar as relacionadas a OCI
"""

import sys
import os
sys.path.insert(0, '/finops_celery')

from settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    print("🔍 Listando todas as tabelas do banco")
    
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Listar todas as tabelas
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            all_tables = cursor.fetchall()
            
            print(f"📊 Total de tabelas: {len(all_tables)}")
            
            oci_related = []
            other_tables = []
            
            for table in all_tables:
                table_name = table['table_name']
                if 'oci' in table_name.lower():
                    oci_related.append(table_name)
                else:
                    other_tables.append(table_name)
            
            print(f"\n🎯 Tabelas relacionadas a OCI ({len(oci_related)}):")
            for table in oci_related:
                print(f"  - {table}")
            
            print(f"\n📋 Outras tabelas ({len(other_tables)}):")
            for table in other_tables[:20]:  # Limitar para não poluir
                print(f"  - {table}")
            if len(other_tables) > 20:
                print(f"  ... e mais {len(other_tables) - 20} tabelas")
            
            # Se encontramos tabelas OCI, vamos analisá-las
            if oci_related:
                for table in oci_related:
                    print(f"\n📋 Estrutura da tabela {table}:")
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    
                    columns = cursor.fetchall()
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        print(f"  - {col['column_name']}: {col['data_type']} {nullable}")
                    
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
                    count = cursor.fetchone()['total']
                    print(f"  📊 Total de registros: {count}")
            
            # Tentar criar nossa estrutura se não existe
            if not oci_related:
                print(f"\n🔧 Nenhuma tabela OCI encontrada. Criando estrutura...")
                
                # Criar tabela de controle de arquivos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS oci_file_control (
                        id SERIAL PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_hash TEXT NOT NULL UNIQUE,
                        file_size BIGINT,
                        status VARCHAR(20) DEFAULT 'pending',
                        total_records INTEGER DEFAULT 0,
                        processed_records INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT
                    )
                """)
                
                # Criar tabela de controle de registros
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS oci_record_control (
                        id SERIAL PRIMARY KEY,
                        file_control_id INTEGER REFERENCES oci_file_control(id),
                        record_hash TEXT NOT NULL UNIQUE,
                        line_number INTEGER,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        error_message TEXT
                    )
                """)
                
                # Criar índices
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_status ON oci_file_control(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_hash ON oci_file_control(file_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_file ON oci_record_control(file_control_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_status ON oci_record_control(status)")
                
                conn.commit()
                print("✅ Tabelas OCI criadas com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
