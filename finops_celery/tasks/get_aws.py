import pytz
import csv
import psycopg
from psycopg.rows import dict_row
from psycopg import sql
import json
import datetime
from psycopg.types.json import Jsonb
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from finops_celery.celery import app
from celery import Task
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.helpers.descompactar_gzp_para_csv import transform_gz_to_dict
from finops_celery.helpers.gerencia_de_recurso import get_id_item
import boto3
import io
from finops_celery.helpers.deletar_mes import deletar_mes
from finops_celery.tasks.up_date_resumo import update_tabela_resumo
import collections
from finops_celery.helpers.valor_dolar import get_valor_dolar_ptax
from dateutil.relativedelta import relativedelta
import redis
from finops_celery.settings import config

def get_aws_tags(consumo: dict) -> dict:
    tags = {}
    for key in consumo:
        if key.find('resource_tags_user') >= 0 or key.find('resourceTags') >= 0:
            tags[key] = consumo[key]
    return tags


@app.task(bind=True)
def gravar_csv_banco(self, id_provedor, id_cliente, id_contrato, client_aws, aws_access_key_id, aws_secret_access_key, bucket_name, key):
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    print('salvando os itens no banco')
    s3_client = boto3.client(client_aws, aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)
    csv_de_itens = baixar_arquivos_aws(s3_client, key, bucket_name)
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379,
                            db=0, decode_responses=True)
    count = 0
    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor, dolarprice, cloudproviderid ) FROM STDIN') as copy:
        for item in csv_de_itens:

            id_recurso = get_id_item(item['product/ProductName'], item['product/servicename'],
                                     item['product/region'], get_aws_tags(item), item['lineItem/ResourceId'], id_provedor, redis_con=redis_con)

            copy.write_row([id_recurso, 
                            id_cliente, 
                            id_contrato, 
                            item['lineItem/UsageEndDate'],
                            item['lineItem/UsageAmount'], 
                           float(item['lineItem/UnblendedCost']) * get_valor_dolar_ptax((datetime.datetime.fromisoformat(item['lineItem/UsageEndDate']) - datetime.timedelta(days=1))), 
                           None,
                            float(item['lineItem/UnblendedCost']), 
                            id_provedor])
            count +=1
            print(count)

    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
    redis_con.close()
    update_tabela_resumo.apply_async()


def baixar_arquivos_aws(s3_client, blob_name, bucket_name):
    file_stream = io.BytesIO()
    s3_client.download_fileobj(
        Bucket=bucket_name, Key=blob_name, Fileobj=file_stream)
    file_stream.seek(0)
    return transform_gz_to_dict(file_stream.read())


@app.task(bind=True)
def task_atualizar_aws(self, bucket_name, region_name, client_aws, id_provedor, date_iso_format, id_cliente, id_contrato, aws_access_key_id, aws_secret_access_key):
    s3_client = boto3.client(client_aws, aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)
    data_minima = datetime.datetime.fromisoformat(date_iso_format)
    paginator = s3_client.get_paginator('list_objects_v2')
    results = paginator.paginate(Bucket=bucket_name, Prefix='')
    intervalo = {}
    for page in results:
        for i in page['Contents']:
            file_name: str = i['Key']
            split_result = file_name.split('/')[-1].split('.')[-1]
            if split_result == 'gz':
                if intervalo.get(file_name.split('/')[2], None) is None:
                    intervalo |= {file_name.split('/')[2]: []}
                if datetime.datetime.strptime(file_name.split('/')[3], '%Y%m%dT%H%M%SZ') not in intervalo[file_name.split('/')[2]]:
                    intervalo[file_name.split(
                        '/')[2]].append(datetime.datetime.strptime(file_name.split('/')[3], '%Y%m%dT%H%M%SZ'))
    for key in intervalo:
        deletar_mes(id_provedor, key[:4], key[4:6], id_contrato)
        if sorted(intervalo[key])[-1] > data_minima:
            result = paginator.paginate(Bucket=bucket_name,
                                        Prefix=f'Report/CNU-Finops/{key}/{sorted(intervalo[key])[-1].strftime("%Y%m%dT%H%M%SZ")}')
            for page in result:
                for i in page['Contents']:
                    split_result = i['Key'].split('/')[-1].split('.')[-1]
                    if split_result == 'gz':
                        gravar_csv_banco.apply_async(
                            args=[id_provedor, id_cliente, id_contrato, client_aws, aws_access_key_id, aws_secret_access_key, bucket_name, i['Key']])


@app.task(bind=True)
def task_verificar_aws_update(self: Task):
    self.update_state(state="PROGRESS", meta={
                      "message": "inicio da verificação oci"})
    conexao_banco = ConexaoBancoDeDados()
    cursor = conexao_banco.get_cursor()
    self.update_state(state="PROGRESS", meta={
                      "message": "coletando os dados "})
    aws_que_precisam_de_atualizacao = cursor.execute("""
                                                     select pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato 
                                                     where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
                                                     and tipo = 'aws' and config_de_acesso is not null""").fetchall()

    for aws_para_atulizar in aws_que_precisam_de_atualizacao:
        self.update_state(state="PROGRESS", meta={
                          "message": f"criando task de update para {aws_para_atulizar['id_provedor']}"})
        if aws_para_atulizar['datatime_ultimo_update'] is not None:
            date_iso_format = aws_para_atulizar['datatime_ultimo_update'].isoformat(
            )
        else:
            date_iso_format = '2010-01-01'
        print(aws_para_atulizar)
        task_atualizar_aws.apply_async(args=[aws_para_atulizar['config_de_acesso']['bucket'], aws_para_atulizar['config_de_acesso']['region_name'],
                                       aws_para_atulizar['config_de_acesso']['client'], aws_para_atulizar['id_provedor'], date_iso_format, aws_para_atulizar['id_cliente'], aws_para_atulizar['id_contrato'],  aws_para_atulizar['config_de_acesso']['aws_access_key_id'],  aws_para_atulizar['config_de_acesso']['aws_secret_access_key']])
        cursor.execute(""" update provedor_nuvem set datatime_ultimo_update = %s, datatime_proximo_update = %s where id_provedor = %s """,
                       (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(hours=2), aws_para_atulizar["id_provedor"]))
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
