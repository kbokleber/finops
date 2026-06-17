#!/usr/bin/env python3
"""
Script básico de diagnóstico do sistema OCI
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def simple_db_test():
    """Teste básico do banco"""
    print("🔍 Teste básico do banco de dados...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='svc_finops',
            password='<sua-senha-do-banco>',
            dbname='finopsdatabase'
        )
        
        cursor = conn.cursor()
        
        # Verificar database atual
        cursor.execute("SELECT current_database()")
        db = cursor.fetchone()
        print(f"✅ Conectado ao banco: {db[0]}")
        
        # Contar tabelas
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()
        print(f"📊 Total de tabelas: {table_count[0]}")
        
        # Verificar utilizacao_recurso
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'utilizacao_recurso'")
        ur_exists = cursor.fetchone()
        
        if ur_exists[0] > 0:
            print("✅ Tabela utilizacao_recurso existe")
            
            # Contar total de registros (sem WHERE)
            cursor.execute("SELECT COUNT(*) FROM utilizacao_recurso")
            total = cursor.fetchone()
            print(f"📈 Total de registros: {total[0]:,}")
            
            # Contar registros OCI
            cursor.execute("SELECT COUNT(*) FROM utilizacao_recurso WHERE cloudproviderid = 3")
            oci_total = cursor.fetchone()
            print(f"🔧 Registros OCI (cloudproviderid=3): {oci_total[0]:,}")
            
        else:
            print("❌ Tabela utilizacao_recurso não existe")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Diagnóstico Básico OCI")
    print("=" * 30)
    
    if simple_db_test():
        print("\n✅ Diagnóstico completado")
    else:
        print("\n❌ Diagnóstico falhou")

if __name__ == "__main__":
    main()
