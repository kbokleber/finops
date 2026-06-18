import os

# Função para carregar configurações do .env manualmente
def load_env_file(file_path):
    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('\'"')
                    config[key] = value
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado")
    return config

# Carregar variáveis do .env
_file_cfg = load_env_file("/finops/finops_celery/.env")

# Variaveis do ambiente (os.environ) tem prioridade sobre o .env.
def _g(key, default=None):
    return os.environ.get(key) or _file_cfg.get(key) or default

# Alias `config` para manter compatibilidade com celery.py (from .settings import config).
config = {**_file_cfg, **{k: v for k, v in os.environ.items()}}

# Configurações do banco
DATABASE_URL = f"postgresql://{_g('CONEXAO_DB_USER')}:{_g('CONEXAO_DB_SENHA')}@{_g('CONEXAO_DB_URL')}:{_g('CONEXAO_DB_PORT')}/{_g('CONEXAO_DB_DATABASE')}"

# Configurações do Redis (com senha opcional via REDIS_PASSWORD ou REDIS_DB_SENHA)
_redis_password = _g('REDIS_PASSWORD') or _g('REDIS_DB_SENHA')
_redis_auth = f":{_redis_password}@" if _redis_password else ""
REDIS_URL = f"redis://{_redis_auth}{_g('REDIS_DB_URL', 'redis')}:{_g('REDIS_DB_PORT', '6379')}/{_g('REDIS_DB_DATABASE', '0')}"

# Configurações Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Outras configurações
DEBUG = True
