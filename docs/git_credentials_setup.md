# 🔐 Configuração de Credenciais Git - Guia Completo

## ✅ **Configurações Já Aplicadas**

```bash
# Usuário e email configurados
user.name=marcelo.oliveira
user.email=marcelo.oliveira@service.com.br
credential.helper=store
```

## 🎯 **Como Funciona Agora**

### 1. **Primeira Push/Pull** (Apenas UMA vez)
```bash
cd /root/finops
git push origin main
# Git vai pedir:
# Username: marcelo.oliveira
# Password: [sua_senha_ou_token]
```

### 2. **Próximas Operações** (Automático)
```bash
git push    # ✅ Sem pedir credenciais
git pull    # ✅ Sem pedir credenciais
git fetch   # ✅ Sem pedir credenciais
```

## 📁 **Onde São Armazenadas**

As credenciais ficam em: `~/.git-credentials`
```bash
https://marcelo.oliveira:TOKEN@gitlab.service.com.br
```

## 🔒 **Opções de Autenticação**

### **Opção 1: Personal Access Token (Recomendado)**
1. Acesse: GitLab → User Settings → Access Tokens
2. Crie um token com permissões: `read_repository`, `write_repository`
3. Use o TOKEN como senha

### **Opção 2: Senha da Conta**
- Use sua senha normal do GitLab
- Menos seguro que token

## 🚀 **Testando a Configuração**

```bash
# Ir para o projeto
cd /root/finops

# Verificar status
git status

# Adicionar mudanças
git add .

# Commit
git commit -m "test: Verificando credenciais configuradas"

# Push (primeira vez vai pedir credenciais)
git push

# Próximas vezes será automático!
```

## ⚙️ **Comandos Úteis**

### Ver configurações atuais:
```bash
git config --global --list
```

### Limpar credenciais armazenadas:
```bash
rm ~/.git-credentials
```

### Verificar repositório remoto:
```bash
git remote -v
```

### Alterar URL do repositório (se necessário):
```bash
git remote set-url origin https://gitlab.service.com.br/devops-serviceit/finops.git
```

## 🛡️ **Segurança**

### ✅ **Boas Práticas:**
- Use Personal Access Tokens em vez de senhas
- Tokens têm escopo limitado
- Podem ser revogados facilmente
- Têm data de expiração

### ⚠️ **Cuidados:**
- Arquivo `~/.git-credentials` contém credenciais em texto plano
- Mantenha permissões restritas: `chmod 600 ~/.git-credentials`
- Não compartilhe o arquivo

## 🔄 **Alternativas Mais Seguras**

### **SSH Keys (Mais Seguro)**
```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "marcelo.oliveira@service.com.br"

# Adicionar ao GitLab
cat ~/.ssh/id_ed25519.pub

# Mudar URL para SSH
git remote set-url origin git@gitlab.service.com.br:devops-serviceit/finops.git
```

### **Git Credential Manager (Empresarial)**
```bash
# Para ambientes empresariais
git config --global credential.helper manager-core
```

## 🎯 **Próximos Passos**

1. **✅ CONCLUÍDO**: Credenciais configuradas e testadas
2. **✅ CONCLUÍDO**: 3 pushes realizados automaticamente
3. **✅ CONCLUÍDO**: Dashboard gerenciado via `/root/finops/dashboard_manager.sh`

### 📊 **Comandos do Dashboard:**
```bash
# Verificar status
/root/finops/dashboard_manager.sh status

# Parar dashboard
/root/finops/dashboard_manager.sh stop

# Iniciar dashboard  
/root/finops/dashboard_manager.sh start

# Reiniciar dashboard
/root/finops/dashboard_manager.sh restart

# Ver logs
/root/finops/dashboard_manager.sh logs

# Testar funcionamento
/root/finops/dashboard_manager.sh test
```

---
**Configurado por**: marcelo.oliveira  
**Data**: 07/08/2025  
**Status**: ✅ Credenciais configuradas e dashboard gerenciado automaticamente
