"""WSGI entrypoint para gunicorn no Coolify.
O comando no compose eh `gunicorn --chdir /finops/finops_celery/dashboard wsgi:app`
e este modulo expoe `app` importando de app.py.
"""
from app import app  # noqa: F401
