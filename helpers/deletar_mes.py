from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados


def deletar_mes(id_provedor: int,  mes_para_deletar: str, ano_para_deletar: str, id_contrato: int):
    conexao_banco = ConexaoBancoDeDados()
    cursor = conexao_banco.get_cursor()
    cursor.execute("""delete from utilizacao_recurso ur where ur.id_utilizacao in (select ur.id_utilizacao  from utilizacao_recurso ur left join recurso_nuvem rn on ur.id_recurso = rn.id_recurso 
                               where rn.id_provedor = %s and 
                               extract('month' from "data") = %s and 
                               extract('year' from "data") = %s and
                               ur.id_contrato = %s)""",
                   (id_provedor, mes_para_deletar, ano_para_deletar,  id_contrato))
    conexao_banco.commit()
    conexao_banco.close_all()
