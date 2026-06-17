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
config = load_env_file("/finops/finops_celery/.env")

# Configurações do banco
DATABASE_URL = f"postgresql://{config.get('CONEXAO_DB_USER')}:{config.get('CONEXAO_DB_SENHA')}@{config.get('CONEXAO_DB_URL')}:{config.get('CONEXAO_DB_PORT')}/{config.get('CONEXAO_DB_DATABASE')}"

# Configurações do Redis
REDIS_URL = f"redis://{config.get('REDIS_DB_URL')}:{config.get('REDIS_DB_PORT')}/{config.get('REDIS_DB_DATABASE')}"

# Configurações Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Outras configurações
DEBUG = True
