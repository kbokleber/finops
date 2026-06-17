from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.helpers.redis_database import create_recurso_redis
import json
from functools import lru_cache
import hashlib
import redis
from finops_celery.settings import config
from psycopg import sql


def get_id_item(sku: str, servico: str, regiao: str, tags: dict, recurso: str, id_provedor: int, redis_con= None, banco_con = None):
    """
    recurso -> (recurso)
    sku -> (nome)
    serviço -> (tipo)
    tags -> (data_bruta)
    região -> (região) 
    """
    close_redis_con = False
    close_banco_con = False
    
    if redis_con == None:
        redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379, db=0, decode_responses=True)
        close_redis_con = True

    
    item_tuple_str = str((sku,
                          id_provedor,
                          servico,
                          str(tags),
                          regiao,
                          recurso))
    hash_item = str(int(
        hashlib.sha256(item_tuple_str.encode('utf-8')).hexdigest(), 16))
    data = redis_con.get(hash_item)

    if data is None:
        if banco_con == None:
            banco_con = ConexaoBancoDeDados()
            close_banco_con = True

        banco_cur = banco_con.get_cursor()
        banco_cur.execute("""INSERT INTO recurso_nuvem (nome, id_provedor, tipo_recurso, custo_unitario, data_bruta, regiao, recurso, hash) select %s, %s, %s, %s, %s, %s, %s, %s
                                   WHERE NOT EXISTS (select 1 from recurso_nuvem where hash = %s ) RETURNING * """
                          ,( str(sku[:100]), id_provedor, servico, 0, json.dumps(tags), regiao, recurso, str(hash_item),str(hash_item)))
       
        banco_con.commit()
        retorno_banco = banco_cur.execute("select hash, id_recurso FROM recurso_nuvem WHERE hash = %s order by id_recurso limit 1", (hash_item,)).fetchall()
        banco_con.close_cursor()
        data = create_recurso_redis(retorno_banco[0], redis_con)
        
        if close_banco_con:
            banco_con.close_conection()
            
    if close_redis_con:
        redis_con.close()
    return data
