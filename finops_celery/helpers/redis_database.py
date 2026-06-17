
import redis
import redis_om
from redis_om import HashModel, Field, Migrator
from .conexao_banco import ConexaoBancoDeDados
from finops_celery.settings import config


def create_recurso_redis(recurso: dict, redis_con=None):
    fechar_redis_con = False
    if redis_con == None:
        redis_con = redis.Redis(host=config.get('REDIS_DB_URL', ''), port=6379,
                                db=0, decode_responses=True)
        fechar_redis_con = True
    redis_con.set(str(recurso['hash']), str(recurso['id_recurso']))
    retorno_do_redis = redis_con.get(recurso['hash'])
    if fechar_redis_con:
        redis_con.close()
    return retorno_do_redis


def sync_databases(executar_flush_redis=False):
    consexao_banco = ConexaoBancoDeDados()
    cursor = consexao_banco.get_cursor()
    cursor.execute('select id_recurso, hash from recurso_nuvem rn')
    recursos = cursor.fetchall()
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379,
                            db=0, decode_responses=True)

    if executar_flush_redis:
        redis_con.flushall()
    for recurso in recursos:
        create_recurso_redis(recurso, redis_con)
    redis_con.close()
