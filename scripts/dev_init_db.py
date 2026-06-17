"""Inicializa tabelas minimas para o dashboard rodar em dev local.
Uso: python scripts/dev_init_db.py
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://svc_finops:<sua-senha-do-banco>@localhost:5432/finopsdatabase",
)

DDL = [
    """CREATE TABLE IF NOT EXISTS provedor_nuvem (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        tipo VARCHAR(20),
        datatime_ultimo_update TIMESTAMP,
        datatime_proximo_update TIMESTAMP,
        jobs_restantes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS utilizacao_recurso (
        id SERIAL PRIMARY KEY,
        provedor_id INTEGER REFERENCES provedor_nuvem(id),
        data DATE,
        recurso TEXT,
        custo_total NUMERIC(18,6) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS controle_processamento (
        id SERIAL PRIMARY KEY,
        provedor_id INTEGER REFERENCES provedor_nuvem(id),
        status VARCHAR(20),
        mensagem TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS recurso (
        id SERIAL PRIMARY KEY,
        provedor_id INTEGER REFERENCES provedor_nuvem(id),
        nome TEXT,
        tipo TEXT,
        regiao TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oci_file_control (
        id SERIAL PRIMARY KEY,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_hash TEXT NOT NULL UNIQUE,
        file_size BIGINT,
        status VARCHAR(20) DEFAULT 'pending',
        total_records INTEGER DEFAULT 0,
        processed_records INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS oci_record_control (
        id SERIAL PRIMARY KEY,
        file_control_id INTEGER REFERENCES oci_file_control(id),
        record_hash TEXT NOT NULL UNIQUE,
        line_number INTEGER,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP,
        error_message TEXT
    )""",
]

def main():
    print(f"Conectando em {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            before = [r["table_name"] for r in cur.fetchall()]
            print(f"Tabelas antes: {before}")

            for ddl in DDL:
                cur.execute(ddl)

            conn.commit()

            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY table_name"
            )
            after = [r["table_name"] for r in cur.fetchall()]
            print(f"Tabelas depois: {after}")
        print("OK")
    except Exception as e:
        conn.rollback()
        print(f"ERRO: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
