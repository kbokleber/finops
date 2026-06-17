"""
Versão melhorada do processamento OCI com controle robusto de duplicações
e rastreamento detalhado de processamento.
"""

import pytz
import oci
import csv
import psycopg
from psycopg.rows import dict_row
from psycopg import sql
import json
import datetime
from psycopg.types.json import Jsonb
from decimal import ROUND_DOWN, ROUND_UP, Decimal
from finops_celery.celery import app
from finops_celery.helpers.descompactar_gzp_para_csv import transform_gz_to_dict
from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
from finops_celery.helpers.gerencia_de_recurso import get_id_item
from finops_celery.tasks.up_date_resumo import update_tabela_resumo
from finops_celery.helpers.oci_file_control import (
    OCIFileController, FileProcessingInfo, FileStatus, RecordStatus
)
import csv
import redis
from finops_celery.settings import config
import pytz
import traceback
from typing import Optional, List, Dict


utc = pytz.UTC


def download_arquivo_oci(config: dict, reporting_namespace: str, reporting_bucket: str, nome_arquivo: str):
    """Realiza o download do arquivo da oci"""
    object_storage = oci.object_storage.ObjectStorageClient(config)
    object_details = object_storage.get_object(
        reporting_namespace, reporting_bucket, nome_arquivo)
    return object_details.data.content


def get_oci_tags(consumo: dict) -> dict:
    """Lista todas as tags do item de consumo"""
    tags = {}
    for key in consumo:
        if key.find('tags/') >= 0:
            tags[key] = consumo[key]
    return tags


def gravar_csv_consumo_oci_banco_controlado(consumo_csv: csv.DictReader, id_provedor: int, 
                                           id_cliente: int, id_contrato: int, 
                                           file_control_id: int, controller: OCIFileController):
    """
    Versão melhorada da gravação que usa controle de duplicação
    """
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379,
                            db=0, decode_responses=True)
    
    total_records = 0
    processed_records = 0
    duplicate_records = 0
    failed_records = 0
    
    print(f"🔄 Iniciando processamento controlado de registros...")
    
    try:
        for consumo in consumo_csv:
            total_records += 1
            
            try:
                # Criar hash do registro para controle de duplicação
                record_hash = controller.create_record_hash(consumo)
                
                # Verificar se já foi processado
                if controller.is_record_duplicate(record_hash):
                    duplicate_records += 1
                    controller.mark_record_duplicate(record_hash)
                    if total_records % 100 == 0:
                        print(f"   Processados {total_records} registros "
                              f"({processed_records} novos, {duplicate_records} duplicados)")
                    continue
                
                # Registrar record para controle
                controller.register_record_processing(file_control_id, consumo)
                
                # Verificar data mínima (só processar dados de 2024 em diante)
                usage_start_str = consumo.get('lineItem/intervalUsageStart', '')
                if usage_start_str:
                    usage_start = datetime.datetime.fromisoformat(usage_start_str.replace('Z', '+00:00'))
                    if usage_start < datetime.datetime(2024, 1, 1, tzinfo=utc):
                        print(f"⚠️  Registro muito antigo ignorado: {usage_start}")
                        continue
                
                # Obter ID do recurso
                id_recurso = get_id_item(
                    sku=consumo.get('product/Description', ''),
                    servico=consumo.get('product/service', ''),
                    regiao=consumo.get('product/region', ''),
                    tags=get_oci_tags(consumo),
                    recurso=consumo.get('product/resourceId', ''),
                    id_provedor=id_provedor,
                    redis_con=redis_con
                )
                
                # Inserir registro na tabela principal
                cursor.execute("""
                    INSERT INTO utilizacao_recurso 
                    (id_recurso, id_cliente, id_contrato, "data", 
                     quantidade_utilizada, custo_total, id_do_provedor, cloudproviderid)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_utilizacao
                """, [
                    id_recurso, 
                    id_cliente, 
                    id_contrato, 
                    usage_start_str,
                    consumo.get('usage/billedQuantity', 0), 
                    consumo.get('cost/myCost', 0), 
                    consumo.get('lineItem/referenceNo', ''), 
                    id_provedor
                ])
                
                id_utilizacao = cursor.fetchone()[0]
                
                # Marcar record como processado
                controller.mark_record_processed(record_hash, id_utilizacao)
                processed_records += 1
                
                # Log de progresso
                if total_records % 100 == 0:
                    print(f"   Processados {total_records} registros "
                          f"({processed_records} novos, {duplicate_records} duplicados)")
                
            except Exception as e:
                failed_records += 1
                error_msg = f"Erro no registro {total_records}: {str(e)}"
                print(f"✗ {error_msg}")
                
                # Marcar record como falhado
                try:
                    record_hash = controller.create_record_hash(consumo)
                    controller.mark_record_failed(record_hash, error_msg)
                except:
                    pass
                
                # Continuar processamento mesmo com erro em registro individual
                continue
        
        # Decrementar job counter
        cursor.execute(
            'UPDATE provedor_nuvem SET jobs_restantes = jobs_restantes-1 WHERE id_provedor = %s RETURNING jobs_restantes', 
            (id_provedor,)
        )
        job_result = cursor.fetchall()
        print(f"Jobs restantes: {job_result}")
        
        conexao_banco.commit()
        
        print(f"✓ Processamento concluído: {processed_records} processados, "
              f"{duplicate_records} duplicados, {failed_records} falharam de {total_records} total")
        
        return {
            'total': total_records,
            'processed': processed_records,
            'duplicated': duplicate_records,
            'failed': failed_records
        }
        
    except Exception as e:
        print(f"✗ Erro crítico no processamento: {e}")
        conexao_banco.rollback()
        raise
    finally:
        conexao_banco.close_cursor()
        conexao_banco.close_conection()
        redis_con.close()


