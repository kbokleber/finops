# 🚀 FinOps Dashboard

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Visão Geral

O **FinOps Dashboard** é uma solução completa para monitoramento e análise de custos em ambientes de nuvem, com foco especial em **Oracle Cloud Infrastructure (OCI)**. 

### ✨ Características Principais

- 🌐 **Dashboard Web Responsivo** - Interface moderna e intuitiva
- 🔐 **Autenticação Enterprise** - Integração com Azure AD (modo bypass disponível)
- 📊 **Monitoramento em Tempo Real** - Dados atualizados automaticamente
- 🔧 **Gerenciamento Simplificado** - Scripts automatizados de administração
- 🐳 **Deploy Flexível** - Suporte a Docker e systemd
- 📝 **Logs Centralizados** - Monitoramento e diagnóstico completo

## 🚀 Início Rápido

### Instalação
```bash
# Clone o repositório
git clone <repository-url> /root/finops
cd /root/finops

# Configure o ambiente (siga o guia de instalação completo)
# Ver docs/INSTALLATION.md para instruções detalhadas
```

### Execução
```bash
# Iniciar dashboard (método recomendado)
./scripts/dashboard_manager.sh start

# Verificar status
./scripts/dashboard_manager.sh status

# Acessar interface
# http://localhost:5000
```

## 📚 Documentação

### 🎯 Guias Essenciais
- [📦 Instalação Completa](docs/INSTALLATION.md)
- [🔧 Gerenciamento do Dashboard](docs/DASHBOARD_MANAGEMENT.md)
- [🔐 Configuração Azure AD](docs/AZURE_AUTH_SETUP.md)
- [🚨 Resolução de Problemas](docs/TROUBLESHOOTING.md)

### 🛠️ Administração
- [📜 Scripts de Gerenciamento](scripts/README.md)
- [🏗️ Arquitetura do Sistema](docs/ARCHITECTURE.md)
- [📝 Changelog](docs/CHANGELOG_DASHBOARD.md)

### 📖 Documentação Completa
Acesse o [índice completo da documentação](docs/README.md) para todos os guias disponíveis.

## 🎯 Funcionalidades

### 📊 Dashboard Principal
- **Visão Geral**: Métricas principais e KPIs
- **Recursos OCI**: Monitoramento de instâncias e custos
- **Status dos Provedores**: Último update e próxima sincronização
- **Dados Históricos**: Análise temporal de utilização

### 🔐 Autenticação
- **Modo Bypass**: Para desenvolvimento e testes
- **Azure AD**: Autenticação enterprise corporativa
- **Alternância Fácil**: Uma variável para alternar modos

### 🛡️ Robustez
- **Independência de Terminal**: Dashboard persiste após logout SSH
- **Recovery Automático**: Scripts de recuperação e limpeza
- **Monitoramento**: Health checks e diagnósticos
- **Logs Estruturados**: Rastreamento completo de atividades

## 🔧 Comandos Principais

### Gerenciamento do Dashboard
```bash
cd /root/finops

# Comandos básicos
./scripts/dashboard_manager.sh start      # Iniciar
./scripts/dashboard_manager.sh stop       # Parar
./scripts/dashboard_manager.sh restart    # Reiniciar
./scripts/dashboard_manager.sh status     # Status
./scripts/dashboard_manager.sh logs       # Ver logs

# Resolução de problemas
./scripts/dashboard_manager.sh cleanup    # Limpeza forçada
./scripts/diagnostico_dashboard.sh        # Diagnóstico completo
```

### Testes e Validação
```bash
# Teste de persistência (independência do terminal)
./scripts/test_persistence.sh

# Verificação de conectividade
curl http://localhost:5000

# Status do banco de dados
python3 -c "import psycopg2; print('DB OK')"
```

## 📁 Estrutura do Projeto

```
finops/
├── 📚 docs/              # Documentação completa
├── 🔧 scripts/           # Scripts de gerenciamento
├── ⚙️ config/            # Configurações (Docker, systemd, nginx)
├── 🌐 dashboard/         # Aplicação web principal
├── 📊 tasks/             # Processamento de dados
├── 🛠️ helpers/           # Utilitários
├── 🔄 finops_celery/     # Processamento assíncrono
├── 📝 logs/              # Logs e arquivos temporários
├── 📋 requirements.txt   # Dependências Python
└── 🔒 .env.example       # Exemplo de configuração
```

## 🚨 Resolução Rápida de Problemas

### Dashboard não inicia
```bash
./scripts/dashboard_manager.sh cleanup
./scripts/dashboard_manager.sh start
```

### Porta ocupada
```bash
./scripts/dashboard_manager.sh cleanup  # Resolve automaticamente
```

### Dados incorretos
Consulte o [guia de troubleshooting](docs/TROUBLESHOOTING.md) - já foram corrigidos problemas de:
- ✅ Contagem de registros (filtros SQL)
- ✅ Timezone dos provedores (conversão UTC/Brasília)

### Diagnóstico completo
```bash
./scripts/diagnostico_dashboard.sh
```

## 🌐 Configuração de Produção

### DNS e SSL
```bash
# Configurar nginx reverse proxy
# Ver docs/INSTALLATION.md para detalhes

# Certificado SSL (Let's Encrypt)
sudo certbot --nginx -d seu-dominio.com
```

### Autenticação Azure AD
```bash
# Editar .env
ENABLE_AZURE_AUTH=true
AZURE_CLIENT_ID=seu-client-id
AZURE_CLIENT_SECRET=seu-secret
AZURE_TENANT_ID=seu-tenant
```

## 🔄 Atualizações e Manutenção

### Backup
```bash
# Backup automático (exclui logs e cache)
tar -czf finops_backup_$(date +%Y%m%d).tar.gz \
    --exclude=logs/ --exclude=__pycache__/ \
    finops/
```

### Atualização
```bash
# Após git pull
./scripts/dashboard_manager.sh restart
```

### Monitoramento
```bash
# Logs em tempo real
./scripts/dashboard_manager.sh logs

# Status periódico
watch -n 30 './scripts/dashboard_manager.sh status'
```

## 📊 Status do Sistema

```
🟢 Dashboard - Funcionando independente do terminal
🟢 Autenticação - Modo bypass ativo (Azure AD preparado)
🟢 Dados - Timezone e contagens corretas
🟢 Scripts - Gerenciamento completo disponível
🟢 Documentação - Organizada e atualizada
🟢 Estrutura - Reorganizada para produção
```

## 🤝 Contribuição

### Estrutura para Desenvolvimento
- **Logs**: `/root/finops/logs/`
- **Scripts**: `/root/finops/scripts/`
- **Docs**: `/root/finops/docs/`
- **Config**: `/root/finops/config/`

### Antes de Commit
```bash
# Verificar funcionamento
./scripts/dashboard_manager.sh status
./scripts/test_persistence.sh

# Atualizar documentação se necessário
# Seguir estrutura em docs/
```

## 📞 Suporte

### Diagnóstico Automático
```bash
./scripts/diagnostico_dashboard.sh
```

### Logs
- **Dashboard**: `/root/finops/logs/dashboard.log`
- **Erro**: Console output dos scripts

### Documentação
- [Troubleshooting Completo](docs/TROUBLESHOOTING.md)
- [Guias de Administração](docs/)

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

**✨ Sistema pronto para produção com todas as funcionalidades essenciais implementadas e testadas!**
