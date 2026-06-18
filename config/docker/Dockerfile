FROM python:3.11

WORKDIR /finops

RUN pip install --upgrade pip

COPY requirements.txt /finops
RUN pip install -r requirements.txt
#RUN mkdir -p /uwsgi

# O codigo do app vive em /finops/finops_celery (a pasta).
# O comando celery precisa ser executado de /finops/ para
# que `celery -A finops_celery` encontre o modulo.
COPY . /finops/
