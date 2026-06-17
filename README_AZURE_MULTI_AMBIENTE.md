# 🔐 Azure AD - Configuração Multi-Ambiente

## 📁 Estrutura de Configuração

```
finops/
├── dashboard/
│   ├── .env                    # ❌ Específico do servidor (NÃO versionar)
│   ├── .env.example           # ✅ Template genérico (versionado)
│   ├── .env.production        # ✅ Template de PRD (versionado)
│   └── config.py              # ✅ Configuração dinâmica (versionado)
├── .gitignore                  # ✅ Protege .env
├── CONFIGURACAO_AZURE_AD.md   # 📘 Configuração inicial (DEV)
├── DEPLOY_AZURE_AD.md         # 📘 Guia completo de deploy
└── deploy_to_production.sh    # 🚀 Script auxiliar de deploy
```

## 🎯 Ambientes

### Desenvolvimento (178.156.185.182)
- **Domínio:** devmonitorfinops.service.com.br
- **Arquivo:** `/root/finops/dashboard/.env`
- **FLASK_ENV:** development
- **Azure Auth:** ✅ Habilitado

### Produção (65.109.154.172)
- **Domínio:** monitorfinops.service.com.br
- **Arquivo:** `/root/finops/dashboard/.env` (criar do template)
- **FLASK_ENV:** production
- **Azure Auth:** ✅ Habilitado

## 🚀 Quick Start - Deploy em Produção

### Opção 1: Script Automatizado (Recomendado)

```bash
ssh root@65.109.154.172
cd /root/finops
./deploy_to_production.sh
```

### Opção 2: Manual

```bash
ssh root@65.109.154.172
cd /root/finops

# 1. Criar .env a partir do template
cp dashboard/.env.production dashboard/.env

# 2. Gerar SECRET_KEY única
python3 -c "import secrets; print(secrets.token_hex(32))"

# 3. Editar .env e colar a SECRET_KEY gerada
nano dashboard/.env

# 4. Reiniciar dashboard
sudo systemctl restart finops-dashboard
```

## 📋 Configuração Azure AD

No [Portal Azure](https://portal.azure.com), adicionar URLs:

### Redirect URIs:
```
https://devmonitorfinops.service.com.br/auth/callback   (DEV)
https://monitorfinops.service.com.br/auth/callback      (PRD)
```

### Logout URLs:
```
https://devmonitorfinops.service.com.br/   (DEV)
https://monitorfinops.service.com.br/      (PRD)
```

## 🔄 Workflow Git

### Arquivos Versionados (Git)
✅ `.env.example` - Template genérico  
✅ `.env.production` - Template PRD (sem secrets)  
✅ `config.py` - Código de configuração  
✅ `DEPLOY_AZURE_AD.md` - Documentação  

### Arquivos NÃO Versionados
❌ `.env` - Configuração local/específica  
❌ `*.log` - Logs  
❌ `flask_session/` - Sessões  

### Commit e Push

```bash
cd /root/finops

# Adicionar apenas templates e código
git add dashboard/.env.example
git add dashboard/.env.production
git add dashboard/config.py
git add DEPLOY_AZURE_AD.md
git add deploy_to_production.sh
git add .gitignore

# Commit
git commit -m "feat: Configuração multi-ambiente Azure AD"

# Push
git push origin main
```

### Atualizar Produção

```bash
ssh root@65.109.154.172
cd /root/finops

# Backup do .env local
cp dashboard/.env dashboard/.env.backup

# Atualizar código
git pull origin main

# Restaurar .env local
cp dashboard/.env.backup dashboard/.env

# Reiniciar
sudo systemctl restart finops-dashboard
```

## 📚 Documentação Completa

- **Configuração Inicial:** [CONFIGURACAO_AZURE_AD.md](./CONFIGURACAO_AZURE_AD.md)
- **Guia de Deploy:** [DEPLOY_AZURE_AD.md](./DEPLOY_AZURE_AD.md)

## ✅ Checklist

### Servidor DEV (178.156.185.182)
- [x] `.env` configurado
- [x] Azure AD URLs configuradas
- [x] Dashboard funcionando
- [x] Código versionado no Git

### Servidor PRD (65.109.154.172)
- [ ] Código atualizado do Git
- [ ] `.env` criado do template
- [ ] `SECRET_KEY` única gerada
- [ ] Azure AD URLs configuradas
- [ ] Dashboard reiniciado
- [ ] Teste de login realizado

## 🆘 Suporte

**Erro de Redirect URI:**
→ Verificar URLs no Portal Azure

**Dashboard não inicia:**
→ `tail -f /root/finops/dashboard/dashboard.log`

**Problemas de sessão:**
→ `rm -rf /root/finops/dashboard/flask_session/*`

---

**Última atualização:** Novembro 2025
