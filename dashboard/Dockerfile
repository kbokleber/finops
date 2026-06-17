# Dashboard FinOps - imagem de dev
# Workdir em /app/dashboard porque o wsgi.py faz `from app import app`
# e o volume monta o codigo do dashboard exatamente nesse caminho.
# Em dev, os volumes sobrepoem /app/dashboard e /app/finops_celery.

FROM python:3.11-slim

# Diretorio base (volume monta /app/dashboard e /app/finops_celery por cima)
WORKDIR /app

# Dependencias: dashboard + integracao Postgres + Celery API (para /api/celery-status)
RUN pip install --no-cache-dir \
        Flask==3.0.0 \
        psycopg2-binary==2.9.9 \
        pytz==2024.1 \
        Flask-Session==0.8.0 \
        msal==1.29.0 \
        celery==5.4.0 \
        gunicorn \
        python-dotenv==1.0.1

# Copia o codigo do dashboard (sera sobrescrito pelo volume em dev,
# mas garante que a imagem funciona standalone tambem)
COPY dashboard/ /app/dashboard/

# Cria o diretorio de sessoes (volume monta por cima em dev)
RUN mkdir -p /app/dashboard/flask_session

EXPOSE 5000

# Entry point: o comando real vem do docker-compose.dev.yml.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--chdir", "/app/dashboard", "wsgi:app"]
