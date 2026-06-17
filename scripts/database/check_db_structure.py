#!/usr/bin/env python3
"""
Script para verificar estrutura das tabelas no banco
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_database_structure():
    """Verifica a estrutura atual do banco"""
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'finopsdatabase',
        'user': 'svc_finops',
        'password': '<sua-senha-do-banco>'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 Verificando tabelas OCI existentes...")
        
        # Verificar se tabelas de controle existem
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%oci%'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        if tables:
            print("📊 Tabelas OCI encontradas:")
            for table in tables:
                print(f"  - {table['table_name']}")
                
                # Verificar estrutura da tabela
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, (table['table_name'],))
                
                columns = cursor.fetchall()
                if columns:
                    print(f"    Colunas:")
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"      {col['column_name']}: {col['data_type']} {nullable}{default}")
                print()
        else:
            print("❌ Nenhuma tabela OCI encontrada")
        
        # Verificar tabelas principais do sistema
        print("🏛️ Verificando tabelas principais do sistema...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('provedor_nuvem', 'utilizacao_recurso', 'contrato')
            ORDER BY table_name;
        """)
        
        main_tables = cursor.fetchall()
        for table in main_tables:
            print(f"✅ {table['table_name']} existe")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    check_database_structure()
