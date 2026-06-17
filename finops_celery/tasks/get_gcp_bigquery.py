from finops_celery.celery import app
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from datetime import date, datetime, timezone, timedelta
import json
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from finops_celery.helpers.gerencia_de_recurso import get_id_item
from finops_celery.helpers.deletar_mes import deletar_mes
import pytz
from dateutil.relativedelta import relativedelta
from finops_celery.tasks.up_date_resumo import update_tabela_resumo
import redis
from finops_celery.settings import config

class GoogleCloudExport():
    __scopes_list: list = ["https://www.googleapis.com/auth/cloud-platform"]
    __credentials: Credentials = None
    __cliente: bigquery.Client = None

    def __init__(self, service_account_config: str, table_name: str):
        self.service_account_config = service_account_config
        self.table_name = table_name

    def set_credentials(self, force_update: bool):
        if self.__credentials is None or force_update:
            self.__credentials = Credentials.from_service_account_info(
                self.service_account_config, scopes=self.__scopes_list)

    def make_bigquery(self, data_de_pesquisa: str):
        self.set_credentials(True)
        self.__cliente = bigquery.Client(credentials=self.__credentials)
        query = f"select * from {self.table_name} where invoice.month = '{data_de_pesquisa}'"

        query_job = self.__cliente.query(query)  # , job_config=job_config)
        return query_job


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))


@app.task(bind=True)
def task_atualizar_gcp(self, provedor_id, id_contrato, id_cliente, config_acesso, date_iso_format: str):
    print('atualizando gcp')
    ano_mes_gcp = ''.join(date_iso_format.split('-')[:2])
    google_gcp = GoogleCloudExport(
        config_acesso, config_acesso['table'])
    query_job = google_gcp.make_bigquery(ano_mes_gcp)
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379, db=0, decode_responses=True)
    cursor.execute("""DELETE FROM utilizacao_recurso where id_utilizacao in (select ur.id_utilizacao from utilizacao_recurso ur 
                   join recurso_nuvem rn on ur.id_recurso = rn.id_recurso 
                   join provedor_nuvem pn on rn.id_provedor=pn.id_provedor where  pn.id_provedor = %s and 
                    extract (year from "data")  = %s and
                    extract (month from "data")  = %s )""", (provedor_id, date_iso_format.split('-')[0],date_iso_format.split('-')[1] ))
    
    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor, cloudproviderid ) FROM STDIN') as copy:
        for row in query_job:
            row_dict =  dict(row.items())
            
            id_recurso = get_id_item(sku=row_dict['sku']['description'][:50],
                                    servico=row_dict['service']['description'][:50],
                                    regiao=row_dict['location']['region'],
                                    tags=row_dict['labels'],
                                    recurso=row_dict['resource']['name'],
                                    id_provedor=provedor_id,
                                    redis_con = redis_con
                                    )
            copy.write_row([id_recurso, id_cliente, id_contrato, dict(row.items())['usage_start_time'],
                           dict(row.items())['usage']['amount'], float(dict(row.items())['cost']), None, provedor_id])
            
            
    cursor.execute('update provedor_nuvem set jobs_restantes = jobs_restantes-1 where id_provedor = %s', (provedor_id,))
    conexao_banco.commit()
    cursor.execute('select jobs_restantes from provedor_nuvem where id_provedor = %s', (provedor_id,))
    verificar = cursor.fetchone()
    print(verificar)
    if verificar['jobs_restantes'] == 0: update_tabela_resumo.apply_async()
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
    redis_con.close()


@app.task(bind=True)
def task_verificar_gcp_update(self):
    """essa função verifica se é necessário atualizar os dados do gcp"""
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    cursor.execute("""select pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
                                                                and tipo = 'gcp' and config_de_acesso is not null""")
    cursor_data = cursor.fetchall()
    print(cursor_data)
    for gcp in cursor_data:
        if gcp['datatime_ultimo_update'] is not None:
            date_start = gcp['datatime_ultimo_update']
        else:
            date_start = datetime(2020, 1, 1)

        while date_start <= datetime.now():
            task_atualizar_gcp.apply_async(args=[gcp['id_provedor'], gcp['id_contrato'],
                                                 gcp['id_cliente'],  gcp['config_de_acesso'], date_start.isoformat()])
            cursor.execute('update provedor_nuvem set jobs_restantes = jobs_restantes+1 where id_provedor = %s', (gcp['id_provedor'],))
            date_start += relativedelta(months=1)

        cursor.execute("""update provedor_nuvem set datatime_ultimo_update = %s, datatime_proximo_update = %s where id_provedor = %s """,
                       (datetime.now(), datetime.now() + timedelta(hours=2), gcp["id_provedor"]))
    conexao_banco.commit()
    conexao_banco.close_cursor()
  