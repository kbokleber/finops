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

def remove_duplicates():
    conn = None
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=== VERIFICANDO DUPLICATAS ===")
        
        # Verificar duplicatas
        cursor.execute("""
            SELECT 
                DATE(data) as data,
                COUNT(*) as total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) BETWEEN '2025-09-15' AND '2025-09-20'
            GROUP BY DATE(data) 
            ORDER BY DATE(data);
        """)
        
        for row in cursor.fetchall():
            print(f"Data: {row[0]} - Total: {row[1]}")
        
        print("\n=== REMOVENDO DUPLICATAS 16/09 ===")
        
        # Remover duplicatas do dia 16/09
        cursor.execute("""
            DELETE FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) = '2025-09-16'
            AND id_utilizacao NOT IN (
                SELECT MIN(id_utilizacao)
                FROM utilizacao_recurso 
                WHERE cloudproviderid = 3 
                AND DATE(data) = '2025-09-16'
                GROUP BY id_recurso, quantidade_utilizada, custo_total, data, id_do_provedor
            );
        """)
        
        affected_16 = cursor.rowcount
        print(f"Removidos {affected_16} registros duplicados do dia 16/09")
        
        print("\n=== REMOVENDO DUPLICATAS 17/09 ===")
        
        # Remover duplicatas do dia 17/09
        cursor.execute("""
            DELETE FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) = '2025-09-17'
            AND id_utilizacao NOT IN (
                SELECT MIN(id_utilizacao)
                FROM utilizacao_recurso 
                WHERE cloudproviderid = 3 
                AND DATE(data) = '2025-09-17'
                GROUP BY id_recurso, quantidade_utilizada, custo_total, data, id_do_provedor
            );
        """)
        
        affected_17 = cursor.rowcount
        print(f"Removidos {affected_17} registros duplicados do dia 17/09")
        
        # Confirmar as mudanças
        conn.commit()
        
        print("\n=== RESULTADO APÓS LIMPEZA ===")
        
        # Verificar resultado final
        cursor.execute("""
            SELECT 
                DATE(data) as data,
                COUNT(*) as total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 
            AND DATE(data) BETWEEN '2025-09-15' AND '2025-09-20'
            GROUP BY DATE(data) 
            ORDER BY DATE(data);
        """)
        
        for row in cursor.fetchall():
            print(f"Data: {row[0]} - Total: {row[1]}")
        
        cursor.close()
        print("\n✅ Limpeza de duplicatas concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        if conn:
            conn.rollback()
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    remove_duplicates()