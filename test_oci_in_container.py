#!/usr/bin/env python3
"""
Script de teste e inicialização do sistema OCI - versão container simples
"""

import sys
import os
sys.path.insert(0, '/finops_celery')

try:
    # Tentar importar direto do settings
    from settings import DATABASE_URL
    print(f"✅ Settings importado com sucesso")
    print(f"📊 DATABASE_URL encontrado: {DATABASE_URL[:50]}...")
except ImportError as e:
    print(f"❌ Erro importando settings: {e}")
    print("🔍 Tentando localizar settings...")
    
    # Listar arquivos disponíveis
    if os.path.exists('/finops_celery'):
        files = os.listdir('/finops_celery')
        print(f"📁 Arquivos em /finops_celery: {files}")
    
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Testar conexão
    print("🔌 Testando conexão com banco...")
    
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ Conectado ao PostgreSQL: {version['version'][:50]}...")
    
    conn.close()
    print("✅ Conexão testada com sucesso!")
    
    # Tentar importar o módulo de controle
    try:
        from helpers.oci_file_control import OCIFileControl
        print("✅ Módulo OCIFileControl importado com sucesso!")
        
        # Inicializar e testar
        control = OCIFileControl()
        print("✅ OCIFileControl inicializado!")
        
        # Verificar se tabelas existem
        if control.check_tables():
            print("✅ Tabelas de controle já existem")
        else:
            print("⚠️  Tabelas de controle não existem - criando...")
            control.setup_tables()
            print("✅ Tabelas criadas com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro com OCIFileControl: {e}")
        print("📋 Vamos criar as tabelas manualmente...")
        
        # Criar tabelas diretamente
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cursor:
            # Tabela de controle de arquivos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_file_control (
                    id SERIAL PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size BIGINT,
                    status VARCHAR(20) DEFAULT 'pending',
                    total_records INTEGER DEFAULT 0,
                    processed_records INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    UNIQUE(file_hash)
                )
            """)
            
            # Tabela de controle de registros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oci_record_control (
                    id SERIAL PRIMARY KEY,
                    file_id INTEGER REFERENCES oci_file_control(id),
                    record_hash TEXT NOT NULL,
                    line_number INTEGER,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT,
                    UNIQUE(record_hash)
                )
            """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_status ON oci_file_control(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_file_created ON oci_file_control(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_file ON oci_record_control(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_oci_record_status ON oci_record_control(status)")
            
            conn.commit()
            print("✅ Tabelas criadas diretamente com sucesso!")
        
        conn.close()
        
except Exception as e:
    print(f"❌ Erro geral: {e}")
    sys.exit(1)

print("\n🎉 Sistema OCI inicializado com sucesso!")
print("📊 Próximos passos:")
print("  1. Testar processamento de arquivo")
print("  2. Integrar com Celery tasks")
print("  3. Configurar monitoramento")
