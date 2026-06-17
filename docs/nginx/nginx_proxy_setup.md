# Configuração NGINX Proxy - FinOps

## Resumo da Implementação

**Data de Configuração:** 16 de Outubro de 2025

### Domínios Configurados

1. **devmonitorfinops.service.com.br**
   - Porta de entrada: 443 (HTTPS)
   - Destino: 178.156.185.182:5000
   - Serviço: Dashboard FinOps (Python Flask)
   - Status: ✅ Funcionando

2. **devfinops.service.com.br**
   - Porta de entrada: 443 (HTTPS)
   - Destino: 178.156.185.182:3001
   - Serviço: Grafana
   - Status: ✅ Funcionando

### Características da Configuração

- **SSL/TLS:** Certificados `service_com_br_full.crt` e `service_com_br_full.key`
- **Redirecionamento HTTP → HTTPS:** Automático na porta 80
- **Protocolos SSL:** TLSv1.2 e TLSv1.3
- **Headers de Segurança:** HSTS, X-Frame-Options, X-Content-Type-Options
- **Proxy Buffers:** Otimizado para performance
- **Logs Separados:** Cada domínio possui logs específicos

### Arquivos Principais

- **Configuração NGINX:** `/etc/nginx/sites-available/finops-proxy`
- **Certificados SSL:** `/etc/ssl/finops/`
- **Logs do Proxy:** `/var/log/nginx/`
- **Script de Verificação:** `/root/scripts/check_nginx_proxy.sh`

### Comandos Úteis

```bash
# Verificar status
systemctl status nginx

# Recarregar configuração
nginx -t && systemctl reload nginx

# Ver logs
tail -f /var/log/nginx/devmonitorfinops_access.log
tail -f /var/log/nginx/devfinops_access.log

# Script de verificação completa
/root/scripts/check_nginx_proxy.sh
```

### Portas Utilizadas

- **443:** NGINX (HTTPS)
- **80:** NGINX (HTTP - redireciona para HTTPS)
- **5000:** Dashboard FinOps
- **3001:** Grafana (interno)

### Monitoramento

Execute o script de verificação regularmente:
```bash
/root/scripts/check_nginx_proxy.sh
```

### Grafana - Plugins VolkovLabs

Os seguintes plugins estão instalados no Grafana:
- **volkovlabs-variable-panel** v3.6.0 (Painéis de variáveis)
- **volkovlabs-form-panel** v4.8.0 (Formulários interativos)  
- **volkovlabs-image-panel** v6.3.0 (Exibição de imagens)
- **volkovlabs-table-panel** v1.2.0 (Tabelas avançadas)
- **volkovlabs-echarts-panel** v6.6.0 (Gráficos ECharts)

**Script para reinstalar plugins:** `/root/scripts/install_grafana_plugins.sh`

### Troubleshooting

1. Se algum domínio não funcionar, verificar se o serviço de destino está rodando
2. Verificar logs: `tail -f /var/log/nginx/error.log`
3. Testar configuração: `nginx -t`
4. Verificar certificados: `openssl x509 -in /etc/ssl/finops/service_com_br_full.crt -text -noout`
5. **Problemas com plugins Grafana:** Execute `/root/scripts/install_grafana_plugins.sh`
6. **Dashboard com erros:** Verifique se todos os plugins necessários estão instalados

---
**Configuração realizada com sucesso!** ✅