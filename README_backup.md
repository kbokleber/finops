# FinOps - Sistema de Gestão de Custos Cloud

## 📋 Descrição
Sistema para monitoramento e gestão de custos de provedores cloud (AWS, Azure, GCP, OCI) usando Celery para processamento assíncrono e PostgreSQL para armazenamento.

## 🏗️ Arquitetura
- **Backend**: Python + Celery + Redis/RabbitMQ
- **Banco de Dados**: PostgreSQL
- **Monitoramento**: Grafana + Dashboard Flask
- **Containerização**: Docker + Docker Compose

## 🚀 Componentes Principais

### Tasks Celery
- `get_aws.py` - Coleta dados AWS
- `get_azure.py` - Coleta dados Azure  
- `get_gcp_bigquery.py` - Coleta dados GCP
- `get_oci.py` - Coleta dados OCI
- `get_recomendations_aws.py` - Recomendações AWS
- `up_date_resumo.py` - Atualização de resumos

### Helpers
- `conexao_banco.py` - Conexões PostgreSQL
- `redis_database.py` - Cache Redis
- `valor_dolar.py` - Cotação USD
- `gerencia_de_recurso.py` - Gestão recursos
- `oci_file_control.py` - Controle arquivos OCI

## 🔧 Configuração

### Variáveis de Ambiente (.env)
```bash
# Banco de Dados
CONEXAO_DB_URL=localhost:5432
CONEXAO_DB_USER=svc_finops
CONEXAO_DB_SENHA=senha
CONEXAO_DB_DATABASE=finopsdatabase

# Cloud Providers
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
OCI_CONFIG_FILE=/opt/oci/config
```

## 🐳 Deploy com Docker

### Desenvolvimento
```bash
docker-compose up -d
```

### Produção
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Dashboard
- **URL**: http://localhost:5000 (integrado ao projeto)
- **Grafana**: http://localhost:3000
- **Localização**: `/finops/dashboard/`

## 🔄 Comandos Úteis

### Celery Workers
```bash
# Iniciar worker
celery -A finops_celery worker --loglevel=info

# Iniciar beat scheduler
celery -A finops_celery beat --loglevel=info

# Monitorar tasks
celery -A finops_celery flower
```

### Scripts de Administração
```bash
# Diagnóstico rápido do sistema
python3 scripts/diagnosis/simple_diagnosis.py

# Monitoramento OCI interativo
python3 scripts/monitoring/monitor_oci_interativo.py

# Listar tabelas do banco
python3 scripts/database/list_all_tables.py

# Verificar conectividade OCI
python3 scripts/utils/test_oci_connectivity.py
```

### Banco de Dados
```bash
# Backup
pg_dump finopsdatabase > backup.sql

# Restore
psql finopsdatabase < backup.sql
```

## 📁 Estrutura do Projeto
```
finops/
├── tasks/           # Tasks Celery
├── helpers/         # Utilitários
├── finops_celery/   # Configuração Celery
├── dashboard/       # Dashboard Flask
│   ├── app.py      # Aplicação principal
│   └── templates/  # Templates HTML
├── scripts/         # Scripts de administração
│   ├── database/   # Scripts de banco
│   ├── diagnosis/  # Scripts de diagnóstico
│   ├── monitoring/ # Scripts de monitoramento
│   ├── utils/      # Scripts utilitários
│   └── admin/      # Scripts de administração
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
├── run_dashboard.py
├── start_finops.sh
├── settings.py
└── celery.py
```

## 🚀 Roadmap
- [ ] Autenticação do Dashboard Finops Monitoring
- [ ] Recomendações
- [ ] Interface web administrativa
- [ ] Alertas automáticos por email
- [ ] Relatórios PDF automatizados
- [ ] API REST completa
- [ ] Machine Learning para previsões

## 👥 Equipe de Desenvolvimento
- DevOps ServiceIT Team
- Contato: devops@service.com.br

## 📝 Changelog
### v2.1.0 (2025-08-07)
- **Dashboard integrado** ao projeto principal
- **Scripts reorganizados** em categorias (`/scripts/database/`, `/scripts/diagnosis/`, etc.)
- Scripts de inicialização automatizados
- Estrutura modular e profissional
- Dependências centralizadas
- Templates atualizados
- Documentação completa dos scripts

### v2.0.0 (2025-08-07)
- Melhorias scripts OCI
- Novos helpers de controle
- Debug logs implementados
- Estrutura modularizada

---
**Ambiente**: Desenvolvimento  
**Servidor Produção**: [URL_PRODUCAO]  
**Última Atualização**: 07/08/2025
