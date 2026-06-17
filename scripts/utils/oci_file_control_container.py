#!/usr/bin/env python3
"""
Módulo de controle de arquivos e registros OCI - Versão Container
Sistema robusto para evitar duplicações e controlar importações

Características:
- Controle por hash de arquivos e registros
- Rastreamento detalhado de status
- Métodos de recuperação e limpeza
- Logging detalhado
- Prevenção de duplicações
"""

import os
import sys
import hashlib
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import json
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports do sistema - adaptar para container
try:
    from finops_celery.helpers.conexao_banco import ConexaoBancoDeDados
except ImportError:
    logger.warning("Importação padrão falhou, tentando imports alternativos...")
    # Tentar imports alternativos para o container
    try:
        sys.path.insert(0, '/finops/finops_celery')
        from helpers.conexao_banco import ConexaoBancoDeDados
    except ImportError:
        logger.error("Não foi possível importar ConexaoBancoDeDados")
        ConexaoBancoDeDados = None


class FileStatus(Enum):
    """Estados possíveis de um arquivo OCI"""
    PENDING = "pending"           # Arquivo identificado, aguardando processamento
    PROCESSING = "processing"     # Arquivo sendo processado
    PROCESSED = "processed"       # Arquivo processado com sucesso
    ERROR = "error"              # Erro no processamento
    SKIPPED = "skipped"          # Arquivo ignorado (já processado anteriormente)
    DUPLICATE = "duplicate"      # Arquivo duplicado detectado


class RecordStatus(Enum):
    """Estados possíveis de um registro individual"""
    PENDING = "pending"          # Registro aguardando processamento
    PROCESSING = "processing"    # Registro sendo processado
    PROCESSED = "processed"      # Registro processado com sucesso
    ERROR = "error"             # Erro no processamento do registro
    DUPLICATE = "duplicate"     # Registro duplicado detectado


