#!/usr/bin/env python3
"""
Script para verificar configuração de banco e schemas
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_database_config():
    """Verifica configuração detalhada do banco"""
    
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
        
        print("🔍 VERIFICAÇÃO DE CONFIGURAÇÃO DO BANCO")
        print("=" * 50)
        
        # 1. Informações básicas do banco
        print("1. INFORMAÇÕES DO BANCO:")
        cursor.execute("SELECT current_database(), current_user, current_schema();")
        info = cursor.fetchone()
        print(f"   Database: {info[0]}")
        print(f"   User: {info[1]}")
        print(f"   Schema: {info[2]}")
        
        # 2. Listar todos os databases disponíveis
        print("\n2. DATABASES DISPONÍVEIS:")
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        for db in databases:
            print(f"   - {db['datname']}")
        
        # 3. Listar schemas no database atual
        print("\n3. SCHEMAS NO DATABASE ATUAL:")
        cursor.execute("SELECT schema_name FROM information_schema.schemata;")
        schemas = cursor.fetchall()
        for schema in schemas:
            print(f"   - {schema['schema_name']}")
        
        # 4. Verificar tabelas em cada schema
        print("\n4. TABELAS POR SCHEMA:")
        for schema in schemas:
            schema_name = schema['schema_name']
            if schema_name not in ['information_schema', 'pg_catalog', 'pg_toast']:
                cursor.execute("""
                    SELECT count(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = %s;
                """, (schema_name,))
                
                count = cursor.fetchone()['count']
                print(f"   {schema_name}: {count} tabela(s)")
                
                if count > 0 and count < 20:  # Mostrar tabelas se não forem muitas
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        ORDER BY table_name;
                    """, (schema_name,))
                    
                    tables = cursor.fetchall()
                    for table in tables[:10]:  # Mostrar apenas primeiras 10
                        print(f"     - {table['table_name']}")
                    if len(tables) > 10:
                        print(f"     ... e mais {len(tables) - 10} tabelas")
        
        # 5. Tentar outros databases comuns
        print("\n5. TESTANDO OUTROS DATABASES:")
        other_dbs = ['finops', 'postgres', 'finopsdatabase']
        
        for db_name in other_dbs:
            if db_name != db_config['database']:
                try:
                    test_config = db_config.copy()
                    test_config['database'] = db_name
                    
                    test_conn = psycopg2.connect(**test_config)
                    test_cursor = test_conn.cursor(cursor_factory=RealDictCursor)
                    
                    test_cursor.execute("""
                        SELECT count(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public';
                    """)
                    
                    count = test_cursor.fetchone()['count']
                    print(f"   {db_name}: {count} tabela(s) no schema public")
                    
                    if count > 0:
                        test_cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                            ORDER BY table_name
                            LIMIT 5;
                        """)
                        
                        tables = test_cursor.fetchall()
                        for table in tables:
                            print(f"     - {table['table_name']}")
                    
                    test_cursor.close()
                    test_conn.close()
                    
                except Exception as e:
                    print(f"   {db_name}: ❌ Erro - {e}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ VERIFICAÇÃO COMPLETA")
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    check_database_config()
