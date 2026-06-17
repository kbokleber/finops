#!/usr/bin/env python3
"""
Script para diagnosticar discrepâncias entre banco de dados e dashboard

NOTA: O dashboard agora está localizado em /root/finops/dashboard/app.py
Para iniciá-lo: cd /root/finops && python3 run_dashboard.py
"""
import psycopg2
import requests
import json
from datetime import datetime

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'svc_finops',
    'password': '<sua-senha-do-banco>',
    'dbname': 'finopsdatabase'
}

def consultar_banco():
    """Consulta direta ao banco usando a mesma query do dashboard"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Query exata do dashboard
        cursor.execute("""
            SELECT DATE(data) as dia, COUNT(*) as registros, 
                   SUM(custo_total) as custo_total
            FROM utilizacao_recurso 
            WHERE cloudproviderid = 3 AND data >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(data) ORDER BY dia DESC
            LIMIT 7
        """)
        
        dados = cursor.fetchall()
        conn.close()
        return dados
        
    except Exception as e:
        print(f"Erro ao consultar banco: {e}")
        return []

def consultar_dashboard():
    """Consulta a API do dashboard"""
    try:
        response = requests.get('http://localhost:5000/api/recent-data', timeout=10)
        if response.status_code == 200:
            return response.json().get('dados_dias', [])
        else:
            print(f"Erro na API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao consultar dashboard: {e}")
        return []

def main():
    print("=" * 60)
    print("DIAGNÓSTICO DETALHADO DE DISCREPÂNCIAS")
    print("=" * 60)
    print()
    
    # 1. Consultar banco diretamente
    print("1. CONSULTANDO BANCO DE DADOS DIRETAMENTE...")
    dados_banco = consultar_banco()
    
    if dados_banco:
        print("   Dados do banco (utilizacao_recurso):")
        for row in dados_banco:
            data, registros, custo = row
            print(f"   {data} | {registros:>6} registros | R$ {float(custo):>10.2f}")
    else:
        print("   ❌ Erro ao consultar banco!")
    
    print()
    
    # 2. Consultar dashboard via API
    print("2. CONSULTANDO DASHBOARD VIA API...")
    dados_dashboard = consultar_dashboard()
    
    if dados_dashboard:
        print("   Dados do dashboard (/api/recent-data):")
        for item in dados_dashboard:
            data = item['dia'][:10]  # Pegar só a data
            registros = item['registros']
            custo = float(item['custo_total'])
            print(f"   {data} | {registros:>6} registros | R$ {custo:>10.2f}")
    else:
        print("   ❌ Erro ao consultar dashboard!")
    
    print()
    
    # 3. Comparação detalhada
    if dados_banco and dados_dashboard:
        print("3. COMPARAÇÃO DETALHADA:")
        print("   " + "-" * 50)
        print("   Data       | Banco  | Dashboard | Diferença")
        print("   " + "-" * 50)
        
        # Converter dados do dashboard para dict
        dash_dict = {}
        for item in dados_dashboard:
            data_str = item['dia'][:10]
            dash_dict[data_str] = item['registros']
        
        diferenca_encontrada = False
        for row in dados_banco:
            data_banco = str(row[0])
            reg_banco = row[1]
            reg_dashboard = dash_dict.get(data_banco, 0)
            diferenca = reg_banco - reg_dashboard
            
            if diferenca != 0:
                status = f"❌ {diferenca:+d}"
                diferenca_encontrada = True
            else:
                status = "✅ OK"
            
            print(f"   {data_banco} | {reg_banco:>6} | {reg_dashboard:>9} | {status}")
        
        if not diferenca_encontrada:
            print("\n   ✅ TODOS OS DADOS ESTÃO IGUAIS!")
        else:
            print("\n   ❌ DISCREPÂNCIAS ENCONTRADAS!")
    
    print()
    
    # 4. Verificações adicionais
    print("4. VERIFICAÇÕES ADICIONAIS:")
    
    # Verificar se o dashboard está usando cache
    try:
        response = requests.get('http://localhost:5000/api/summary', timeout=5)
        if response.status_code == 200:
            summary = response.json()
            print(f"   Dashboard online: ✅")
            print(f"   Última atualização: {summary.get('ultima_atualizacao', 'N/A')}")
        else:
            print(f"   Dashboard com problemas: ❌ {response.status_code}")
    except:
        print("   Dashboard inacessível: ❌")
    
    # Verificar tabelas relacionadas
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar total de registros na tabela
        cursor.execute("SELECT COUNT(*) FROM utilizacao_recurso WHERE cloudproviderid = 3")
        total_registros = cursor.fetchone()[0]
        print(f"   Total registros OCI na tabela: {total_registros}")
        
        # Verificar data mais recente
        cursor.execute("SELECT MAX(data) FROM utilizacao_recurso WHERE cloudproviderid = 3")
        data_mais_recente = cursor.fetchone()[0]
        print(f"   Data mais recente: {data_mais_recente}")
        
        conn.close()
        
    except Exception as e:
        print(f"   Erro nas verificações: {e}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
