#!/usr/bin/env python3
"""
Script para verificar estrutura existente das tabelas OCI
"""

import sys
import os
sys.path.insert(0, '/finops_celery')

from settings import DATABASE_URL
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    print("🔍 Verificando estrutura existente das tabelas OCI")
    
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Verificar se as tabelas existem
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%oci%'
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            print(f"📊 Tabelas OCI encontradas: {tables}")
            
            for table in tables:
                print(f"\n📋 Estrutura da tabela {table}:")
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cursor.fetchall()
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"  - {col['column_name']}: {col['data_type']} {nullable}{default}")
                
                # Verificar quantidade de registros
                cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
                count = cursor.fetchone()['total']
                print(f"  📊 Total de registros: {count}")
                
                if count > 0:
                    # Mostrar alguns exemplos
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"  📝 Exemplos:")
                    for i, sample in enumerate(samples, 1):
                        print(f"    {i}. {dict(sample)}")
            
            # Verificar se podemos usar a estrutura existente
            print(f"\n🔧 Analisando compatibilidade...")
            
            # Verificar se temos as colunas necessárias na tabela principal
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'oci_file_control'
            """)
            file_columns = [row['column_name'] for row in cursor.fetchall()]
            
            required_file_columns = ['file_path', 'file_name', 'file_hash', 'status']
            missing_file_cols = [col for col in required_file_columns if col not in file_columns]
            
            if missing_file_cols:
                print(f"❌ Faltam colunas na oci_file_control: {missing_file_cols}")
            else:
                print(f"✅ Tabela oci_file_control tem as colunas necessárias")
            
            # Verificar tabela de registros
            if 'oci_record_control' in tables:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'oci_record_control'
                """)
                record_columns = [row['column_name'] for row in cursor.fetchall()]
                
                required_record_columns = ['record_hash', 'status']
                missing_record_cols = [col for col in required_record_columns if col not in record_columns]
                
                if missing_record_cols:
                    print(f"❌ Faltam colunas na oci_record_control: {missing_record_cols}")
                else:
                    print(f"✅ Tabela oci_record_control tem as colunas necessárias")
            else:
                print(f"❌ Tabela oci_record_control não existe")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
