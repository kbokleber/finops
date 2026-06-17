#!/usr/bin/env python3
import psycopg2
from datetime import datetime, date

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'svc_finops',
    'password': '<sua-senha-do-banco>',
    'dbname': 'finopsdatabase'
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=== VERIFICAÇÃO DE DISCREPÂNCIA DOS DADOS ===")
        print()
        
        # Dados informados pelo usuário
        seus_dados = [
            ('2025-08-03', 2460),
            ('2025-08-02', 7382),
            ('2025-08-01', 7400),
            ('2025-07-31', 7387),
            ('2025-07-30', 7390),
            ('2025-07-29', 7381),
            ('2025-07-28', 7382),
            ('2025-07-27', 7381),
            ('2025-07-26', 7382)
        ]
        
        print("1. DADOS INFORMADOS PELO USUÁRIO:")
        for data, registros in seus_dados:
            print(f"   {data} | {registros} registros")
        print()
        
        # Verificar na tabela utilizacao_recurso (usada pelo dashboard)
        print("2. DADOS DA TABELA utilizacao_recurso (DASHBOARD):")
        cursor.execute("""
            SELECT DATE(data) as dia, COUNT(*) as registros, 
                   SUM(custo_total) as custo_total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 AND data >= '2025-07-26' AND data <= '2025-08-03'
            GROUP BY DATE(data) ORDER BY dia DESC;
        """)
        dados_dashboard = cursor.fetchall()
        for row in dados_dashboard:
            print(f"   {row[0]} | {row[1]} registros | R$ {float(row[2]):.2f}")
        print()
        
        # Verificar na tabela oci_itens (dados brutos)
        print("3. DADOS DA TABELA oci_itens (DADOS BRUTOS):")
        cursor.execute("""
            SELECT DATE(usage_start_time) as data, COUNT(*) as registros
            FROM oci_itens 
            WHERE DATE(usage_start_time) >= '2025-07-26' 
              AND DATE(usage_start_time) <= '2025-08-03'
            GROUP BY DATE(usage_start_time) ORDER BY data DESC;
        """)
        dados_oci = cursor.fetchall()
        for row in dados_oci:
            print(f"   {row[0]} | {row[1]} registros")
        print()
        
        # Comparação
        print("4. ANÁLISE DA DISCREPÂNCIA:")
        
        # Criar dicionários para comparação
        seus_dados_dict = {data: registros for data, registros in seus_dados}
        dashboard_dict = {str(row[0]): row[1] for row in dados_dashboard}
        oci_dict = {str(row[0]): row[1] for row in dados_oci}
        
        print("   Data       | Seus Dados | Dashboard | OCI_Itens | Status")
        print("   " + "-"*60)
        
        for data in sorted(seus_dados_dict.keys(), reverse=True):
            seus = seus_dados_dict.get(data, 0)
            dash = dashboard_dict.get(data, 0)
            oci = oci_dict.get(data, 0)
            
            if seus == oci and oci != dash:
                status = "❌ Dashboard diverge"
            elif seus == dash and dash != oci:
                status = "❌ OCI diverge"
            elif seus == dash == oci:
                status = "✅ Dados corretos"
            else:
                status = "❌ Múltiplas divergências"
            
            print(f"   {data} | {seus:>9} | {dash:>9} | {oci:>9} | {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