class OCIFileControlContainer:
    """
    Controle robusto de arquivos e registros OCI - Versão Container
    """
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        Inicializa o controle de arquivos OCI
        
        Args:
            db_config: Configuração do banco de dados (opcional)
        """
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'finopsdatabase',
            'user': 'svc_finops',
            'password': '<sua-senha-do-banco>'
        }
        
        logger.info("OCIFileControlContainer inicializado")
    
    def get_connection(self):
        """Obtém conexão com o banco de dados"""
        try:
            if ConexaoBancoDeDados:
                # Usar classe existente se disponível
                conexao = ConexaoBancoDeDados()
                conexao.set_cursor()
                return conexao.get_connection(), conexao.get_cursor()
            else:
                # Conexão direta com psycopg2
                conn = psycopg2.connect(**self.db_config)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                return conn, cursor
        except Exception as e:
            logger.error(f"Erro na conexão com banco: {e}")
            raise
    
    def create_control_tables(self):
        """Cria tabelas de controle se não existirem"""
        conn, cursor = self.get_connection()
        
        try:
            # Tabela de controle de arquivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_file_control (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(500) NOT NULL,
                    file_path VARCHAR(1000),
                    file_hash VARCHAR(64) NOT NULL,
                    file_size BIGINT,
                    file_modified TIMESTAMP,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    provider_id INTEGER,
                    client_id INTEGER,
                    contract_id INTEGER,
                    processing_started TIMESTAMP,
                    processing_finished TIMESTAMP,
                    records_total INTEGER DEFAULT 0,
                    records_processed INTEGER DEFAULT 0,
                    records_errors INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    UNIQUE(file_hash)
                );
            """)
            
            # Commit após primeira tabela
            conn.commit()
            logger.info("Tabela oci_file_control criada/verificada")
            
            # Tabela de controle de registros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_record_control (
                    id SERIAL PRIMARY KEY,
                    file_control_id INTEGER REFERENCES oci_file_control(id),
                    record_hash VARCHAR(64) NOT NULL,
                    line_number INTEGER,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    resource_id INTEGER,
                    interval_usage_start TIMESTAMP,
                    reference_no VARCHAR(100),
                    cost_value DECIMAL(15,6),
                    processing_started TIMESTAMP,
                    processing_finished TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_data JSONB,
                    UNIQUE(record_hash)
                );
            """)
            
            # Commit após segunda tabela
            conn.commit()
            logger.info("Tabela oci_record_control criada/verificada")
            
            # Criar índices
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_status ON oci_file_control(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_hash ON oci_file_control(file_hash);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_provider ON oci_file_control(provider_id, client_id, contract_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_status ON oci_record_control(status);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_hash ON oci_record_control(record_hash);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_file ON oci_record_control(file_control_id);")
                
                conn.commit()
                logger.info("Índices criados/verificados")
            except Exception as e:
                logger.warning(f"Erro ao criar índices (não crítico): {e}")
                # Não fazer rollback aqui, índices são opcionais
            
            logger.info("Tabelas de controle criadas/verificadas com sucesso")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calcula hash SHA-256 do conteúdo do arquivo"""
        return hashlib.sha256(file_content).hexdigest()
    
    def calculate_record_hash(self, record_data: Dict) -> str:
        """Calcula hash único para um registro"""
        # Criar string única baseada em campos críticos
        key_fields = [
            record_data.get('lineItem/referenceNo', ''),
            record_data.get('lineItem/intervalUsageStart', ''),
            record_data.get('product/resourceId', ''),
            record_data.get('usage/billedQuantity', ''),
            record_data.get('cost/myCost', '')
        ]
        
        record_string = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(record_string.encode('utf-8')).hexdigest()
    
    def register_file(self, file_name: str, file_content: bytes, 
                     provider_id: int, client_id: int, contract_id: int,
                     file_path: str = None, metadata: Dict = None) -> Tuple[int, bool]:
        """
        Registra um arquivo para processamento
        
        Returns:
            Tuple[file_id, is_new]: ID do arquivo e se é novo (True) ou duplicado (False)
        """
        conn, cursor = self.get_connection()
        file_hash = self.calculate_file_hash(file_content)
        
        try:
            # Verificar se arquivo já existe
            cursor.execute("""
                SELECT id, status FROM oci_file_control 
                WHERE file_hash = %s
            """, (file_hash,))
            
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Arquivo {file_name} já existe (ID: {existing['id']}, Status: {existing['status']})")
                return existing['id'], False
            
            # Registrar novo arquivo
            cursor.execute("""
                INSERT INTO oci_file_control 
                (file_name, file_path, file_hash, file_size, status, 
                 provider_id, client_id, contract_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (file_name, file_path, file_hash, len(file_content), 
                  FileStatus.PENDING.value, provider_id, client_id, contract_id,
                  json.dumps(metadata) if metadata else None))
            
            file_id = cursor.fetchone()['id']
            conn.commit()
            
            logger.info(f"Arquivo {file_name} registrado com ID: {file_id}")
            return file_id, True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao registrar arquivo: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def start_file_processing(self, file_id: int) -> bool:
        """Marca início do processamento de um arquivo"""
        conn, cursor = self.get_connection()
        
        try:
            cursor.execute("""
                UPDATE oci_file_control 
                SET status = %s, processing_started = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = %s
                RETURNING id
            """, (FileStatus.PROCESSING.value, file_id, FileStatus.PENDING.value))
            
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                logger.info(f"Iniciado processamento do arquivo ID: {file_id}")
                return True
            else:
                logger.warning(f"Não foi possível iniciar processamento do arquivo ID: {file_id}")
                return False
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao iniciar processamento: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def register_records_batch(self, file_id: int, records: List[Dict]) -> Dict[str, int]:
        """
        Registra lote de registros para processamento
        
        Returns:
            Dict com estatísticas: {'new': count, 'duplicate': count, 'error': count}
        """
        conn, cursor = self.get_connection()
        stats = {'new': 0, 'duplicate': 0, 'error': 0}
        
        try:
            for i, record in enumerate(records):
                try:
                    record_hash = self.calculate_record_hash(record)
                    
                    # Verificar se registro já existe
                    cursor.execute("""
                        SELECT id FROM oci_record_control 
                        WHERE record_hash = %s
                    """, (record_hash,))
                    
                    if cursor.fetchone():
                        stats['duplicate'] += 1
                        continue
                    
                    # Inserir novo registro
                    cursor.execute("""
                        INSERT INTO oci_record_control 
                        (file_control_id, record_hash, line_number, status,
                         interval_usage_start, reference_no, cost_value, record_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (file_id, record_hash, i + 1, RecordStatus.PENDING.value,
                          record.get('lineItem/intervalUsageStart'),
                          record.get('lineItem/referenceNo'),
                          record.get('cost/myCost'),
                          json.dumps(record)))
                    
                    stats['new'] += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao registrar registro {i}: {e}")
                    stats['error'] += 1
                    continue
            
            conn.commit()
            logger.info(f"Registros processados - Novos: {stats['new']}, Duplicados: {stats['duplicate']}, Erros: {stats['error']}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao registrar lote de registros: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        return stats
    
    def get_system_status(self) -> Dict:
        """Obtém status geral do sistema de controle"""
        conn, cursor = self.get_connection()
        
        try:
            # Status dos arquivos
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM oci_file_control 
                GROUP BY status
            """)
            file_stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Status dos registros
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM oci_record_control 
                GROUP BY status
            """)
            record_stats = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Estatísticas gerais
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_files,
                    SUM(records_total) as total_records,
                    SUM(records_processed) as processed_records,
                    SUM(records_errors) as error_records,
                    AVG(file_size) as avg_file_size
                FROM oci_file_control
            """)
            general_stats = cursor.fetchone()
            
            return {
                'file_status': file_stats,
                'record_status': record_stats,
                'general': dict(general_stats) if general_stats else {},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


# Alias para compatibilidade
OCIFileControl = OCIFileControlContainer