@app.task(bind=True)
def task_download_arquivos_gravar_controlado(self, config: dict, reporting_namespace: str, 
                                            reporting_bucket: str, nome_arquivo: str, 
                                            id_provedor: int, id_cliente: int, 
                                            id_contrato: int, file_hash: str):
    """
    Versão melhorada da task que usa controle de duplicação
    """
    controller = OCIFileController()
    
    try:
        print(f"🔄 Iniciando download e processamento de {nome_arquivo}")
        
        # Marcar arquivo como sendo processado
        file_control_id = controller.start_file_processing(file_hash)
        if not file_control_id:
            raise Exception("Não foi possível iniciar processamento do arquivo")
        
        # Download e transformação
        raw_data = download_arquivo_oci(config, reporting_namespace, reporting_bucket, nome_arquivo)
        data_csv = transform_gz_to_dict(raw_data)
        
        # Processamento controlado
        stats = gravar_csv_consumo_oci_banco_controlado(
            data_csv, id_provedor, id_cliente, id_contrato, file_control_id, controller
        )
        
        # Marcar como concluído
        controller.finish_file_processing(file_hash, success=True)
        
        print(f"✅ Arquivo {nome_arquivo} processado com sucesso: {stats}")
        
    except Exception as e:
        error_msg = f"Erro no processamento de {nome_arquivo}: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        # Marcar como falhado
        controller.finish_file_processing(file_hash, success=False, error_message=error_msg)
        
        # Re-raise para que Celery registre como failed
        raise


@app.task(bind=True)
def update_oci_controlado(self, id_cliente: int, id_contrato: int, id_provedor: int, 
                         config_provedor, iso_date_time_min):
    """
    Versão melhorada do update_oci com controle de duplicação
    """
    controller = OCIFileController()
    
    # Inicializar tabelas de controle se necessário
    controller.init_control_tables()
    
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    utc = pytz.UTC
    reporting_namespace = 'bling'
    
    try:
        print(f"🔄 Iniciando update OCI controlado para provedor {id_provedor}")
        
        object_storage = oci.object_storage.ObjectStorageClient(config_provedor)
        report_bucket_objects = oci.pagination.list_call_get_all_results(
            object_storage.list_objects, 
            reporting_namespace, 
            config_provedor['tenancy'], 
            fields="timeCreated,timeModified,name,size"
        )
        
        hora_do_ultimo_update = datetime.datetime.fromisoformat(
            iso_date_time_min).replace(tzinfo=utc)
        
        files_to_process = []
        files_skipped = 0
        
        # Analisar arquivos disponíveis
        for row in report_bucket_objects.data.objects:
            # Verificar se é arquivo de custo CSV
            if not (row.name.rsplit('/', 1)[-2] == 'reports/cost-csv'):
                continue
                
            # Verificar se é mais novo que último update
            if not (row.time_modified.replace(tzinfo=utc) > hora_do_ultimo_update):
                continue
            
            # Criar informações do arquivo
            file_info = FileProcessingInfo(
                file_name=row.name,
                file_hash=controller.create_file_hash(
                    row.name, 
                    row.time_modified, 
                    getattr(row, 'size', 0)
                ),
                size_bytes=getattr(row, 'size', 0),
                modified_date=row.time_modified,
                status=FileStatus.PENDING,
                id_provedor=id_provedor,
                id_cliente=id_cliente,
                id_contrato=id_contrato
            )
            
            # Tentar registrar arquivo para processamento
            if controller.register_file_for_processing(file_info):
                files_to_process.append((row, file_info))
            else:
                files_skipped += 1
        
        print(f"📊 Encontrados {len(files_to_process)} arquivos para processar, "
              f"{files_skipped} ignorados (já processados)")
        
        # Processar arquivos
        for row, file_info in files_to_process:
            try:
                # Incrementar contador de jobs
                cursor.execute(
                    'UPDATE provedor_nuvem SET jobs_restantes = jobs_restantes+1 WHERE id_provedor = %s', 
                    (id_provedor,)
                )
                
                # Agendar processamento
                task_download_arquivos_gravar_controlado.apply_async(
                    args=[
                        config_provedor, 
                        reporting_namespace, 
                        config_provedor['tenancy'], 
                        row.name, 
                        id_provedor, 
                        id_cliente, 
                        id_contrato, 
                        file_info.file_hash
                    ]
                )
                
                print(f"✓ Agendado processamento de {row.name}")
                
            except Exception as e:
                print(f"✗ Erro ao agendar {row.name}: {e}")
                controller.finish_file_processing(
                    file_info.file_hash, 
                    success=False, 
                    error_message=str(e)
                )
        
        conexao_banco.commit()
        
        # Mostrar estatísticas
        stats = controller.get_processing_stats(id_provedor)
        print(f"📈 Estatísticas do provedor {id_provedor}: {stats}")
        
    except Exception as e:
        print(f"❌ Erro no update OCI: {e}")
        conexao_banco.rollback()
        raise
    finally:
        conexao_banco.close_cursor()
        conexao_banco.close_conection()


