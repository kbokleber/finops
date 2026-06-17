import requests
import datetime
from functools import lru_cache

@lru_cache(maxsize=512)
def get_valor_dolar_ptax(date: datetime.datetime):
    retorno =  requests.get(f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{date.strftime('%m-%d-%Y')}'&$top=100&$format=json&$select=cotacaoVenda")
    if retorno.status_code == 200 and len(retorno.json()['value']) > 0:
        return retorno.json()['value'][0]['cotacaoVenda']
    else:
        return get_valor_dolar_ptax((date+datetime.timedelta(days=-1)))
