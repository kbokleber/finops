#!/bin/bash

# Script para testar manualmente o processamento OCI

echo "=== Testando processamento OCI ==="

# Executar dentro do container
docker exec -it finops-finops_worker_verifica-1 bash -c "
cd /finops_celery
export PYTHONPATH=/finops_celery:\$PYTHONPATH
python3 -c \"
import sys
sys.path.insert(0, '/finops_celery')
from helpers.conexao_banco import ConexaoBancoDeDados
from tasks.get_oci import task_verificar_provedores_oci_para_update
import asyncio

print('Iniciando processamento OCI...')

# Conectar ao banco
conexao = ConexaoBancoDeDados()
conexao.set_cursor()
cursor = conexao.get_cursor()

# Buscar provedores OCI
cursor.execute('''
    SELECT pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update 
    FROM provedor_nuvem pn 
    LEFT JOIN contrato ct ON pn.id_contrato = ct.id_contrato
    WHERE (pn.datatime_proximo_update <= NOW() OR pn.datatime_ultimo_update IS NULL)
    AND tipo = 'oci' AND config_de_acesso IS NOT NULL
''')

ocis_precisam_de_update = cursor.fetchall()
print(f'Encontrados {len(ocis_precisam_de_update)} provedores OCI para atualizar')

for oci_para_update in ocis_precisam_de_update:
    print(f'Processando provedor {oci_para_update[\\\"id_provedor\\\"]}...')
    
    # Importar e executar a tarefa
    from tasks.get_oci import update_oci
    
    if oci_para_update['datatime_ultimo_update'] is not None:
        date_iso_format = oci_para_update['datatime_ultimo_update'].isoformat()
    else:
        date_iso_format = '1970-01-01'
    
    print(f'Executando update_oci para cliente {oci_para_update[\\\"id_cliente\\\"]}...')
    
    try:
        # Executar a tarefa diretamente
        resultado = update_oci(
            id_cliente=oci_para_update['id_cliente'],
            id_contrato=oci_para_update['id_contrato'],
            id_provedor=oci_para_update['id_provedor'],
            config_provedor=oci_para_update['config_de_acesso'],
            iso_date_time_min=date_iso_format
        )
        print(f'✓ Processamento concluído para provedor {oci_para_update[\\\"id_provedor\\\"]}')
    except Exception as e:
        print(f'✗ Erro ao processar provedor {oci_para_update[\\\"id_provedor\\\"]}: {e}')
        import traceback
        traceback.print_exc()

print('Processamento finalizado!')
\"
"