@app.task(bind=True)
def task_verificar_provedores_oci_para_update_controlado(self):
    """
    Versão melhorada da task de verificação com controle de duplicação
    """
    controller = OCIFileController()
    
    # Inicializar sistema de controle
    controller.init_control_tables()
    
    # Limpeza de registros antigos (opcional, roda a cada execução)
    controller.cleanup_old_records(days=30)
    
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    
    try:
        # Buscar provedores que precisam de atualização
        ocis_precisam_de_update = cursor.execute("""
            SELECT pn.id_provedor, ct.id_contrato, ct.id_cliente, 
                   pn.config_de_acesso, pn.datatime_ultimo_update 
            FROM provedor_nuvem pn 
            LEFT JOIN contrato ct ON pn.id_contrato = ct.id_contrato 
            WHERE (pn.datatime_proximo_update <= NOW() OR pn.datatime_ultimo_update IS NULL) 
            AND tipo = 'oci' AND config_de_acesso IS NOT NULL
        """).fetchall()
        
        print(f"🔍 Encontrados {len(ocis_precisam_de_update)} provedores OCI para verificar")
        
        for oci_para_update in ocis_precisam_de_update:
            try:
                # Determinar data mínima
                if oci_para_update['datatime_ultimo_update'] is not None:
                    date_iso_format = oci_para_update['datatime_ultimo_update'].isoformat()
                else:
                    date_iso_format = '1970-01-01'
                
                print(f"🔄 Processando provedor {oci_para_update['id_provedor']} "
                      f"(último update: {date_iso_format})")
                
                # Usar versão controlada
                update_oci_controlado.apply_async(args=[
                    oci_para_update['id_cliente'], 
                    oci_para_update['id_contrato'],
                    oci_para_update["id_provedor"], 
                    oci_para_update["config_de_acesso"], 
                    date_iso_format
                ])
                
                # Atualizar timestamps
                cursor.execute("""
                    UPDATE provedor_nuvem 
                    SET datatime_ultimo_update = %s, datatime_proximo_update = %s 
                    WHERE id_provedor = %s 
                """, (
                    datetime.datetime.now(), 
                    datetime.datetime.now() + datetime.timedelta(minutes=15), 
                    oci_para_update["id_provedor"]
                ))
                
            except Exception as e:
                print(f"✗ Erro ao processar provedor {oci_para_update['id_provedor']}: {e}")
                continue
        
        conexao_banco.commit()
        
        # Mostrar estatísticas globais
        stats = controller.get_processing_stats()
        print(f"📈 Estatísticas globais: {stats}")
        
    except Exception as e:
        print(f"❌ Erro na verificação de provedores: {e}")
        conexao_banco.rollback()
        raise
    finally:
        conexao_banco.close_cursor()
        conexao_banco.close_conection()


