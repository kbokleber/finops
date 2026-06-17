import psycopg
from psycopg.rows import dict_row
from finops_celery.celery import app
from finops_celery.settings import config

@app.task(bind=True)
def update_tabela_resumo(self):
    _host = config['CONEXAO_DB_URL']
    _port = int(config['CONEXAO_DB_PORT'] if config['CONEXAO_DB_PORT'] else 5432)
    _user = config['CONEXAO_DB_USER']
    _password = config['CONEXAO_DB_SENHA']
    _database = config['CONEXAO_DB_DATABASE']
    
    conector = psycopg.connect(dbname=_database, user=_user, password=_password, host=_host, port=_port, row_factory=dict_row)
    conector.autocommit = True
    cursor = conector.cursor()
    
    cursor.execute('drop table resumo_soma_dia_mes_ano_recurso')

    cursor.execute("""create table resumo_soma_dia_mes_ano_recurso as
select utilizacao_recurso.cloudproviderid as cloudproviderid, utilizacao_recurso.id_recurso as id_recurso_resumo, 
extract(year from utilizacao_recurso."data") as ano, extract(month from	utilizacao_recurso."data") as mes,
extract(day from utilizacao_recurso."data") as dia,	SUM(utilizacao_recurso.custo_total) as total_custo
from utilizacao_recurso group by utilizacao_recurso.cloudproviderid, utilizacao_recurso.id_recurso,
extract(year from utilizacao_recurso."data"), extract(month from utilizacao_recurso."data"),
extract(day from utilizacao_recurso."data")""")

    cursor.execute('DROP table resumo_finops')
    
    cursor.execute("""CREATE TABLE resumo_finops AS
        SELECT
            rsm.ano,
            3 AS id_provedor,
            rsm.mes,
            rn.nome,
            rn.recurso,
            rn.regiao,
            rn.tipo_recurso,
            SUM(rsm.total_custo) AS total_custo
        FROM
            resumo_soma_dia_mes_ano_recurso rsm
        JOIN
            recurso_nuvem rn
            ON rn.id_recurso = rsm.id_recurso_resumo
        WHERE
            rn.id_provedor = 3
        GROUP BY
            rsm.ano,
            rsm.mes,
            rn.nome,
            rn.recurso,
            rn.regiao,
            rn.tipo_recurso""")

    cursor.close()
    conector.close()

