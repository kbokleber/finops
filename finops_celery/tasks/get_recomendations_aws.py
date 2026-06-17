import boto3
import datetime
import pytz
import gzip
import io
import csv
from datetime import date, tzinfo
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.celery import app

session = boto3.Session(region_name='us-east-1')
client = boto3.client('cost-optimization-hub', region_name='us-east-1')





@app.task(bind=True)
def list_aws_configs(self):
    conexao_banco = ConexaoBancoDeDados()
    cursor = conexao_banco.get_cursor()
    aws_que_precisam_de_atualizacao = cursor.execute("""
                                                    select pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from 
                                                    provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato 
                                                    where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
                                                    and tipo = 'aws' and config_de_acesso is not null""").fetchall()
    print(aws_que_precisam_de_atualizacao)