"""Helper para gravar dados OCI apagando o dia (inline, sem abrir nova conexao)."""
import datetime
import pytz
from finops_celery.helpers.gerencia_de_recurso import get_id_item
from finops_celery.tasks.get_oci import get_oci_tags

utc = pytz.UTC


def gravar_deletando_dia_inline(cursor, redis_con, consumo_csv, id_provedor, id_cliente, id_contrato):
    """Faz DELETE-por-dia + COPY em uma unica conexao, sem abrir nova."""
    consumo_list = []
    dias_no_csv = set()
    for consumo in consumo_csv:
        consumo_list.append(consumo)
        data_iso = consumo.get('lineItem/intervalUsageStart', '')
        if data_iso and len(data_iso) >= 10:
            dias_no_csv.add(data_iso[:10])

    for dia in dias_no_csv:
        lock_key = f'oci-{id_provedor}-{id_contrato}-{dia}'
        cursor.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', (lock_key,))
        cursor.execute("""DELETE FROM utilizacao_recurso ur
                          WHERE ur.id_utilizacao IN (
                              SELECT ur2.id_utilizacao FROM utilizacao_recurso ur2
                              LEFT JOIN recurso_nuvem rn ON ur2.id_recurso = rn.id_recurso
                              WHERE rn.id_provedor = %s
                                AND ur2.data = %s
                                AND ur2.id_contrato = %s
                          )""",
                       (id_provedor, dia, id_contrato))

    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor, cloudproviderid ) FROM STDIN') as copy:
        for consumo in consumo_list:
            id_recurso = get_id_item(sku=consumo['product/Description'],
                                     servico=consumo['product/service'],
                                     regiao=consumo['product/region'],
                                     tags=get_oci_tags(consumo),
                                     recurso=consumo['product/resourceId'],
                                     id_provedor=id_provedor,
                                     redis_con=redis_con
                                     )
            if datetime.datetime.fromisoformat(consumo['lineItem/intervalUsageStart']) >= datetime.datetime(2024, 1, 1, tzinfo=utc):
                copy.write_row([id_recurso, id_cliente, id_contrato, consumo['lineItem/intervalUsageStart'],
                           consumo['usage/billedQuantity'], consumo['cost/myCost'], consumo['lineItem/referenceNo'], id_provedor])
