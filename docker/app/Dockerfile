# Imagem compartilhada por dashboard Flask e workers Celery.
# Cada servico no compose define seu proprio `command:`.
#
# Estrutura final dentro da imagem:
#   /finops/finops_celery/         <- raiz do projeto copiada aqui
#       celery.py                  <- celery app (module finops_celery.celery)
#       settings.py                <- le /finops/finops_celery/.env
#       __init__.py                <- reexporta `app` (from .celery import app)
#       tasks/                     <- tasks reais (package finops_celery.tasks)
#       helpers/                   <- helpers (package finops_celery.helpers)
#       dashboard/                 <- app Flask
#       .env                       <- placeholder; Coolify injeta env vars
#
# WORKDIR=/finops/finops_celery/ garante que `celery -A finops_celery worker`
# resolva para o package real `finops_celery/` (e nao para o diretorio-pai,
# que viraria um namespace package vazio).

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /finops

# Dependencias de sistema minimas para compilar psycopg2-binary.
# Tambem instala o docker CLI (binario estatico) para o endpoint
# /api/docker-containers do dashboard conseguir listar os containers
# do host (via socket /var/run/docker.sock montado pelo compose).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
        libpq5 \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz \
        | tar -xz -C /tmp \
    && mv /tmp/docker/docker /usr/local/bin/docker \
    && chmod +x /usr/local/bin/docker \
    && rm -rf /tmp/docker /var/lib/apt/lists/*

# requirements.txt fica na raiz copiada, mas precisamos dele antes do COPY . .
# Truque: copiamos temporariamente e depois o COPY . sobrescreve a pasta raiz.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && pip install gunicorn==22.0.0

# Copia o codigo inteiro para /finops/finops_celery/.
COPY . /finops/finops_celery/

# Em runtime, o Coolify injeta env vars na UI. Nao precisamos de .env.

# Cria diretorios de log que o codigo assume existirem.
RUN mkdir -p /finops/finops_celery/logs

# Usuario nao-root. Ordem importa: criar usuario PRIMEIRO, depois
# adicionar aos grupos (caso contrario, `usermod` retorna exit 6
# dizendo que o usuario nao existe).
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /finops

# O usuario `app` precisa ter acesso ao socket do Docker.
# Adiciona o usuario ao grupo 'docker' (gid espelha o host) e ao grupo
# 'root' (gid 0) para que o socket do Docker (permissao 660,
# root:docker) seja acessivel.
RUN groupadd -f docker \
    && usermod -aG docker,root app

USER app

# CWD passa a ser o diretorio-raiz copiado. Assim:
#   - `celery -A finops_celery` resolve para o package REAL (com __init__.py)
#   - `gunicorn --chdir /finops/finops_celery/dashboard wsgi:app` continua OK
#   - Imports absolutos `from finops_celery.tasks import ...` continuam OK
WORKDIR /finops/finops_celery

EXPOSE 5000
