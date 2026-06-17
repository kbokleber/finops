import os

# Carrega .env opcional (mantem compatibilidade com setup local/legado).
# Variaveis do ambiente (os.environ) tem prioridade sobre o .env.
def _load_env_file(file_path):
    config = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip().strip('\'"')
    except FileNotFoundError:
        pass
    return config

_file_cfg = _load_env_file("/finops/finops_celery/.env")

def _g(key, default=None):
    # Ambiente > arquivo .env > default
    return os.environ.get(key) or _file_cfg.get(key) or default

# Configurações do banco (CONEXAO_* e DB_* ambos suportados)
DATABASE_URL = (
    f"postgresql://{_g('CONEXAO_DB_USER', _g('DB_USER'))}:"
    f"{_g('CONEXAO_DB_SENHA', _g('DB_PASSWORD'))}@"
    f"{_g('CONEXAO_DB_URL', _g('DB_HOST'))}:"
    f"{_g('CONEXAO_DB_PORT', _g('DB_PORT', '5432'))}/"
    f"{_g('CONEXAO_DB_DATABASE', _g('DB_NAME'))}"
)

# Configurações do Redis
REDIS_URL = (
    f"redis://{_g('REDIS_DB_URL', 'redis')}:"
    f"{_g('REDIS_DB_PORT', '6379')}/"
    f"{_g('REDIS_DB_DATABASE', '0')}"
)

# Configurações Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Outras configurações
DEBUG = True