# Manter compatibilidade com funções antigas (deprecated)
def gravar_csv_consumo_oci_banco(consumo_csv: csv.DictReader, id_provedor: int, 
                                id_cliente: int, id_contrato: int):
    """DEPRECATED: Use gravar_csv_consumo_oci_banco_controlado"""
    print("⚠️  AVISO: Usando versão antiga sem controle de duplicação")
    # Implementação original mantida para compatibilidade
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    redis_con = redis.Redis(host=config['REDIS_DB_URL'], port=6379,
                            db=0, decode_responses=True)
    
    with cursor.copy('COPY utilizacao_recurso (id_recurso, id_cliente, id_contrato, "data", quantidade_utilizada, custo_total, id_do_provedor, cloudproviderid ) FROM STDIN') as copy:
        for consumo in consumo_csv:
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

    cursor.execute(
        'update provedor_nuvem set jobs_restantes = jobs_restantes-1 where id_provedor = %s RETURNING jobs_restantes', (id_provedor,))
    print(cursor.fetchall())
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
    redis_con.close()


@app.task(bind=True)
def task_download_arquivos_gravar(self, config: dict, reporting_namespace: str, 
                                 reporting_bucket: str, nome_arquivo: str, 
                                 id_provedor: int, id_cliente: int, id_contrato: int):
    """DEPRECATED: Use task_download_arquivos_gravar_controlado"""
    print("⚠️  AVISO: Usando versão antiga sem controle de duplicação")
    data_csv = transform_gz_to_dict(download_arquivo_oci(
        config, reporting_namespace, reporting_bucket, nome_arquivo))
    gravar_csv_consumo_oci_banco(
        data_csv, id_provedor, id_cliente, id_contrato)


@app.task(bind=True)
def update_oci(self, id_cliente: int, id_contrato: int, id_provedor: int, 
               config_provedor, iso_date_time_min):
    """DEPRECATED: Use update_oci_controlado"""
    print("⚠️  AVISO: Usando versão antiga sem controle de duplicação")
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    utc = pytz.UTC
    reporting_namespace = 'bling'

    object_storage = oci.object_storage.ObjectStorageClient(config_provedor)
    report_bucket_objects = oci.pagination.list_call_get_all_results(
        object_storage.list_objects, reporting_namespace, config_provedor['tenancy'], fields="timeCreated,timeModified,name")

    for row in report_bucket_objects.data.objects:
        if row.name.rsplit('/', 1)[-2] == 'reports/cost-csv' and row.time_modified.replace(tzinfo=utc) > datetime.datetime.fromisoformat(iso_date_time_min).replace(tzinfo=utc):
            task_download_arquivos_gravar.apply_async(
                args=[config_provedor, reporting_namespace, config_provedor['tenancy'], row.name, id_provedor, id_cliente, id_contrato])
            cursor.execute(
                'update provedor_nuvem set jobs_restantes = jobs_restantes+1 where id_provedor = %s', (id_provedor,))
            
    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()


@app.task(bind=True)
def task_verificar_provedores_oci_para_update(self):
    """DEPRECATED: Use task_verificar_provedores_oci_para_update_controlado"""
    print("⚠️  AVISO: Usando versão antiga sem controle de duplicação")
    conexao_banco = ConexaoBancoDeDados()
    conexao_banco.set_cursor()
    cursor = conexao_banco.get_cursor()
    ocis_precisam_de_update = cursor.execute("""select  pn.id_provedor, ct.id_contrato, ct.id_cliente, pn.config_de_acesso, pn.datatime_ultimo_update from provedor_nuvem pn left join contrato ct on pn.id_contrato = ct.id_contrato 
 where (pn.datatime_proximo_update <= NOW() or pn.datatime_ultimo_update is null) 
 and tipo = 'oci' and config_de_acesso is not null""").fetchall()
    for oci_para_update in ocis_precisam_de_update:
        if oci_para_update['datatime_ultimo_update'] is not None:
            date_iso_format = oci_para_update['datatime_ultimo_update'].isoformat(
            )
        else:
            date_iso_format = '1970-01-01'
        update_oci.apply_async(args=[oci_para_update['id_cliente'], oci_para_update['id_contrato'],
                               oci_para_update["id_provedor"], oci_para_update["config_de_acesso"], date_iso_format])
        cursor.execute("""update provedor_nuvem set datatime_ultimo_update = %s, datatime_proximo_update = %s where id_provedor = %s """,
                       (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(minutes=15), oci_para_update["id_provedor"]))

    conexao_banco.commit()
    conexao_banco.close_cursor()
    conexao_banco.close_conection()
