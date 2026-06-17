#!/usr/bin/env python3
"""
Script para criar settings.py adequado para o container
"""

settings_content = '''from dotenv import dotenv_values
import os

# Carregar variáveis do .env
config = dotenv_values(".env")

# Configurações do banco
DATABASE_URL = f"postgresql://{config.get('CONEXAO_DB_USER')}:{config.get('CONEXAO_DB_SENHA')}@{config.get('CONEXAO_DB_URL')}:{config.get('CONEXAO_DB_PORT')}/{config.get('CONEXAO_DB_DATABASE')}"

# Configurações do Redis
REDIS_URL = f"redis://{config.get('REDIS_DB_URL')}:{config.get('REDIS_DB_PORT')}/{config.get('REDIS_DB_DATABASE')}"

# Configurações Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Outras configurações
DEBUG = True
'''

print("Criando settings.py...")
with open('/finops_celery/settings.py', 'w') as f:
    f.write(settings_content)

print("✅ settings.py criado com sucesso!")
