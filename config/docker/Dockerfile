FROM python:3.11

WORKDIR /finops

RUN pip install --upgrade pip

COPY requirements.txt /finops
RUN pip install -r requirements.txt
#RUN mkdir -p /uwsgi

COPY . /finops/finops_celery
