# 🚀 Guia de Instalação - FinOps Dashboard

## 📋 Pré-requisitos

### 🖥️ Sistema Operacional
- **Ubuntu 20.04+** ou **Debian 11+**
- **Python 3.8+**
- **PostgreSQL 12+**
- **Git** para controle de versão

### 🔧 Dependências do Sistema
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git curl
```

## 📦 Instalação

### 1. Clonar o Repositório
```bash
# Navegar para diretório raiz
cd /root

# Clonar repositório
git clone <repository-url> finops
cd finops
```

### 2. Configurar Ambiente Python
```bash
# Criar ambiente virtual
python3 -m venv dashboard_env

# Ativar ambiente
source dashboard_env/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Banco de Dados

#### Criar Usuário e Banco
```bash
sudo -u postgres createuser finops_user
sudo -u postgres createdb finops
sudo -u postgres psql -c "ALTER USER finops_user PASSWORD 'finops2024';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE finops TO finops_user;"
```

#### Configurar PostgreSQL
```bash
# Editar configuração (se necessário)
sudo nano /etc/postgresql/*/main/postgresql.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Reiniciar serviço
sudo systemctl restart postgresql
```

### 4. Configurar Aplicação

#### Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

**Configuração básica do .env:**
```env
# Banco de Dados
DATABASE_URL=postgresql://finops_user:finops2024@localhost/finops

# Dashboard
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-aqui

# Autenticação (Modo Bypass para início)
ENABLE_AZURE_AUTH=false

# Opcional: Azure AD (para produção)
# AZURE_CLIENT_ID=seu-client-id
# AZURE_CLIENT_SECRET=seu-client-secret
# AZURE_TENANT_ID=seu-tenant-id
```

### 5. Inicializar Banco de Dados
```bash
# Executar scripts de inicialização (se existirem)
python3 init_oci_tables.py

# Ou executar scripts SQL personalizados
# psql -h localhost -U finops_user -d finops -f scripts/init_database.sql
```

### 6. Tornar Scripts Executáveis
```bash
chmod +x scripts/*.sh
chmod +x dashboard/run.sh
```

## 🚀 Primeira Execução

### Método Simples (Dashboard)
```bash
# Navegar para dashboard
cd dashboard
./run.sh
```

### Método Completo (Recomendado)
```bash
# Usar o gerenciador principal
cd /root/finops
./scripts/dashboard_manager.sh start
```

### Verificar Funcionamento
```bash
# Status do dashboard
./scripts/dashboard_manager.sh status

# Teste de conectividade
curl http://localhost:5000

# Diagnóstico completo
./scripts/diagnostico_dashboard.sh
```

## 🌐 Acesso

### Interface Web
- **URL Principal**: http://localhost:5000
- **Modo**: Bypass (sem autenticação inicialmente)

### Para Acesso Externo
```bash
# Se necessário, configure iptables ou ufw
sudo ufw allow 5000
```

## ⚙️ Configurações Avançadas

### Systemd Service (Opcional)
```bash
# Instalar como serviço
./scripts/dashboard_manager.sh install-service

# Gerenciar via systemd
sudo systemctl start finops-dashboard
sudo systemctl enable finops-dashboard
sudo systemctl status finops-dashboard
```

### Docker (Alternativo)
```bash
# Usar configuração Docker
cd config/docker
docker-compose up -d
```

### Nginx Reverse Proxy (Produção)
```nginx
# /etc/nginx/sites-available/finops
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Pós-Instalação

### Verificações Essenciais
```bash
# 1. Status do dashboard
./scripts/dashboard_manager.sh status

# 2. Teste de persistência
./scripts/test_persistence.sh

# 3. Conectividade do banco
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', database='finops', user='finops_user', password='finops2024')
    print('✅ Conexão com banco OK')
    conn.close()
except Exception as e:
    print(f'❌ Erro no banco: {e}')
"

