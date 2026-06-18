from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados


def deletar_dia(id_provedor: int, data_para_deletar: str, id_contrato: int):
    """Deleta registros de utilizacao_recurso para um provedor/contrato/data
    especificos. Usado pelos providers (ex: OCI) cujos arquivos CSV contem
    dados de UM DIA especifico, dividido em varios arquivos complementares.

    O deletar_mes (mensal) nao funciona para esses casos porque cada arquivo
    do mesmo dia sobrescreve os dados dos arquivos anteriores, deixando
    apenas o ultimo arquivo processado no banco.

    Argumentos:
        id_provedor: ID do provedor (ex: 3 para OCI)
        data_para_deletar: data no formato 'YYYY-MM-DD'
        id_contrato: ID do contrato
    """
    conexao_banco = ConexaoBancoDeDados()
    cursor = conexao_banco.get_cursor()
    cursor.execute("""delete from utilizacao_recurso ur where ur.id_utilizacao in (
                       select ur.id_utilizacao from utilizacao_recurso ur
                       left join recurso_nuvem rn on ur.id_recurso = rn.id_recurso
                       where rn.id_provedor = %s
                       and ur.data = %s
                       and ur.id_contrato = %s
                   )""",
                   (id_provedor, data_para_deletar, id_contrato))
    conexao_banco.commit()
    conexao_banco.close_all()
