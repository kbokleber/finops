from finops_celery.celery import app  # , conexao_banco
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.helpers.deletar_mes import deletar_mes
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
import pytz
import datetime
import csv
from finops_celery.helpers.gerencia_de_recurso import get_id_item
import json
from celery.utils.log import get_task_logger
from finops_celery.tasks.up_date_resumo import update_tabela_resumo
import redis
from finops_celery.settings import config

logger = get_task_logger(__name__)


def gravar_no_banco_csv(csv_de_itens, id_provedor: int, id_cliente: int, id_contrato: int):
    logger.info(
        'Executando a gravação da ultilização no banco de dados para o id_provedor: ' + str(id_provedor))
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    print('gravando no banco')
    count = 0
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379,
                            db=0, decode_responses=True)
    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor,cloudproviderid ) FROM STDIN') as copy:
        for item_de_consumo in csv_de_itens:
            id_recurso = get_id_item(sku=item_de_consumo['ProductName'],
                                     servico=item_de_consumo['serviceFamily'],
                                     regiao=item_de_consumo['location'],
                                     tags=item_de_consumo['tags'],
                                     recurso=item_de_consumo['ResourceId'],
                                     id_provedor=id_provedor,
                                     redis_con=redis_con
                                     )
            copy.write_row([id_recurso, id_cliente, id_contrato, datetime.datetime.strptime(item_de_consumo['date'], '%m/%d/%Y'),
                           item_de_consumo['quantity'],
                           item_de_consumo['costInBillingCurrency'],
                           None, id_provedor])
            count += 1
            print(count)

    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
    redis_con.close()


def baixar_arquivos(container, blob_name):
    print('baixando ' + blob_name)
    download = container.download_blob(
        blob_name,  encoding='utf-8-sig', connection_timeout=100000).readall()
    return csv.DictReader(download.splitlines(), delimiter=',')


def get_container(config_de_acesso):
    default_credential = ClientSecretCredential(
        config_de_acesso['TENANT_ID'], config_de_acesso['CLIENT_ID'], config_de_acesso['CLIENT_SECRET'])
    blob_service_client = BlobServiceClient(
        config_de_acesso['account_url'], credential=default_credential)

    return blob_service_client.get_container_client(container=config_de_acesso['container'])


@app.task(bind=True)
def task_baixar_e_gravar(self, azure_cloud, nome):
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    container = get_container(azure_cloud['config_de_acesso'])
    csv_de_itens = baixar_arquivos(container, nome)
    gravar_no_banco_csv(
        csv_de_itens, azure_cloud['id_provedor'], azure_cloud['id_cliente'], azure_cloud['id_contrato'])
    cursor.execute('update provedor_nuvem set jobs_restantes = jobs_restantes-1 where id_provedor = %s',
                   (azure_cloud['id_provedor'],))
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()


@app.task(bind=True)
def task_atulizar_azure(self, azure_cloud: dict, data_para_update_iso: str):
    logger.info('Fazendo update da azure' + str(azure_cloud))
    utc = pytz.UTC
    data_minima = datetime.datetime.fromisoformat(
        data_para_update_iso).replace(tzinfo=utc)
    config_de_acesso = azure_cloud['config_de_acesso']
    container = get_container(config_de_acesso)
    blob_list = container.list_blobs()
    intervalo = {}
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    logger.info('listando os blobs' + str(azure_cloud))

    for blob in blob_list:
        file_name = blob.name
        if blob.last_modified > data_minima and (file_name.find('ic_billing') > 0 or file_name.find('daily_report') > 0):
            blob.last_modified
            split_result = file_name.split('/')
            try:
                if intervalo.get(split_result[2], None) is None:
                    intervalo |= {file_name.split('/')[2]: []}
                if blob.last_modified not in intervalo[file_name.split('/')[2]]:
                    intervalo[file_name.split('/')[2]].append(blob)
            except:
                pass
    logger.info(
        'Após listar os blobs com data superior ao ultimo update executando o download e salvamento ' + str(azure_cloud))
    print(intervalo)
    for key in intervalo:
        new_list = sorted(intervalo[key], key=lambda d: d.last_modified)
        print(new_list[-1].name)

        logger.info('Arquivos baixados executando o delete do mes ' +
                    str(azure_cloud) + ' ' + str(key))
        cursor.execute(f"""delete from utilizacao_recurso where id_utilizacao in ( select ur.id_utilizacao 
	                       from utilizacao_recurso ur join recurso_nuvem rn on ur.id_recurso = rn.id_recurso
                           join provedor_nuvem pn on rn.id_provedor=pn.id_provedor where  pn.id_provedor = {azure_cloud['id_provedor']} 
                           and extract(month from  ur."data") = {new_list[-1].last_modified.month} and extract(year from  ur."data") = {new_list[-1].last_modified.year})""")
        task_baixar_e_gravar.apply_async(args=[azure_cloud, new_list[-1].name])
        #cursor.execute('update provedor_nuvem set jobs_restantes = jobs_restantes+1 where id_provedor = %s',
#                       (azure_cloud['id_provedor'],))

    conexao_banco.commit()
    

    cursor.execute('select jobs_restantes from provedor_nuvem where id_provordor = %s', (azure_cloud['id_provedor'],))

    verificar = cursor.fetchone()

    if verificar['jobs_restantes'] == 0:
        update_tabela_resumo.apply_async()
    conexao_banco.close_conection()

@app.task(bind=True)
def task_verificar_azure_para_atualizar(self):
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    azure_que_precisam_de_atualizacao = cursor.execute("""select pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato 
                                                                where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
                                                                and tipo = 'azure' and config_de_acesso is not null""", ()).fetchall()
    for azure_cloud in azure_que_precisam_de_atualizacao:
        logger.info('reuisitando update da seguinte azure' + str(azure_cloud))
        if azure_cloud['datatime_ultimo_update'] is not None:
            date_iso_format = azure_cloud['datatime_ultimo_update'].isoformat()
        else:
            date_iso_format = '1970-01-01'
        task_atulizar_azure.apply_async(args=[azure_cloud, date_iso_format])
        cursor.execute('update provedor_nuvem set jobs_restantes = jobs_restantes+1 where id_provedor = %s',
                       (azure_cloud['id_provedor'],))
        cursor.execute("""update provedor_nuvem set datatime_ultimo_update = NOW() , datatime_proximo_update = (NOW() + interval '2 hours') where id_provedor= %s  """,
                       (azure_cloud['id_provedor'],))
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
