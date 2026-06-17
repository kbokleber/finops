# 🔧 Scripts de Gerenciamento FinOps

## 📋 Visão Geral

Esta pasta contém todos os scripts necessários para gerenciar o Dashboard FinOps de forma eficiente e automatizada.

## 🚀 Scripts Principais

### `dashboard_manager.sh` - Gerenciador Principal ⭐
**O script mais importante para administração do dashboard.**

```bash
# Comandos básicos
./dashboard_manager.sh start     # Iniciar dashboard independente
./dashboard_manager.sh stop      # Parar dashboard
./dashboard_manager.sh restart   # Reiniciar dashboard
./dashboard_manager.sh status    # Verificar status
./dashboard_manager.sh logs      # Ver logs em tempo real
./dashboard_manager.sh test      # Testar conectividade
./dashboard_manager.sh cleanup   # Limpeza forçada

# Comandos de serviço systemd
./dashboard_manager.sh install-service  # Instalar serviço
./dashboard_manager.sh service-start    # Iniciar via systemd
./dashboard_manager.sh service-stop     # Parar via systemd
./dashboard_manager.sh service-status   # Status do serviço
```

**Características:**
- ✅ Detecção robusta de processos
- ✅ Independência total do terminal
- ✅ Suporte a systemd
- ✅ Logs centralizados
- ✅ Testes automáticos

### `diagnostico_dashboard.sh` - Diagnóstico Completo
**Script para diagnóstico abrangente do sistema.**

```bash
./diagnostico_dashboard.sh
```

**Verifica:**
- ✅ Status de arquivos e diretórios
- ✅ Processos ativos do dashboard
- ✅ Conectividade de rede (porta 5000)
- ✅ Dependências Python
- ✅ Configuração do banco de dados
- ✅ Logs recentes
- ✅ Configurações essenciais

### `test_persistence.sh` - Teste de Persistência
**Testa se o dashboard funciona independente do terminal.**

```bash
./test_persistence.sh
```

**Funcionalidades:**
- ✅ Inicia dashboard em modo independente
- ✅ Testa conectividade
- ✅ Simula fechamento de terminal
- ✅ Verifica se continua funcionando
- ✅ Relatório detalhado dos testes

## 🌐 Script do Sistema Completo

### `../start_finops.sh` - Sistema Completo
```bash
# Localizado na raiz do projeto
cd /root/finops
./start_finops.sh
```
- Inicia todo o sistema FinOps (não apenas dashboard)
- Verifica dependências (PostgreSQL, Redis, etc.)
- Inicializa múltiplos serviços

## 📊 Uso Recomendado

### Para Administração Diária
```bash
# Use sempre o gerenciador principal
cd /root/finops
./scripts/dashboard_manager.sh start    # Para iniciar
./scripts/dashboard_manager.sh status   # Para verificar
./scripts/dashboard_manager.sh logs     # Para monitorar
```

### Para Resolução de Problemas
```bash
# 1. Diagnóstico completo
./scripts/diagnostico_dashboard.sh

# 2. Se houver problemas, limpeza
./scripts/dashboard_manager.sh cleanup

# 3. Reiniciar
./scripts/dashboard_manager.sh start

# 4. Testar persistência
./scripts/test_persistence.sh
```

### Para Emergências
```bash
# Parar tudo e recomeçar limpo
./scripts/dashboard_manager.sh cleanup
./scripts/dashboard_manager.sh start

# Verificar se funcionou
./scripts/dashboard_manager.sh status
```

## 🔧 Configuração dos Scripts

### Permissões
```bash
# Garantir que scripts são executáveis
chmod +x /root/finops/scripts/*.sh
```

### Variáveis de Ambiente
Os scripts usam estas configurações:
- `FINOPS_ROOT="/root/finops"`
- `DASHBOARD_PORT=5000`
- `LOG_FILE="/root/finops/logs/dashboard.log"`
- `PID_FILE="/root/finops/logs/dashboard.pid"`

### Dependências
- **Python 3** com Flask
- **PostgreSQL** configurado
- **Porta 5000** disponível

## 📝 Logs e Monitoramento

### Localizações
- **Logs principais**: `/root/finops/logs/dashboard.log`
- **PID tracking**: `/root/finops/logs/dashboard.pid`
- **Logs do sistema**: Acessíveis via systemd

### Monitoramento
```bash
# Logs em tempo real
./scripts/dashboard_manager.sh logs

# Últimas linhas
tail -50 /root/finops/logs/dashboard.log

# Buscar erros
grep -i error /root/finops/logs/dashboard.log
```

## 🚨 Resolução de Problemas

### Script não executa
```bash
# Verificar permissões
ls -la /root/finops/scripts/

# Corrigir se necessário
chmod +x /root/finops/scripts/*.sh
```

### Dashboard não inicia
```bash
# Diagnóstico completo
./scripts/diagnostico_dashboard.sh

# Limpeza e restart
./scripts/dashboard_manager.sh cleanup
./scripts/dashboard_manager.sh start
```

### Porta ocupada
```bash
# O cleanup resolve automaticamente
./scripts/dashboard_manager.sh cleanup
```

### Processo não para
```bash
# Força parada de todos os processos relacionados
./scripts/dashboard_manager.sh cleanup
```

## ✅ Funcionalidades dos Scripts

### Detecção de Processos
- ✅ Busca por `run_dashboard.py`
- ✅ Busca por `app.py` diretamente
- ✅ Verificação de porta ativa
- ✅ Validação de PID files

### Independência do Terminal
- ✅ Uso de `setsid` para nova sessão
- ✅ Redirecionamento completo de I/O
- ✅ Detach completo do terminal pai

### Robustez
- ✅ Tratamento de erros abrangente
- ✅ Fallbacks para diferentes cenários
- ✅ Limpeza automática de recursos
- ✅ Validação de estados

## 🎯 Integração com Sistema

### Systemd
```bash
# Instalar serviço (uma vez)
./scripts/dashboard_manager.sh install-service

# Usar serviço
sudo systemctl start finops-dashboard
sudo systemctl status finops-dashboard
```

### Backup
```bash
# Scripts incluídos em backup automático
# Localizados em /root/finops/scripts/
```

### Atualização
```bash
# Scripts auto-contidos
# Basta executar após atualização do código
./scripts/dashboard_manager.sh restart
```

## 📊 Status dos Scripts

```
🟢 dashboard_manager.sh - Funcional e completo (PRINCIPAL)
🟢 diagnostico_dashboard.sh - Completo e abrangente
🟢 test_persistence.sh - Validado e funcional
🟢 ../start_finops.sh - Sistema completo (na raiz)
```

**� Nota sobre limpeza realizada:**
- ✅ Removidos scripts redundantes/defasados (backup em `/backup/scripts_removidos_YYYYMMDD/`)
- ✅ Eliminadas duplicações de funcionalidade
- ✅ Foco nos scripts essenciais e funcionais
- ✅ Estrutura mais limpa e fácil de manter

## 🚀 Próximas Melhorias

- [ ] **Health Checks**: Monitoramento automático
- [ ] **Alertas**: Notificações por email/Slack
- [ ] **Backup Scripts**: Backup automático da aplicação
- [ ] **Performance**: Métricas de performance
- [ ] **Security**: Auditoria de segurança

---

**Para dúvidas ou problemas, execute primeiro:**
```bash
./scripts/diagnostico_dashboard.sh
```
