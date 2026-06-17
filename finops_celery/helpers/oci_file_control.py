"""
Sistema de Controle de Importação de Arquivos OCI

Este módulo implementa um controle robusto para evitar duplicações e garantir 
o processamento correto de cada arquivo e registro OCI.

Funcionalidades:
- Controle de estado de processamento de arquivos
- Prevenção de duplicações
- Log detalhado de processamento
- Recuperação automática em caso de falhas
- Rastreamento individual de registros
"""

import hashlib
import json
import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pytz
import sys
import os

# Adicionar paths necessários
sys.path.insert(0, '/root/finops')
sys.path.insert(0, '/root/finops/helpers')

from helpers.conexao_banco import ConexaoBancoDeDados


class FileStatus(Enum):
    """Estados possíveis de um arquivo OCI"""
    PENDING = "pending"           # Arquivo identificado, aguardando processamento
    PROCESSING = "processing"     # Arquivo sendo processado
    COMPLETED = "completed"       # Arquivo processado com sucesso
    FAILED = "failed"            # Arquivo falhou no processamento
    SKIPPED = "skipped"          # Arquivo ignorado (duplicado, muito antigo, etc.)


class RecordStatus(Enum):
    """Estados possíveis de um registro individual"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


@dataclass
class FileProcessingInfo:
    """Informações sobre o processamento de um arquivo"""
    file_name: str
    file_hash: str
    size_bytes: int
    modified_date: datetime.datetime
    status: FileStatus
    id_provedor: int
    id_cliente: int
    id_contrato: int
    records_total: int = 0
    records_processed: int = 0
    records_failed: int = 0
    records_duplicated: int = 0
    processing_start: Optional[datetime.datetime] = None
    processing_end: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class OCIFileController:
    """Controlador para gerenciar importação de arquivos OCI"""
    
    def __init__(self):
        self.utc = pytz.UTC
        
    def create_file_hash(self, file_name: str, modified_date: datetime.datetime, 
                        size_bytes: int = 0) -> str:
        """Cria hash único para identificar um arquivo"""
        unique_string = f"{file_name}_{modified_date.isoformat()}_{size_bytes}"
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
    
    def create_record_hash(self, record_data: dict) -> str:
        """Cria hash único para identificar um registro individual"""
        # Usar campos únicos do registro OCI para criar hash
        key_fields = [
            record_data.get('lineItem/referenceNo', ''),
            record_data.get('product/resourceId', ''),
            record_data.get('lineItem/intervalUsageStart', ''),
            record_data.get('lineItem/intervalUsageEnd', ''),
            record_data.get('usage/billedQuantity', ''),
            record_data.get('cost/myCost', '')
        ]
        unique_string = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
    
    def init_control_tables(self):
        """Inicializa as tabelas de controle se não existirem"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            # Tabela de controle de arquivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_file_control (
                    id SERIAL PRIMARY KEY,
                    file_name VARCHAR(500) NOT NULL,
                    file_hash VARCHAR(64) UNIQUE NOT NULL,
                    size_bytes BIGINT DEFAULT 0,
                    modified_date TIMESTAMPTZ NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    id_provedor INTEGER NOT NULL,
                    id_cliente INTEGER NOT NULL,
                    id_contrato INTEGER NOT NULL,
                    records_total INTEGER DEFAULT 0,
                    records_processed INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    records_duplicated INTEGER DEFAULT 0,
                    processing_start TIMESTAMPTZ,
                    processing_end TIMESTAMPTZ,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Tabela de controle de registros individuais
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_record_control (
                    id SERIAL PRIMARY KEY,
                    file_control_id INTEGER REFERENCES oci_file_control(id) ON DELETE CASCADE,
                    record_hash VARCHAR(64) NOT NULL,
                    line_item_reference VARCHAR(255),
                    resource_id VARCHAR(255),
                    usage_start TIMESTAMPTZ,
                    cost_amount DECIMAL(15,6),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    id_utilizacao_recurso INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(record_hash)
                )
            """)
            
            # Índices para performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_oci_file_control_hash 
                ON oci_file_control(file_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_oci_file_control_status 
                ON oci_file_control(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_oci_file_control_provedor 
                ON oci_file_control(id_provedor, status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_oci_record_control_hash 
                ON oci_record_control(record_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_oci_record_control_status 
                ON oci_record_control(status)
            """)
            
            conexao.commit()
            print("✓ Tabelas de controle OCI inicializadas com sucesso")
            
        except Exception as e:
            print(f"✗ Erro ao inicializar tabelas de controle: {e}")
            conexao.rollback()
            raise
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def register_file_for_processing(self, file_info: FileProcessingInfo) -> bool:
        """Registra um arquivo para processamento, evitando duplicatas"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            # Verificar se arquivo já foi processado
            cursor.execute("""
                SELECT id, status FROM oci_file_control 
                WHERE file_hash = %s
            """, (file_info.file_hash,))
            
            existing = cursor.fetchone()
            
            if existing:
                if existing[1] == FileStatus.COMPLETED.value:
                    print(f"⚠️  Arquivo {file_info.file_name} já foi processado com sucesso")
                    return False
                elif existing[1] == FileStatus.PROCESSING.value:
                    print(f"⚠️  Arquivo {file_info.file_name} já está sendo processado")
                    return False
                else:
                    # Arquivo falhou anteriormente, permitir reprocessamento
                    print(f"🔄 Arquivo {file_info.file_name} será reprocessado (status anterior: {existing[1]})")
                    cursor.execute("""
                        UPDATE oci_file_control 
                        SET status = %s, retry_count = retry_count + 1, updated_at = NOW()
                        WHERE file_hash = %s
                    """, (FileStatus.PENDING.value, file_info.file_hash))
            else:
                # Registrar novo arquivo
                cursor.execute("""
                    INSERT INTO oci_file_control 
                    (file_name, file_hash, size_bytes, modified_date, status, 
                     id_provedor, id_cliente, id_contrato)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    file_info.file_name,
                    file_info.file_hash,
                    file_info.size_bytes,
                    file_info.modified_date,
                    FileStatus.PENDING.value,
                    file_info.id_provedor,
                    file_info.id_cliente,
                    file_info.id_contrato
                ))
                print(f"✓ Arquivo {file_info.file_name} registrado para processamento")
            
            conexao.commit()
            return True
            
        except Exception as e:
            print(f"✗ Erro ao registrar arquivo {file_info.file_name}: {e}")
            conexao.rollback()
            return False
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def start_file_processing(self, file_hash: str) -> Optional[int]:
        """Marca arquivo como em processamento e retorna o ID do controle"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                UPDATE oci_file_control 
                SET status = %s, processing_start = NOW(), updated_at = NOW()
                WHERE file_hash = %s AND status = %s
                RETURNING id
            """, (FileStatus.PROCESSING.value, file_hash, FileStatus.PENDING.value))
            
            result = cursor.fetchone()
            if result:
                conexao.commit()
                return result[0]
            else:
                print(f"⚠️  Não foi possível iniciar processamento do arquivo (hash: {file_hash[:12]}...)")
                return None
                
        except Exception as e:
            print(f"✗ Erro ao iniciar processamento: {e}")
            conexao.rollback()
            return None
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def is_record_duplicate(self, record_hash: str) -> bool:
        """Verifica se um registro já foi processado"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                SELECT id FROM oci_record_control 
                WHERE record_hash = %s AND status = %s
            """, (record_hash, RecordStatus.PROCESSED.value))
            
            result = cursor.fetchone()
            return result is not None
            
        except Exception as e:
            print(f"✗ Erro ao verificar duplicata: {e}")
            return False
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def register_record_processing(self, file_control_id: int, record_data: dict) -> str:
        """Registra um registro para processamento e retorna o hash"""
        record_hash = self.create_record_hash(record_data)
        
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                INSERT INTO oci_record_control 
                (file_control_id, record_hash, line_item_reference, resource_id, 
                 usage_start, cost_amount, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (record_hash) DO NOTHING
            """, (
                file_control_id,
                record_hash,
                record_data.get('lineItem/referenceNo', '')[:255],
                record_data.get('product/resourceId', '')[:255],
                record_data.get('lineItem/intervalUsageStart'),
                record_data.get('cost/myCost', 0),
                RecordStatus.PENDING.value
            ))
            
            conexao.commit()
            return record_hash
            
        except Exception as e:
            print(f"✗ Erro ao registrar record: {e}")
            conexao.rollback()
            return record_hash
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def mark_record_processed(self, record_hash: str, id_utilizacao_recurso: int):
        """Marca um registro como processado com sucesso"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                UPDATE oci_record_control 
                SET status = %s, id_utilizacao_recurso = %s, updated_at = NOW()
                WHERE record_hash = %s
            """, (RecordStatus.PROCESSED.value, id_utilizacao_recurso, record_hash))
            
            conexao.commit()
            
        except Exception as e:
            print(f"✗ Erro ao marcar record como processado: {e}")
            conexao.rollback()
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def mark_record_duplicate(self, record_hash: str):
        """Marca um registro como duplicado"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                UPDATE oci_record_control 
                SET status = %s, updated_at = NOW()
                WHERE record_hash = %s
            """, (RecordStatus.DUPLICATE.value, record_hash))
            
            conexao.commit()
            
        except Exception as e:
            print(f"✗ Erro ao marcar record como duplicado: {e}")
            conexao.rollback()
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def mark_record_failed(self, record_hash: str, error_message: str):
        """Marca um registro como falhado"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            cursor.execute("""
                UPDATE oci_record_control 
                SET status = %s, error_message = %s, updated_at = NOW()
                WHERE record_hash = %s
            """, (RecordStatus.FAILED.value, error_message[:1000], record_hash))
            
            conexao.commit()
            
        except Exception as e:
            print(f"✗ Erro ao marcar record como falhado: {e}")
            conexao.rollback()
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def finish_file_processing(self, file_hash: str, success: bool = True, 
                             error_message: str = None):
        """Finaliza o processamento de um arquivo"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            # Obter estatísticas dos registros
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = %s THEN 1 END) as processed,
                    COUNT(CASE WHEN status = %s THEN 1 END) as failed,
                    COUNT(CASE WHEN status = %s THEN 1 END) as duplicated
                FROM oci_record_control 
                WHERE file_control_id = (
                    SELECT id FROM oci_file_control WHERE file_hash = %s
                )
            """, (
                RecordStatus.PROCESSED.value,
                RecordStatus.FAILED.value, 
                RecordStatus.DUPLICATE.value,
                file_hash
            ))
            
            stats = cursor.fetchone()
            
            # Atualizar arquivo
            status = FileStatus.COMPLETED if success else FileStatus.FAILED
            cursor.execute("""
                UPDATE oci_file_control 
                SET status = %s, processing_end = NOW(), updated_at = NOW(),
                    records_total = %s, records_processed = %s, 
                    records_failed = %s, records_duplicated = %s,
                    error_message = %s
                WHERE file_hash = %s
            """, (
                status.value,
                stats[0] if stats else 0,
                stats[1] if stats else 0,
                stats[2] if stats else 0,
                stats[3] if stats else 0,
                error_message[:1000] if error_message else None,
                file_hash
            ))
            
            conexao.commit()
            
            if stats:
                print(f"✓ Processamento concluído: {stats[1]} processados, "
                      f"{stats[2]} falharam, {stats[3]} duplicados de {stats[0]} total")
            
        except Exception as e:
            print(f"✗ Erro ao finalizar processamento: {e}")
            conexao.rollback()
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def get_processing_stats(self, id_provedor: int = None) -> Dict:
        """Retorna estatísticas de processamento"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            where_clause = "WHERE id_provedor = %s" if id_provedor else ""
            params = [id_provedor] if id_provedor else []
            
            cursor.execute(f"""
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(records_total) as total_records,
                    SUM(records_processed) as processed_records,
                    SUM(records_failed) as failed_records,
                    SUM(records_duplicated) as duplicated_records
                FROM oci_file_control 
                {where_clause}
                GROUP BY status
            """, params)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'files': row[1],
                    'total_records': row[2] or 0,
                    'processed_records': row[3] or 0,
                    'failed_records': row[4] or 0,
                    'duplicated_records': row[5] or 0
                }
            
            return stats
            
        except Exception as e:
            print(f"✗ Erro ao obter estatísticas: {e}")
            return {}
        finally:
            conexao.close_cursor()
            conexao.close_conection()
    
    def cleanup_old_records(self, days: int = 30):
        """Remove registros de controle antigos para manter performance"""
        conexao = ConexaoBancoDeDados()
        conexao.set_cursor()
        cursor = conexao.get_cursor()
        
        try:
            # Remover apenas registros de arquivos completados há mais de X dias
            cursor.execute("""
                DELETE FROM oci_file_control 
                WHERE status = %s 
                AND processing_end < NOW() - INTERVAL '%s days'
            """, (FileStatus.COMPLETED.value, days))
            
            deleted = cursor.rowcount
            conexao.commit()
            
            if deleted > 0:
                print(f"✓ Removidos {deleted} registros de controle antigos")
            
        except Exception as e:
            print(f"✗ Erro ao limpar registros antigos: {e}")
            conexao.rollback()
        finally:
            conexao.close_cursor()
            conexao.close_conection()
