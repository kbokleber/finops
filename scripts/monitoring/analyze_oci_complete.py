#!/usr/bin/env python3
"""
Script para mostrar todas as colunas dos arquivos OCI
"""
import sys
import os
import json
import gzip
import csv
import io

# Adicionar o diretório finops_celery ao PYTHONPATH
sys.path.insert(0, '/finops_celery')

# Importar as dependências
import psycopg
from psycopg.rows import dict_row
import oci

# Conectar ao banco
conn = psycopg.connect(
    host='localhost',
    port=5432,
    user='svc_finops',
    password='<sua-senha-do-banco>',
    dbname='finopsdatabase',
    row_factory=dict_row
)

cursor = conn.cursor()

print("=== Análise completa dos campos OCI ===")

# Buscar configuração OCI
cursor.execute("SELECT config_de_acesso FROM provedor_nuvem WHERE tipo = 'oci'")
config_oci = cursor.fetchone()['config_de_acesso']

# Criar cliente OCI
object_storage = oci.object_storage.ObjectStorageClient(config_oci)
reporting_namespace = 'bling'

# Listar objetos recentes
print('Listando objetos OCI...')
objects = oci.pagination.list_call_get_all_results(
    object_storage.list_objects,
    reporting_namespace,
    config_oci['tenancy'],
    fields="timeCreated,timeModified,name",
    limit=1
)

if objects.data.objects:
    primeiro_objeto = objects.data.objects[0]
    print(f'\\nAnalisando arquivo: {primeiro_objeto.name}')
    
    # Fazer download
    object_details = object_storage.get_object(reporting_namespace, config_oci['tenancy'], primeiro_objeto.name)
    
    # Descompactar
    decompressed = gzip.decompress(object_details.data.content)
    csv_content = decompressed.decode('utf-8')
    
    # Ler CSV
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    
    print(f'Arquivo possui {len(rows)} registros')
    
    if rows:
        print('\\n=== TODAS AS COLUNAS DISPONÍVEIS ===')
        primeiro_registro = rows[0]
        
        # Mostrar todas as colunas organizadas
        colunas = list(primeiro_registro.keys())
        for i, coluna in enumerate(colunas):
            print(f'  {i+1:2d}. {coluna}: {primeiro_registro[coluna][:50]}...' if len(primeiro_registro[coluna]) > 50 else f'  {i+1:2d}. {coluna}: {primeiro_registro[coluna]}')
    
    print('\\n=== MAPEAMENTO SUGERIDO ===')
    print('Campo Original -> Campo FOCUS')
    if rows:
        primeiro_registro = rows[0]
        
        mapeamento = {
            'product/Description': 'ChargeDescription',
            'product/service': 'ServiceName', 
            'product/region': 'AvailabilityZone',
            'product/resourceId': 'ResourceId',
            'lineItem/intervalUsageStart': 'BillingPeriodStart',
            'usage/billedQuantity': 'PricingQuantity',
            'cost/myCost': 'BilledCost',
            'lineItem/referenceNo': 'InvoiceIssuer'
        }
        
        for campo_original, campo_focus in mapeamento.items():
            valor = primeiro_registro.get(campo_focus, 'N/A')
            print(f'  {campo_original} -> {campo_focus}: {valor}')

conn.close()
print('\\nAnálise concluída!')