# 4. Verificar logs
tail -20 logs/dashboard.log
```

### Configurar Monitoramento
```bash
# Adicionar ao crontab para verificação automática
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /root/finops && ./scripts/dashboard_manager.sh status >/dev/null") | crontab -
```

## 🔒 Configuração de Produção

### 1. Habilitar Autenticação Azure AD
```bash
# Editar .env
ENABLE_AZURE_AUTH=true
AZURE_CLIENT_ID=seu-client-id-real
AZURE_CLIENT_SECRET=seu-client-secret-real
AZURE_TENANT_ID=seu-tenant-id-real
```

### 2. SSL/HTTPS
```bash
# Instalar certificado (Let's Encrypt recomendado)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

### 3. Firewall
```bash
# Configurar firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw deny 5000  # Bloquear acesso direto após nginx
```

### 4. Backup Automático
```bash
# Configurar backup automático
echo "0 2 * * * cd /root/finops && tar -czf /backup/finops_backup_\$(date +\%Y\%m\%d).tar.gz . --exclude=logs/ --exclude=__pycache__/" | crontab -
```

## 🚨 Solução de Problemas de Instalação

### Erro: Dependências Python
```bash
# Atualizar pip
python3 -m pip install --upgrade pip

# Instalar dependências uma por uma
pip install flask psycopg2-binary requests
```

### Erro: PostgreSQL
```bash
# Verificar se está rodando
sudo systemctl status postgresql

# Reiniciar se necessário
sudo systemctl restart postgresql

# Verificar logs
sudo tail -20 /var/log/postgresql/postgresql-*-main.log
```

### Erro: Permissões
```bash
# Corrigir permissões dos scripts
find scripts/ -name "*.sh" -exec chmod +x {} \;

# Verificar ownership
sudo chown -R root:root /root/finops
```

### Erro: Porta em Uso
```bash
# Verificar o que está usando a porta 5000
sudo fuser -v 5000/tcp

# Matar processo se necessário
sudo fuser -k 5000/tcp
```

## ✅ Validação da Instalação

### Checklist Final
- [ ] ✅ Python 3.8+ instalado
- [ ] ✅ PostgreSQL funcionando
- [ ] ✅ Banco `finops` criado
- [ ] ✅ Usuário `finops_user` configurado
- [ ] ✅ Dependências Python instaladas
- [ ] ✅ Arquivo `.env` configurado
- [ ] ✅ Scripts executáveis
- [ ] ✅ Dashboard iniciando sem erros
- [ ] ✅ Interface web acessível
- [ ] ✅ Logs sendo gerados
- [ ] ✅ Teste de persistência passou

### Comando de Validação Completa
```bash
cd /root/finops
echo "🔍 VALIDAÇÃO COMPLETA DA INSTALAÇÃO"
echo "=================================="

# 1. Dashboard
./scripts/dashboard_manager.sh status

# 2. Diagnóstico
./scripts/diagnostico_dashboard.sh

# 3. Conectividade
curl -s http://localhost:5000 >/dev/null && echo "✅ Interface web OK" || echo "❌ Interface web FALHA"

echo "=================================="
echo "✅ Instalação concluída com sucesso!"
```

## 📞 Suporte

### Documentação Adicional
- [Gerenciamento do Dashboard](DASHBOARD_MANAGEMENT.md)
- [Resolução de Problemas](TROUBLESHOOTING.md)
- [Configuração Azure AD](AZURE_AUTH_SETUP.md)

### Logs para Debug
- **Dashboard**: `/root/finops/logs/dashboard.log`
- **Sistema**: `/var/log/syslog`
- **PostgreSQL**: `/var/log/postgresql/`

### Comandos de Diagnóstico
```bash
# Diagnóstico completo
./scripts/diagnostico_dashboard.sh

# Status detalhado
./scripts/dashboard_manager.sh status

# Logs em tempo real
./scripts/dashboard_manager.sh logs
```
