# Deployment Configuration

Este diretório contém as configurações de deploy para o ambiente FinOps.

## Estrutura

- `nginx/` - Configurações do proxy NGINX
- `grafana/` - Configuração do container Grafana
- `scripts/` - Scripts de automação e monitoramento

## Deploy NGINX Proxy

```bash
# Copiar configuração
sudo cp deploy/nginx/finops-proxy.conf /etc/nginx/sites-available/finops-proxy
sudo ln -sf /etc/nginx/sites-available/finops-proxy /etc/nginx/sites-enabled/

# Testar e recarregar
sudo nginx -t && sudo systemctl reload nginx
```

## Deploy Grafana

```bash
# Usar docker-compose do deploy
cd deploy/grafana
docker-compose up -d

# Instalar plugins
../scripts/install_grafana_plugins.sh
```

## Monitoramento

```bash
# Verificar status completo
./deploy/scripts/check_nginx_proxy.sh
```
