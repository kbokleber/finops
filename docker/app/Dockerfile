# Imagem compartilhada por dashboard Flask e workers Celery.
# Cada servico no compose define seu proprio `command:`.
#
# Estrutura final dentro da imagem (espelha o Dockerfile legacy do projeto):
#   /finops/finops_celery/         <- raiz do projeto copiada aqui
#       celery.py                  <- celery app (module finops_celery.celery)
#       settings.py                <- le /finops/finops_celery/.env
#       __init__.py
#       tasks/                     <- tasks reais
#       dashboard/                 <- app Flask
#       finops_celery/.env         <- settings.py procura esse path absoluto
#
# WORKDIR=/finops faz com que `celery -A finops_celery worker`
# encontre o package `finops_celery/` em sys.path.

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /finops

# Dependencias de sistema minimas para compilar psycopg2-binary.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt fica na raiz copiada, mas precisamos dele antes do COPY . .
# Truque: copiamos temporariamente e depois o COPY . sobrescreve a pasta raiz.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && pip install gunicorn==22.0.0

# Copia o codigo inteiro para /finops/finops_celery/.
COPY . /finops/finops_celery/

# settings.py le /finops/finops_celery/.env (path absoluto).
# Em runtime, o Coolify monta env vars na UI; este arquivo eh so um placeholder.
RUN cp /finops/finops_celery/.env.example /finops/finops_celery/.env \
    || touch /finops/finops_celery/.env

# Cria diretorios de log que o codigo assume existirem.
RUN mkdir -p /finops/finops_celery/logs

# Usuario nao-root.
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /finops
USER app

WORKDIR /finops

EXPOSE 5000
