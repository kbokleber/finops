#!/bin/bash

# Script para configurar backup automático
# Execute este script no NOVO servidor após a migração

set -e

echo "=== Configurando backup automático ==="

# Criar diretório de backup
mkdir -p /root/backups

# Criar script de backup
cat > /root/backup_finops.sh << 'EOF'
#!/bin/bash

# Script de backup automático do FinOps
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
LOG_FILE="/var/log/finops_backup.log"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

log "Iniciando backup automático"

# Backup do banco
log "Fazendo backup do banco de dados"
sudo -u postgres pg_dump -h localhost -U svc_finops -d finopsdatabase | gzip > $BACKUP_DIR/finops_db_$DATE.sql.gz

if [ $? -eq 0 ]; then
    log "Backup do banco concluído com sucesso"
else
    log "ERRO: Falha no backup do banco"
fi

# Backup dos dados do Grafana
log "Fazendo backup dos dados do Grafana"
docker exec grafana-grafana-1 tar -czf - /var/lib/grafana > $BACKUP_DIR/grafana_data_$DATE.tar.gz 2>/dev/null

if [ $? -eq 0 ]; then
    log "Backup do Grafana concluído com sucesso"
else
    log "ERRO: Falha no backup do Grafana"
fi

# Backup das configurações
log "Fazendo backup das configurações"
tar -czf $BACKUP_DIR/finops_configs_$DATE.tar.gz /root/finops /root/docker_compose_* /root/grafana 2>/dev/null

if [ $? -eq 0 ]; then
    log "Backup das configurações concluído com sucesso"
else
    log "ERRO: Falha no backup das configurações"
fi

# Manter apenas os últimos 7 backups
log "Limpando backups antigos"
find $BACKUP_DIR -name "finops_db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "grafana_data_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "finops_configs_*.tar.gz" -mtime +7 -delete

# Verificar espaço em disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log "ATENÇÃO: Uso de disco acima de 80% ($DISK_USAGE%)"
fi

log "Backup automático concluído"
EOF

# Tornar executável
chmod +x /root/backup_finops.sh

# Configurar crontab para backup diário às 2h
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup_finops.sh") | crontab -

# Configurar logrotate para os logs de backup
cat > /etc/logrotate.d/finops << 'EOF'
/var/log/finops_backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

echo "✓ Backup automático configurado"
echo "✓ Execução diária às 2h da manhã"
echo "✓ Logs em /var/log/finops_backup.log"
echo "✓ Backups salvos em /root/backups"

# Testar backup manualmente
echo "Executando teste de backup..."
/root/backup_finops.sh

echo "=== Configuração de backup concluída ==="
