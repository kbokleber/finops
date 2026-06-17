#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório finops_celery ao PYTHONPATH
sys.path.insert(0, '/finops_celery')

# Importar as dependências
import psycopg
from psycopg.rows import dict_row
from datetime import datetime

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

# Buscar provedores OCI que precisam ser atualizados
cursor.execute("""
    SELECT pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update
    FROM provedor_nuvem pn 
    LEFT JOIN contrato ct ON pn.id_contrato = ct.id_contrato
    WHERE (pn.datatime_proximo_update <= NOW() OR pn.datatime_ultimo_update IS NULL)
    AND tipo = 'oci' AND config_de_acesso IS NOT NULL
""")

ocis_precisam_de_update = cursor.fetchall()
print(f'Encontrados {len(ocis_precisam_de_update)} provedores OCI para atualizar')

for oci_para_update in ocis_precisam_de_update:
    print(f'Processando provedor {oci_para_update["id_provedor"]}...')
    
    # Testar conectividade com OCI
    try:
        import oci
        
        config_oci = oci_para_update['config_de_acesso']
        
        # Criar cliente OCI
        object_storage = oci.object_storage.ObjectStorageClient(config_oci)
        
        # Testar listagem de objetos
        reporting_namespace = 'bling'
        
        print(f'Testando conectividade com OCI...')
        print(f'Tenancy: {config_oci["tenancy"]}')
        print(f'Region: {config_oci["region"]}')
        
        # Listar objetos
        objects = oci.pagination.list_call_get_all_results(
            object_storage.list_objects,
            reporting_namespace,
            config_oci['tenancy'],
            fields="timeCreated,timeModified,name",
            limit=10  # Limitar para teste
        )
        
        print(f'✓ Conectividade OCI OK - Encontrados {len(objects.data.objects)} objetos')
        
        # Mostrar alguns objetos para debug
        for i, obj in enumerate(objects.data.objects[:5]):
            print(f'  - {obj.name} (modificado: {obj.time_modified})')
            
    except Exception as e:
        print(f'✗ Erro ao conectar com OCI: {e}')
        import traceback
        traceback.print_exc()

conn.close()
print('Teste finalizado!')
