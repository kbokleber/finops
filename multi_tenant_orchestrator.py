#!/usr/bin/env python3
"""
Multi-Tenant Task Orchestrator
Gerencia tasks Celery para múltiplos clientes e provedores
"""

from celery import Celery, group, chord
from celery.schedules import crontab
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import redis
from multi_tenant_db_manager import MultiTenantDatabaseManager

# Configuração do Celery
app = Celery('finops_multi_tenant')

# Configurações
app.conf.update(
    broker_url='redis://localhost:6379/1',
    result_backend='redis://localhost:6379/2',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Roteamento por tenant
    task_routes={
        'finops.tasks.collect_oci_data': {'queue': 'oci_collection'},
        'finops.tasks.collect_aws_data': {'queue': 'aws_collection'},
        'finops.tasks.collect_azure_data': {'queue': 'azure_collection'},
        'finops.tasks.aggregate_tenant_data': {'queue': 'aggregation'},
    },
    
    # Auto-scaling por queue
    worker_autoscaler='celery.worker.autoscale:Autoscaler',
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Schedule dinâmico - será populado dinamicamente
app.conf.beat_schedule = {}

# Logger
logger = logging.getLogger(__name__)

# Gerenciador de banco de dados
db_manager = MultiTenantDatabaseManager(
    master_db_config={
        'host': 'localhost',
        'port': 5432,
        'user': 'finops_admin',
        'password': 'admin_password',
        'database': 'finops_master'
    },
    redis_config={
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
)

class TenantTaskOrchestrator:
    """
    Orquestrador de tasks por tenant
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=3)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def schedule_all_tenant_tasks(self):
        """
        Agenda tasks para todos os tenants ativos
        """
        try:
            tenants = self._get_active_tenants()
            
            for tenant in tenants:
                self.schedule_tenant_tasks(tenant['id'])
                
        except Exception as e:
            self.logger.error(f"Erro ao agendar tasks: {e}")
    
    def schedule_tenant_tasks(self, tenant_id: str):
        """
        Agenda tasks para um tenant específico
        """
        try:
            providers = db_manager.get_tenant_providers(tenant_id)
            
            # Criar grupo de tasks paralelas por provedor
            tasks = []
            
            for provider in providers:
                if provider['provider_type'] == 'oci':
                    tasks.append(collect_oci_data.s(tenant_id, provider['id']))
                elif provider['provider_type'] == 'aws':
                    tasks.append(collect_aws_data.s(tenant_id, provider['id']))
                elif provider['provider_type'] == 'azure':
                    tasks.append(collect_azure_data.s(tenant_id, provider['id']))
                elif provider['provider_type'] == 'gcp':
                    tasks.append(collect_gcp_data.s(tenant_id, provider['id']))
                elif provider['provider_type'] == 'hetzner':
                    tasks.append(collect_hetzner_data.s(tenant_id, provider['id']))
            
            # Executar coleta em paralelo e depois agregação
            if tasks:
                callback = aggregate_tenant_data.s(tenant_id)
                chord(tasks)(callback)
                
                self.logger.info(f"Tasks agendadas para tenant {tenant_id}: {len(tasks)} provedores")
            
        except Exception as e:
            self.logger.error(f"Erro ao agendar tasks para tenant {tenant_id}: {e}")
    
    def _get_active_tenants(self) -> List[Dict]:
        """Busca todos os tenants ativos"""
        with db_manager.get_master_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, slug, settings
                    FROM tenants
                    WHERE status = 'active'
                """)
                return cursor.fetchall()
    
    def update_dynamic_schedule(self):
        """
        Atualiza o schedule do Celery Beat dinamicamente
        """
        tenants = self._get_active_tenants()
        new_schedule = {}
        
        for tenant in tenants:
            tenant_settings = tenant.get('settings', {})
            collection_interval = tenant_settings.get('collection_interval', 900)  # 15 min default
            
            new_schedule[f'collect_data_tenant_{tenant["id"]}'] = {
                'task': 'finops.tasks.schedule_tenant_tasks',
                'schedule': collection_interval,
                'args': (tenant['id'],)
            }
        
        # Atualizar o schedule
        app.conf.beat_schedule = new_schedule
        
        # Salvar no Redis para persistência
        self.redis_client.set('beat_schedule', json.dumps(new_schedule, default=str))


# Instanciar orquestrador
orchestrator = TenantTaskOrchestrator()

# Tasks Celery

@app.task(bind=True, max_retries=3)
def collect_oci_data(self, tenant_id: str, provider_id: str):
    """
    Coleta dados do OCI para um tenant específico
    """
    try:
        from providers.oci_service import OCIMultiTenantService
        
        service = OCIMultiTenantService(tenant_id, provider_id, db_manager)
        
        # Definir range de datas (últimos 7 dias)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Coletar dados
        data = service.collect_cost_data(start_date, end_date)
        
        # Processar e armazenar
        processed_count = service.process_and_store(data)
        
        logger.info(f"OCI: {processed_count} registros processados para tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'provider': 'oci',
            'records_processed': processed_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta OCI para tenant {tenant_id}: {e}")
        
        # Retry com backoff exponencial
        self.retry(countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def collect_aws_data(self, tenant_id: str, provider_id: str):
    """
    Coleta dados do AWS para um tenant específico
    """
    try:
        from providers.aws_service import AWSMultiTenantService
        
        service = AWSMultiTenantService(tenant_id, provider_id, db_manager)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data = service.collect_cost_data(start_date, end_date)
        processed_count = service.process_and_store(data)
        
        logger.info(f"AWS: {processed_count} registros processados para tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'provider': 'aws',
            'records_processed': processed_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta AWS para tenant {tenant_id}: {e}")
        self.retry(countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def collect_azure_data(self, tenant_id: str, provider_id: str):
    """
    Coleta dados do Azure para um tenant específico
    """
    try:
        from providers.azure_service import AzureMultiTenantService
        
        service = AzureMultiTenantService(tenant_id, provider_id, db_manager)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data = service.collect_cost_data(start_date, end_date)
        processed_count = service.process_and_store(data)
        
        logger.info(f"Azure: {processed_count} registros processados para tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'provider': 'azure',
            'records_processed': processed_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta Azure para tenant {tenant_id}: {e}")
        self.retry(countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def collect_gcp_data(self, tenant_id: str, provider_id: str):
    """
    Coleta dados do GCP para um tenant específico
    """
    try:
        from providers.gcp_service import GCPMultiTenantService
        
        service = GCPMultiTenantService(tenant_id, provider_id, db_manager)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data = service.collect_cost_data(start_date, end_date)
        processed_count = service.process_and_store(data)
        
        logger.info(f"GCP: {processed_count} registros processados para tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'provider': 'gcp',
            'records_processed': processed_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta GCP para tenant {tenant_id}: {e}")
        self.retry(countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def collect_hetzner_data(self, tenant_id: str, provider_id: str):
    """
    Coleta dados do Hetzner para um tenant específico
    """
    try:
        from providers.hetzner_service import HetznerMultiTenantService
        
        service = HetznerMultiTenantService(tenant_id, provider_id, db_manager)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data = service.collect_cost_data(start_date, end_date)
        processed_count = service.process_and_store(data)
        
        logger.info(f"Hetzner: {processed_count} registros processados para tenant {tenant_id}")
        
        return {
            'tenant_id': tenant_id,
            'provider': 'hetzner',
            'records_processed': processed_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Erro na coleta Hetzner para tenant {tenant_id}: {e}")
        self.retry(countdown=60 * (2 ** self.request.retries))

@app.task
def aggregate_tenant_data(collection_results: List[Dict], tenant_id: str):
    """
    Agrega dados coletados de todos os provedores para um tenant
    """
    try:
        total_records = sum(result.get('records_processed', 0) for result in collection_results)
        
        # Calcular resumos diários
        from aggregators.daily_aggregator import DailyAggregator
        aggregator = DailyAggregator(tenant_id, db_manager)
        
        today = datetime.utcnow().date()
        aggregator.calculate_daily_summary(today)
        
        # Atualizar cache
        from cache.tenant_cache import TenantCacheManager
        cache_manager = TenantCacheManager(tenant_id)
        cache_manager.refresh_summary_cache()
        
        logger.info(f"Agregação concluída para tenant {tenant_id}: {total_records} registros totais")
        
        return {
            'tenant_id': tenant_id,
            'total_records': total_records,
            'providers_processed': len(collection_results),
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Erro na agregação para tenant {tenant_id}: {e}")
        raise

@app.task
def schedule_tenant_tasks(tenant_id: str):
    """
    Task que agenda a coleta para um tenant específico
    """
    orchestrator.schedule_tenant_tasks(tenant_id)

@app.task
def cleanup_old_data():
    """
    Task para limpeza de dados antigos de todos os tenants
    """
    try:
        tenants = orchestrator._get_active_tenants()
        
        for tenant in tenants:
            tenant_settings = tenant.get('settings', {})
            retention_days = tenant_settings.get('data_retention_days', 90)
            
            db_manager.cleanup_old_data(tenant['id'], retention_days)
            
        logger.info(f"Limpeza concluída para {len(tenants)} tenants")
        
    except Exception as e:
        logger.error(f"Erro na limpeza de dados: {e}")

@app.task
def health_check():
    """
    Verifica saúde de todos os tenants
    """
    try:
        tenants = orchestrator._get_active_tenants()
        health_status = {}
        
        for tenant in tenants:
            try:
                # Testar conexão com banco do tenant
                with db_manager.get_tenant_connection(tenant['id']) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                
                health_status[tenant['id']] = {
                    'status': 'healthy',
                    'last_check': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                health_status[tenant['id']] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
        
        # Salvar status no Redis
        orchestrator.redis_client.setex(
            'tenants_health_status', 
            300,  # 5 minutos
            json.dumps(health_status, default=str)
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise

# Schedule estático para tasks administrativas
app.conf.beat_schedule.update({
    'cleanup-old-data': {
        'task': 'finops.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Todo dia às 2h
    },
    'health-check': {
        'task': 'finops.tasks.health_check',
        'schedule': 300.0,  # A cada 5 minutos
    },
    'update-dynamic-schedule': {
        'task': 'finops.tasks.update_schedule',
        'schedule': 3600.0,  # A cada hora
    }
})

@app.task
def update_schedule():
    """Atualiza o schedule dinâmico"""
    orchestrator.update_dynamic_schedule()

if __name__ == '__main__':
    # Para desenvolvimento/teste
    app.start()
