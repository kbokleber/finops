from psycopg.rows import dict_row
from psycopg import sql, ClientCursor
import psycopg
import hashlib
from finops_celery.settings import config


class ConexaoBancoDeDados():
    _host = config['CONEXAO_DB_URL']
    _port = int(config['CONEXAO_DB_PORT']
                if config['CONEXAO_DB_PORT'] else 5432)
    _user = config['CONEXAO_DB_USER']
    _password = config['CONEXAO_DB_SENHA']
    _database = config['CONEXAO_DB_DATABASE']
    _conector = None
    _cursor = None

    def __init__(self, autocommit=False):
        self._conector = psycopg.connect(dbname=self._database, user=self._user,
                                         password=self._password, host=self._host, port=self._port, row_factory=dict_row)
        self._conector.autocommit = autocommit

    def set_cursor(self):
        self._cursor = self._conector.cursor()

    def get_cursor(self) -> ClientCursor:
        if not self._cursor:
            self._cursor = self._conector.cursor()
        return self._cursor

    def commit(self):
        try:
            self._conector.commit()
        except Exception as e:
            print('erro ao commitar')
            print(e)
            self._conector.rollback()

    def close_cursor(self):
        self._cursor.close()

    def close_conection(self):
        self._conector.close()

    def close_all(self):
        self._cursor.close()
        self._conector.close()

def criar_hash():
    conexao_banco = ConexaoBancoDeDados()
    cursor = conexao_banco.get_cursor()
    cursor.execute('select * from recurso_nuvem')
    recursos = cursor.fetchall()
    for recurso in recursos:
        tuple_item = str((recurso['nome'],
                          recurso['id_provedor'],
                          recurso['tipo_recurso'],
                          str(recurso['data_bruta']),
                          recurso['regiao'],
                          recurso['recurso']))

        cursor.execute('update recurso_nuvem set hash =%s where id_recurso = %s', (int(
            hashlib.sha256(tuple_item.encode('utf-8')).hexdigest(), 16), recurso['id_recurso']))

    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection
