#!/usr/bin/env python3
import psycopg2
import os

# Configurações de conexão
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'finopsdatabase',
    'user': 'svc_finops',
    'password': '<sua-senha-do-banco>'
}

def verify_data():
    conn = None
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=== VERIFICAÇÃO FINAL DOS DADOS ===")
        
        # Verificar dados das datas específicas
        cursor.execute("""
            SELECT 
                DATE(data) as data,
                COUNT(*) as registros,
                ROUND(SUM(custo_total::numeric), 2) as custo_total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) BETWEEN '2025-09-15' AND '2025-09-20'
            GROUP BY DATE(data) 
            ORDER BY DATE(data);
        """)
        
        print("Data\t\tRegistros\tCusto Total")
        print("="*50)
        for row in cursor.fetchall():
            print(f"{row[0]}\t{row[1]}\t\t{row[2]}")
        
        # Verificar especificamente 16 e 17
        print("\n=== DETALHES DOS DIAS CORRIGIDOS ===")
        cursor.execute("""
            SELECT 
                DATE(data) as data,
                COUNT(*) as registros,
                ROUND(SUM(custo_total::numeric), 2) as custo_total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) IN ('2025-09-16', '2025-09-17')
            GROUP BY DATE(data) 
            ORDER BY DATE(data);
        """)
        
        for row in cursor.fetchall():
            print(f"✅ {row[0]}: {row[1]} registros (Custo: {row[2]})")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_data()