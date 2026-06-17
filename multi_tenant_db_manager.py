#!/usr/bin/env python3
"""
Multi-Tenant Database Manager para FinOps
Gerencia conexões e isolamento de dados por cliente
"""

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import Dict, Optional, Any
from contextlib import contextmanager
import redis
from datetime import datetime, timedelta

class MultiTenantDatabaseManager:
    """
    Gerenciador de banco de dados multi-tenant
    Suporta isolamento por database (recomendado) ou por schema
    """
    
    def __init__(self, master_db_config: Dict[str, Any], redis_config: Dict[str, Any]):
        self.master_db_config = master_db_config
        self.tenant_pools: Dict[str, psycopg2.pool.ThreadedConnectionPool] = {}
        self.tenant_configs: Dict[str, Dict] = {}
        
        # Cache para configurações de tenant
        self.redis_client = redis.Redis(**redis_config)
        
        # Pool de conexões para o banco master
        self.master_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 10,
            **master_db_config
        )
        
        self.logger = logging.getLogger(__name__)
    
    def get_tenant_config(self, tenant_identifier: str) -> Optional[Dict]:
        """
        Busca configuração do tenant (com cache)
        """
        cache_key = f"tenant_config:{tenant_identifier}"
        
        # Tentar cache primeiro
        cached_config = self.redis_client.get(cache_key)
        if cached_config:
            return json.loads(cached_config)
        
        # Buscar no banco master
        with self.get_master_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, slug, database_name, settings
                    FROM tenants 
                    WHERE slug = %s OR id::text = %s
                    AND status = 'active'
                """, (tenant_identifier, tenant_identifier))
                
                result = cursor.fetchone()
                if result:
                    config = dict(result)
                    # Cache por 1 hora
                    self.redis_client.setex(cache_key, 3600, json.dumps(config, default=str))
                    return config
        
        return None
    
    @contextmanager
    def get_master_connection(self):
        """Context manager para conexão com banco master"""
        conn = self.master_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.master_pool.putconn(conn)
    
    @contextmanager
    def get_tenant_connection(self, tenant_id: str):
        """Context manager para conexão com banco do tenant"""
        tenant_config = self.get_tenant_config(tenant_id)
        if not tenant_config:
            raise ValueError(f"Tenant {tenant_id} não encontrado")
        
        # Inicializar pool se não existir
        if tenant_id not in self.tenant_pools:
            self._initialize_tenant_pool(tenant_id, tenant_config)
        
        pool = self.tenant_pools[tenant_id]
        conn = pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)
    
    def _initialize_tenant_pool(self, tenant_id: str, tenant_config: Dict):
        """Inicializa pool de conexões para um tenant"""
        db_config = self.master_db_config.copy()
        db_config['database'] = tenant_config['database_name']
        
        self.tenant_pools[tenant_id] = psycopg2.pool.ThreadedConnectionPool(
            1, 5,  # min e max conexões
            **db_config
        )
        
        self.logger.info(f"Pool inicializado para tenant {tenant_id}")
    
    def create_tenant(self, tenant_name: str, tenant_slug: str) -> str:
        """
        Cria um novo tenant com database isolado
        """
        tenant_id = self._generate_tenant_id()
        database_name = f"finops_{tenant_slug}"
        
        try:
            # Criar registro do tenant
            with self.get_master_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tenants (id, name, slug, database_name, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (tenant_id, tenant_name, tenant_slug, database_name, datetime.utcnow()))
            
            # Criar database do tenant
            self._create_tenant_database(database_name)
            
            # Aplicar schema inicial
            self._apply_tenant_schema(database_name)
            
            # Limpar cache
            self.redis_client.delete(f"tenant_config:{tenant_slug}")
            
            self.logger.info(f"Tenant {tenant_name} criado com sucesso")
            return tenant_id
            
        except Exception as e:
            self.logger.error(f"Erro ao criar tenant {tenant_name}: {e}")
            raise
    
    def _create_tenant_database(self, database_name: str):
        """Cria database para o tenant"""
        # Conexão direta para criar database (não pode usar transação)
        conn = psycopg2.connect(**self.master_db_config)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE "{database_name}"')
        finally:
            conn.close()
    
    def _apply_tenant_schema(self, database_name: str):
        """Aplica schema inicial no database do tenant"""
        db_config = self.master_db_config.copy()
        db_config['database'] = database_name
        
        conn = psycopg2.connect(**db_config)
        try:
            with conn.cursor() as cursor:
                # Criar schemas por provedor
                schemas = ['oci', 'aws', 'azure', 'gcp', 'hetzner', 'reports']
                for schema in schemas:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
                
                # Criar tabelas básicas
                self._create_tenant_tables(cursor)
                
            conn.commit()
        finally:
            conn.close()
    
    def _create_tenant_tables(self, cursor):
        """Cria tabelas básicas para o tenant"""
        
        # Tabela de configurações de provedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider_type VARCHAR(50) NOT NULL,
                provider_name VARCHAR(255) NOT NULL,
                credentials_encrypted TEXT NOT NULL,
                settings JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabelas de dados por provedor (exemplo OCI)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oci.cost_data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                date DATE NOT NULL,
                service_name VARCHAR(255),
                resource_id VARCHAR(255),
                compartment_id VARCHAR(255),
                cost DECIMAL(15,4) NOT NULL,
                currency VARCHAR(10) DEFAULT 'USD',
                tags JSONB DEFAULT '{}',
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_cost_date ON oci.cost_data(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_cost_service ON oci.cost_data(service_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_cost_compartment ON oci.cost_data(compartment_id)")
        
        # Tabela de resumos agregados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports.daily_summary (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                date DATE NOT NULL,
                provider VARCHAR(50) NOT NULL,
                total_cost DECIMAL(15,4) NOT NULL,
                currency VARCHAR(10) DEFAULT 'USD',
                breakdown JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, provider)
            )
        """)
    
    def _generate_tenant_id(self) -> str:
        """Gera ID único para tenant"""
        import uuid
        return str(uuid.uuid4())
    
    def get_tenant_providers(self, tenant_id: str) -> list:
        """Busca provedores configurados para um tenant"""
        with self.get_tenant_connection(tenant_id) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, provider_type, provider_name, settings, is_active
                    FROM provider_configs
                    WHERE is_active = TRUE
                    ORDER BY provider_type, provider_name
                """)
                return cursor.fetchall()
    
    def store_cost_data(self, tenant_id: str, provider: str, data: list):
        """
        Armazena dados de custo para um tenant/provedor específico
        """
        with self.get_tenant_connection(tenant_id) as conn:
            with conn.cursor() as cursor:
                for record in data:
                    cursor.execute(f"""
                        INSERT INTO {provider}.cost_data 
                        (date, service_name, resource_id, compartment_id, cost, currency, tags, raw_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        record['date'],
                        record['service_name'],
                        record['resource_id'],
                        record.get('compartment_id'),
                        record['cost'],
                        record.get('currency', 'USD'),
                        json.dumps(record.get('tags', {})),
                        json.dumps(record.get('raw_data', {}))
                    ))
    
    def get_cost_summary(self, tenant_id: str, date_from: str, date_to: str) -> Dict:
        """
        Busca resumo de custos para um tenant
        """
        with self.get_tenant_connection(tenant_id) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Buscar dados de todos os provedores
                providers = ['oci', 'aws', 'azure', 'gcp', 'hetzner']
                summary = {}
                
                for provider in providers:
                    cursor.execute(f"""
                        SELECT 
                            DATE(date) as date,
                            SUM(cost) as total_cost,
                            COUNT(*) as record_count
                        FROM {provider}.cost_data
                        WHERE date BETWEEN %s AND %s
                        GROUP BY DATE(date)
                        ORDER BY date
                    """, (date_from, date_to))
                    
                    summary[provider] = cursor.fetchall()
                
                return summary
    
    def cleanup_old_data(self, tenant_id: str, days_to_keep: int = 90):
        """
        Remove dados antigos para otimizar performance
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.get_tenant_connection(tenant_id) as conn:
            with conn.cursor() as cursor:
                providers = ['oci', 'aws', 'azure', 'gcp', 'hetzner']
                
                for provider in providers:
                    cursor.execute(f"""
                        DELETE FROM {provider}.cost_data
                        WHERE created_at < %s
                    """, (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    self.logger.info(f"Removidos {deleted_count} registros antigos do {provider} para tenant {tenant_id}")
    
    def close_all_connections(self):
        """Fecha todas as conexões"""
        if hasattr(self, 'master_pool'):
            self.master_pool.closeall()
        
        for pool in self.tenant_pools.values():
            pool.closeall()
        
        self.redis_client.close()


# Exemplo de uso
if __name__ == "__main__":
    # Configurações
    master_db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'finops_admin',
        'password': 'admin_password',
        'database': 'finops_master'
    }
    
    redis_config = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    
    # Inicializar manager
    db_manager = MultiTenantDatabaseManager(master_db_config, redis_config)
    
    try:
        # Criar tenant
        tenant_id = db_manager.create_tenant("Cliente ABC", "cliente_abc")
        print(f"Tenant criado: {tenant_id}")
        
        # Buscar configuração
        config = db_manager.get_tenant_config("cliente_abc")
        print(f"Configuração: {config}")
        
        # Armazenar dados de exemplo
        sample_data = [
            {
                'date': '2024-01-15',
                'service_name': 'Compute',
                'resource_id': 'instance-123',
                'compartment_id': 'comp-456',
                'cost': 150.75,
                'currency': 'USD',
                'tags': {'environment': 'production'},
                'raw_data': {'detailed_info': 'example'}
            }
        ]
        
        db_manager.store_cost_data(tenant_id, 'oci', sample_data)
        print("Dados armazenados com sucesso")
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        db_manager.close_all_connections()
