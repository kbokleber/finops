# 📚 Documentação FinOps

## 📋 Índice Geral

### 🚀 Início Rápido
- [Instalação e Configuração](INSTALLATION.md)
- [Gerenciamento do Dashboard](DASHBOARD_MANAGEMENT.md)
- [Configuração Azure AD](AZURE_AUTH_SETUP.md)

### 🔧 Administração
- [Scripts de Gerenciamento](../scripts/README.md)
- [Resolução de Problemas](TROUBLESHOOTING.md)
- [Arquitetura do Sistema](ARCHITECTURE.md)

### 📝 Histórico
- [Changelog Principal](../CHANGELOG.md)
- [Changelog Dashboard](CHANGELOG_DASHBOARD.md)

### 🛠️ Desenvolvimento
- [Estrutura do Projeto](PROJECT_STRUCTURE.md)
- [Guia de Contribuição](CONTRIBUTING.md)

## 🎯 Links Rápidos

### ⚡ Comandos Essenciais
```bash
# Iniciar dashboard
cd /root/finops
./scripts/dashboard_manager.sh start

# Verificar status
./scripts/dashboard_manager.sh status

# Ver logs
./scripts/dashboard_manager.sh logs

# Diagnóstico completo
./scripts/diagnostico_dashboard.sh
```

### 🌐 Acesso
- **Dashboard**: http://localhost:5000
- **Logs**: `/root/finops/logs/dashboard.log`
- **Configurações**: `/root/finops/config/`

## 📊 Status do Sistema

- ✅ **Dashboard**: Funcionando independente do terminal
- ✅ **Autenticação**: Modo bypass ativo (Azure AD preparado)
- ✅ **Dados**: Timezone corrigido, contagens precisas
- ✅ **Gestão**: Scripts completos de gerenciamento

## 🆘 Suporte Rápido

### 🚨 Problemas Comuns
1. **Dashboard não inicia**: `./scripts/dashboard_manager.sh cleanup && ./scripts/dashboard_manager.sh start`
2. **Porta ocupada**: `./scripts/dashboard_manager.sh cleanup`
3. **Dados incorretos**: Verificar [Troubleshooting](TROUBLESHOOTING.md)
4. **Timezone errado**: Já corrigido automaticamente

### 📞 Para Mais Ajuda
- Consulte [Troubleshooting](TROUBLESHOOTING.md)
- Execute `./scripts/diagnostico_dashboard.sh`
- Verifique logs em `/root/finops/logs/`
