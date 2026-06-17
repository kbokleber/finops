from celery import Celery
from .settings import config
import urllib.parse
import os

database_password = urllib.parse.quote_plus(config.get('CONEXAO_DB_SENHA', ''))
database_name = urllib.parse.quote_plus(config.get('CONEXAO_DB_DATABASE', ''))
database_user = urllib.parse.quote_plus(config.get('CONEXAO_DB_USER', ''))

# Broker: prefere CELERY_BROKER_URL (env var) sobre o default hardcoded.
# Isso permite que o dashboard em prod consulte o mesmo broker que os workers.
broker_url = os.environ.get('CELERY_BROKER_URL') or 'amqp://guest:guest@rabbitmq:5672/'

app = Celery('finops',
            broker=broker_url,
            backend=f'db+postgresql://{database_user}:{database_password}@{config.get("CONEXAO_DB_URL", "")}/{database_name}',
            include=['finops_celery.tasks'])


# Optional configuration, see the application user guide.
# app.conf.update(
#     result_expires=3600,
# )


app.conf.beat_schedule = {
    'oci': {
        'task': 'finops_celery.tasks.get_oci.task_verificar_provedores_oci_para_update',
        'schedule': 900
    },
    'azure': {
        'task': 'finops_celery.tasks.get_azure.task_verificar_azure_para_atualizar',
        'schedule': 900
    },
    'aws': {
        'task': 'finops_celery.tasks.get_aws.task_verificar_aws_update',
        'schedule': 900
    },
    'gcp': {
        'task': 'finops_celery.tasks.get_gcp_bigquery.task_verificar_gcp_update',
        'schedule': 900
    },
    'update_resumo': {
        'task': 'finops_celery.tasks.up_date_resumo.update_tabela_resumo',
        'schedule': 7200
    },
}

app.conf.timezone = 'UTC'

app.conf.task_routes = {
    'finops_celery.tasks.get_oci.task_verificar_provedores_oci_para_update': {
        'queue': 'verifica_up_date'},
    'finops_celery.tasks.get_azure.task_verificar_azure_para_atualizar': {
        'queue': 'verifica_up_date'},
    'finops_celery.tasks.get_aws.task_verificar_aws_update': {
        'queue': 'verifica_up_date'},
    'finops_celery.tasks.get_gcp_bigquery.task_verificar_gcp_update': {
        'queue': 'verifica_up_date'},

    'finops_celery.tasks.get_oci.update_oci': {
        'queue': 'atualizar_nuvem'},
    'finops_celery.tasks.task_download_arquivos_gravar': {
        'queue': 'atualizar_nuvem'},
    'finops_celery.tasks.get_azure.task_atulizar_azure': {
        'queue': 'atualizar_nuvem'},
    'finops_celery.tasks.get_aws.task_atualizar_aws': {
        'queue': 'atualizar_nuvem'},
    'finops_celery.tasks.get_gcp_bigquery.task_atualizar_gcp': {
        'queue': 'atualizar_nuvem'},
    'finops_celery.tasks.up_date_resumo.update_tabela_resumo': {
        'queue': 'atualizar_nuvem'},
}


# @signals.worker_ready.connect
# def on_worker_init(**kargs):
#     sync_databases()
    


if __name__ == '__main__':
    app.start()
