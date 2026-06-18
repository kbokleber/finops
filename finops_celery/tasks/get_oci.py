import pytz
import oci
import csv
import psycopg
from psycopg.rows import dict_row
from psycopg import sql
import json
import datetime
from psycopg.types.json import Jsonb
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from finops_celery.celery import app
from finops_celery.helpers.descompactar_gzp_para_csv import transform_gz_to_dict
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.helpers.deletar_mes import deletar_mes
from finops_celery.helpers.gerencia_de_recurso import get_id_item
from finops_celery.tasks.up_date_resumo import update_tabela_resumo
import csv
import redis
from finops_celery.settings import config
import pytz


utc=pytz.UTC

def download_arquivo_oci(config: dict, reporting_namespace: str, reporting_bucket: str, nome_arquivo: str):
    """Realiza o download do arquivo da oci"""
    object_storage = oci.object_storage.ObjectStorageClient(config)
    object_details = object_storage.get_object(
        reporting_namespace, reporting_bucket, nome_arquivo)
    return object_details.data.content


def get_oci_tags(consumo: dict) -> dict:
    """Lista todas as tags do item de consumo"""
    tags = {}
    for key in consumo:
        if key.find('tags/') >= 0:
            tags[key] = consumo[key]
    return tags


def gravar_csv_consumo_oci_banco(consumo_csv: csv.DictReader, id_provedor: int, id_cliente: int, id_contrato: int, ano_referencia: str, mes_referencia: str):
    # Deduplicacao: deleta todos os registros do provedor/contrato/mes/ano
    # antes de inserir via COPY. Isso garante que reprocessamentos nao
    # gerem duplicatas. Mesma rotina usada por get_aws.py.
    deletar_mes(id_provedor, mes_referencia, ano_referencia, id_contrato)

    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    # Conexao Redis com autenticacao: Redis 6+ exige 'default' como user
    # quando so senha e fornecida. Usa o REDIS_URL centralizado do settings.
    from finops_celery.settings import REDIS_URL
    redis_con = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    # Insere em massa via COPY. Datas sao inseridas como string ISO
    # (a coluna eh DATE mas o cast automatico do psycopg funciona).
    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor, cloudproviderid ) FROM STDIN') as copy:
        for consumo in consumo_csv:
            id_recurso = get_id_item(sku=consumo['product/Description'],
                                     servico=consumo['product/service'],
                                     regiao=consumo['product/region'],
                                     tags=get_oci_tags(consumo),
                                     recurso=consumo['product/resourceId'],
                                     id_provedor=id_provedor,
                                     redis_con=redis_con
                                     )
            if datetime.datetime.fromisoformat(consumo['lineItem/intervalUsageStart']) >= datetime.datetime(2024, 1, 1, tzinfo=utc):
                copy.write_row([id_recurso, id_cliente, id_contrato, consumo['lineItem/intervalUsageStart'],
                           consumo['usage/billedQuantity'], consumo['cost/myCost'], consumo['lineItem/referenceNo'], id_provedor])

    cursor.execute(
        'update provedor_nuvem set jobs_restantes = jobs_restantes-1 where id_provedor = %s RETURNING jobs_restantes', (id_provedor,))
    print(cursor.fetchall())
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
    redis_con.close()

@app.task(bind=True)
def task_download_arquivos_gravar(self, config: dict, reporting_namespace: str, reporting_bucket: str, nome_arquivo: str, id_provedor: int, id_cliente: int, id_contrato: int, ano_referencia: str, mes_referencia: str):
    data_csv = transform_gz_to_dict(download_arquivo_oci(
        config, reporting_namespace, reporting_bucket, nome_arquivo))
    gravar_csv_consumo_oci_banco(
        data_csv, id_provedor, id_cliente, id_contrato, ano_referencia, mes_referencia)


@app.task(bind=True)
def update_oci(self, id_cliente: int, id_contrato: int, id_provedor: int, config_provedor, iso_date_time_min):
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    utc = pytz.UTC
    reporting_namespace = 'bling'

    object_storage = oci.object_storage.ObjectStorageClient(config_provedor)
    report_bucket_objects = oci.pagination.list_call_get_all_results(
        object_storage.list_objects, reporting_namespace, config_provedor['tenancy'], fields="timeCreated,timeModified,name")

    # hora_do_ultimo_update = datetime.datetime.fromisoformat(
    #     iso_date_time_min).replace(tzinfo=utc)

    for row in report_bucket_objects.data.objects:
        if row.name.rsplit('/', 1)[-2] == 'reports/cost-csv' and row.time_modified.replace(tzinfo=utc) > datetime.datetime.fromisoformat(iso_date_time_min).replace(tzinfo=utc):
            # Extrai ano/mes do time_modified do arquivo (formato 'YYYY-MM-DD...')
            # Usado por gravar_csv_consumo_oci_banco para deletar registros
            # do mesmo mes/ano antes de inserir (rotina de deduplicacao).
            ano_ref = row.time_modified.strftime('%Y')
            mes_ref = row.time_modified.strftime('%m')
            task_download_arquivos_gravar.apply_async(
                args=[config_provedor, reporting_namespace, config_provedor['tenancy'], row.name, id_provedor, id_cliente, id_contrato, ano_ref, mes_ref])
            cursor.execute(
                'update provedor_nuvem set jobs_restantes = jobs_restantes+1 where id_provedor = %s', (id_provedor,))
            
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()


@app.task(bind=True)
def task_verificar_provedores_oci_para_update(self):
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    ocis_precisam_de_update = cursor.execute("""select  pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato 
 where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
 and tipo = 'oci' and config_de_acesso is not null""").fetchall()
    for oci_para_update in ocis_precisam_de_update:
        if oci_para_update['datatime_ultimo_update'] is not None:
            date_iso_format = oci_para_update['datatime_ultimo_update'].isoformat(
            )
        else:
            date_iso_format = '1970-01-01'
        update_oci.apply_async(args=[oci_para_update['id_cliente'], oci_para_update['id_contrato'],
                               oci_para_update["id_provedor"], oci_para_update["config_de_acesso"], date_iso_format])
        cursor.execute("""update provedor_nuvem set datatime_ultimo_update = %s, datatime_proximo_update = %s where id_provedor = %s """,
                       (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(minutes=15), oci_para_update["id_provedor"]))

    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
