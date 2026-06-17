# FinOps - Guia de Deployment

## Visão Geral

Sistema de monitoramento e controle de custos para Oracle Cloud Infrastructure (OCI).

### Arquitetura Atual

- **Frontend Dashboard:** Flask (porta 5000) → `devmonitorfinops.service.com.br`
- **Grafana:** Dashboards e visualizações (porta 3001) → `devfinops.service.com.br`
- **NGINX:** Proxy reverso com SSL/TLS (portas 80/443)
- **PostgreSQL:** Banco de dados principal
- **Celery:** Processamento assíncrono de jobs OCI
- **Redis/RabbitMQ:** Message brokers

## Deploy Rápido

### 1. NGINX Proxy (HTTPS)

```bash
# Instalar NGINX
sudo apt update && sudo apt install -y nginx

# Configurar proxy
sudo cp deploy/nginx/finops-proxy.conf /etc/nginx/sites-available/finops-proxy
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/finops-proxy /etc/nginx/sites-enabled/

# Certificados SSL (ajustar paths conforme necessário)
sudo mkdir -p /etc/ssl/finops
sudo cp certificados/*.crt /etc/ssl/finops/service_com_br_full.crt
sudo cp certificados/*.key /etc/ssl/finops/service_com_br_full.key
sudo chmod 600 /etc/ssl/finops/service_com_br_full.key

# Ativar
sudo nginx -t && sudo systemctl enable nginx && sudo systemctl start nginx
```

### 2. Grafana com Plugins

```bash
# Subir Grafana
cd deploy/grafana
docker-compose up -d

# Instalar plugins VolkovLabs
../scripts/install_grafana_plugins.sh
```

### 3. Dashboard FinOps

```bash
# Instalar dependências Python
cd /root/finops
pip install -r requirements.txt

# Configurar ambiente
python run_dashboard.py
```

## Domínios Configurados

- **devmonitorfinops.service.com.br** → Dashboard principal (Flask)
- **devfinops.service.com.br** → Grafana (dashboards e análises)

## Monitoramento

```bash
# Verificar proxy NGINX
./deploy/scripts/check_nginx_proxy.sh

# Verificar dashboard
./deploy/scripts/check_dashboard.sh
```

## Troubleshooting

Ver documentação completa em: `docs/nginx_proxy_setup.md`
