# 🚀 Guia de Deploy - FinOps Dashboard com Azure AD

## 📋 Pré-requisitos

Antes de iniciar o deploy, certifique-se de ter:

- ✅ Acesso ao Portal Azure com permissões para gerenciar App Registrations
- ✅ Acesso SSH aos servidores (DEV e PRD)
- ✅ PostgreSQL configurado e rodando
- ✅ NGINX configurado com SSL/HTTPS

---

## 🔧 Configuração no Azure AD

### 1. URLs de Redirecionamento

No [Portal Azure](https://portal.azure.com) → **Azure Active Directory** → **App registrations** → Sua aplicação (`<seu-client-id>`):

#### **Authentication > Redirect URIs > Web**
Adicione as seguintes URLs:

```
✅ DESENVOLVIMENTO
https://devmonitorfinops.service.com.br/auth/callback
http://localhost:5000/auth/callback

✅ PRODUÇÃO  
https://monitorfinops.service.com.br/auth/callback
```

#### **Authentication > Logout URLs**
Adicione:

```
✅ DESENVOLVIMENTO
https://devmonitorfinops.service.com.br/

✅ PRODUÇÃO
https://monitorfinops.service.com.br/
```

### 2. Permissões da API

Certifique-se de que as seguintes permissões estão configuradas:

- **Microsoft Graph** → `User.ReadBasic.All` (Delegated)

---

## 🖥️ Deploy no Servidor de Produção (65.109.154.172)

### Passo 1: Conectar ao Servidor de Produção

```bash
ssh root@65.109.154.172
```

### Passo 2: Acessar o Diretório do Projeto

```bash
cd /root/finops/dashboard
```

### Passo 3: Criar o Arquivo .env de Produção

```bash
# Copiar o template de produção
cp .env.production .env

# Editar o arquivo .env
nano .env
```

**IMPORTANTE:** Gere uma SECRET_KEY única para produção:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e substitua em `SECRET_KEY=` no arquivo `.env`

### Passo 4: Configurar o .env de Produção

Edite `/root/finops/dashboard/.env` com os seguintes valores:

```bash
# Ambiente
FLASK_ENV=production
SERVER_DOMAIN=monitorfinops.service.com.br

# Azure AD (usar as mesmas credenciais)
ENABLE_AZURE_AUTH=true
AZURE_CLIENT_ID=<seu-client-id>
AZURE_CLIENT_SECRET=<seu-client-secret>
AZURE_TENANT_ID=<seu-tenant-id>

# Segurança (GERAR NOVO!)
SECRET_KEY=<cole-aqui-a-chave-gerada>

# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_USER=svc_finops
DB_PASSWORD=<sua-senha-do-banco>
DB_NAME=finopsdatabase
```

### Passo 5: Ativar Ambiente Virtual e Instalar Dependências

```bash
# Ativar ambiente virtual (se não estiver ativo)
cd /root/finops
source dashboard_env/bin/activate

# Verificar dependências do Azure
pip list | grep msal
```

Se o MSAL não estiver instalado:

```bash
pip install msal==1.33.0 python-dotenv==1.1.1
```

### Passo 6: Testar a Configuração

```bash
# Testar se as variáveis estão carregando
cd /root/finops/dashboard
python3 -c "
from config import Config
print(f'Azure Auth: {Config.ENABLE_AZURE_AUTH}')
print(f'Client ID: {Config.CLIENT_ID[:10]}...')
print(f'Server: {Config.SERVER_NAME}')
print(f'Environment: {Config.FLASK_ENV}')
"
```

### Passo 7: Reiniciar o Dashboard

```bash
# Parar o dashboard atual
pkill -f "python.*dashboard"

# Ou usar o serviço systemd se configurado
sudo systemctl restart finops-dashboard

# Ou iniciar manualmente
cd /root/finops
source dashboard_env/bin/activate
python dashboard/start_dashboard.py
```

### Passo 8: Verificar Logs

```bash
# Verificar se iniciou corretamente
tail -f /root/finops/dashboard/dashboard.log

# Ou ver logs do systemd
sudo journalctl -u finops-dashboard -f
```

---

## 🧪 Testes Pós-Deploy

### 1. Testar Acesso Local

No servidor de produção:

```bash
curl -I http://localhost:5000
```

Deve retornar `302 Found` (redirecionamento para login)

### 2. Testar Acesso Externo

Em qualquer navegador:

```
https://monitorfinops.service.com.br
```

Deve:
1. ✅ Redirecionar para página de login
2. ✅ Mostrar botão "Entrar com Microsoft"
3. ✅ Redirecionar para login.microsoftonline.com
4. ✅ Após login, retornar ao dashboard

### 3. Verificar Logs de Autenticação

```bash
grep "Azure AD" /root/finops/dashboard/dashboard.log
```

---

## 📁 Estrutura de Arquivos

```
/root/finops/dashboard/
├── .env                    # ❌ NÃO versionar (específico de cada servidor)
├── .env.example           # ✅ Template genérico (versionado no Git)
├── .env.production        # ✅ Template de PRD (versionado no Git)
├── config.py              # ✅ Configuração dinâmica (versionado no Git)
├── auth.py                # ✅ Lógica de autenticação (versionado no Git)
└── ...
```

### Arquivos Versionados no Git
- ✅ `.env.example` - Template genérico
- ✅ `.env.production` - Template de produção (sem credenciais reais)
- ✅ `config.py` - Configuração dinâmica
- ✅ Todo código Python

### Arquivos NÃO Versionados (protegidos pelo .gitignore)
- ❌ `.env` - Configuração específica de cada servidor
- ❌ `*.log` - Logs
- ❌ `flask_session/` - Sessões
- ❌ `__pycache__/` - Cache Python

---

## 🔄 Workflow Git Recomendado

### No Servidor de DESENVOLVIMENTO

```bash
cd /root/finops

# Adicionar apenas os arquivos template
git add dashboard/.env.example
git add dashboard/.env.production
git add dashboard/config.py
git add .gitignore

# Fazer commit
git commit -m "feat: Configuração multi-ambiente para Azure AD

- Criado .env.example como template genérico
- Criado .env.production para ambiente de produção
- Atualizado config.py para usar SERVER_DOMAIN dinâmico
- Garantido que .env local não seja versionado
"

# Enviar para repositório
git push origin main
```

### No Servidor de PRODUÇÃO

```bash
cd /root/finops

# Fazer backup do .env local (se existir)
cp dashboard/.env dashboard/.env.backup 2>/dev/null || true

# Atualizar código do Git
git pull origin main

# Restaurar .env local ou criar novo
if [ -f dashboard/.env.backup ]; then
    cp dashboard/.env.backup dashboard/.env
else
    cp dashboard/.env.production dashboard/.env
    # EDITAR o .env com as configurações corretas
    nano dashboard/.env
fi

# Reiniciar serviço
sudo systemctl restart finops-dashboard
```

---

## 🔐 Segurança

### ⚠️ IMPORTANTE - Gestão de Credenciais

1. **NUNCA** comitar o arquivo `.env` no Git
2. **SEMPRE** usar `.env.example` como template
3. **GERAR** uma `SECRET_KEY` única para cada ambiente
4. **ROTACIONAR** as credenciais Azure periodicamente
5. **USAR** variáveis de ambiente diferentes para DEV e PRD

### Gerar Nova SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Verificar se .env está protegido

```bash
cd /root/finops
git check-ignore dashboard/.env
```

Deve retornar: `dashboard/.env` ✅

---

## 🎯 Diferenças entre Ambientes

| Item | DESENVOLVIMENTO | PRODUÇÃO |
|------|-----------------|----------|
| **Servidor** | 178.156.185.182 | 65.109.154.172 |
| **Domínio** | devmonitorfinops.service.com.br | monitorfinops.service.com.br |
| **FLASK_ENV** | development | production |
| **DEBUG** | true | false |
| **SECRET_KEY** | Chave de DEV | ⚠️ CHAVE ÚNICA |
| **Credenciais Azure** | Mesmas | Mesmas |
| **Redirect URL** | https://devmonitorfinops.../auth/callback | https://monitorfinops.../auth/callback |

---

## 🆘 Troubleshooting

### Erro: "Redirect URI mismatch"

**Causa:** URL de callback não está configurada no Azure AD

**Solução:**
1. Acesse o Portal Azure
2. Vá em App registrations → Authentication
3. Adicione a URL: `https://monitorfinops.service.com.br/auth/callback`

### Erro: "Invalid client secret"

**Causa:** SECRET_KEY do Azure expirou ou está incorreta

**Solução:**
1. No Portal Azure, gere um novo Client Secret
2. Atualize `AZURE_CLIENT_SECRET` no `.env`
3. Reinicie o dashboard

### Dashboard não inicia

**Causa:** Erro de configuração no `.env`

**Solução:**
```bash
# Verificar sintaxe do .env
cat /root/finops/dashboard/.env

# Testar carregamento
cd /root/finops/dashboard
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ENABLE_AZURE_AUTH'))"
```

### Página em branco após login

**Causa:** Sessão Flask não está persistindo

**Solução:**
```bash
# Limpar sessões antigas
rm -rf /root/finops/dashboard/flask_session/*

# Reiniciar dashboard
sudo systemctl restart finops-dashboard
```

---

## 📞 Suporte

Para problemas ou dúvidas:

1. Verificar logs: `tail -f /root/finops/dashboard/dashboard.log`
2. Verificar documentação: `/root/finops/CONFIGURACAO_AZURE_AD.md`
3. Consultar este guia de deploy

---

## ✅ Checklist de Deploy

- [ ] URLs configuradas no Azure AD (DEV + PRD)
- [ ] Arquivo `.env` criado no servidor de produção
- [ ] `SECRET_KEY` única gerada para produção
- [ ] Dependências Python instaladas (msal, python-dotenv)
- [ ] Dashboard reiniciado
- [ ] Teste de login realizado com sucesso
- [ ] Logs verificados (sem erros)
- [ ] Código versionado no Git (apenas templates)
- [ ] `.env` local NÃO versionado

---

**Última atualização:** Novembro 2025  
**Versão:** 2.0
