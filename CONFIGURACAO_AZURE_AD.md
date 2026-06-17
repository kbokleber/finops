# Configuração Azure AD - Dashboard FinOps

> **📘 Para deploy em produção, consulte:** [DEPLOY_AZURE_AD.md](./DEPLOY_AZURE_AD.md)

## ✅ Configuração Realizada (Ambiente de Desenvolvimento)

### 1. Credenciais do Azure AD
As seguintes credenciais foram configuradas no arquivo `/root/finops/dashboard/.env`:

- **Client ID**: `<seu-client-id>`
- **Client Secret**: `<seu-client-secret>`
- **Tenant ID**: `<seu-tenant-id>`
- **Secret ID**: `<seu-secret-id>`

### 2. Alterações nos Arquivos

#### `/root/finops/dashboard/.env`
```env
# Controle de Autenticação
ENABLE_AZURE_AUTH=true

# Configurações do Azure AD (preencher com suas credenciais reais)
AZURE_CLIENT_ID=<seu-client-id>
AZURE_CLIENT_SECRET=<seu-client-secret>
AZURE_TENANT_ID=<seu-tenant-id>
```

### 3. Status das Dependências
- ✅ **MSAL**: v1.33.0 (Microsoft Authentication Library)
- ✅ **Flask**: v3.1.1
- ✅ **Flask-Session**: Instalado
- ✅ **python-dotenv**: v1.1.1
- ✅ **psycopg2**: Instalado

### 4. Status do Dashboard
- ✅ **Ambiente Virtual**: Ativo em `/root/finops/dashboard_env/`
- ✅ **Configuração**: Carregada com sucesso
- ✅ **Servidor**: Rodando em http://localhost:5000 e http://178.156.185.182:5000
- ✅ **Autenticação**: Habilitada e funcionando

## 🔗 URLs de Redirecionamento

### URLs que devem estar configuradas no Azure AD:
1. **Desenvolvimento/Local**:
   - `http://localhost:5000/auth/callback`
   - `http://127.0.0.1:5000/auth/callback`

2. **Produção** (baseado no proxy NGINX):
   - `https://devmonitorfinops.service.com.br/auth/callback`

### URLs de Logout:
1. **Desenvolvimento/Local**:
   - `http://localhost:5000/`
   - `http://127.0.0.1:5000/`

2. **Produção**:
   - `https://devmonitorfinops.service.com.br/`

## 🚀 Como Usar

### 1. Iniciar o Dashboard
```bash
cd /root/finops
source dashboard_env/bin/activate
python dashboard/start_dashboard.py
```

### 2. Acessar o Dashboard
- **Local**: http://localhost:5000
- **Produção**: https://devmonitorfinops.service.com.br

### 3. Processo de Login
1. Acesse a URL do dashboard
2. Será redirecionado para a página de login
3. Clique em "Entrar com Microsoft"
4. Será redirecionado para o Azure AD
5. Faça login com suas credenciais corporativas
6. Após autorização, retornará ao dashboard logado

## ⚙️ Configurações no Azure AD

### URLs de Redirecionamento Necessárias
No portal do Azure AD, na aplicação `<seu-client-id>`, configure:

**Authentication > Redirect URIs > Web**:
- `http://localhost:5000/auth/callback` (desenvolvimento)
- `https://devmonitorfinops.service.com.br/auth/callback` (produção)

**Authentication > Logout URLs**:
- `http://localhost:5000/` (desenvolvimento)
- `https://devmonitorfinops.service.com.br/` (produção)

### Permissões Necessárias
- **Microsoft Graph**: `User.ReadBasic.All` (Delegated)

## 🔧 Troubleshooting

### 1. Erro de Redirect URI
Se ocorrer erro de URI de redirecionamento:
- Verifique se as URLs estão configuradas no Azure AD
- Certifique-se de que não há barras extras no final das URLs

### 2. Erro de Permissões
Se ocorrer erro de permissões:
- Verifique se o aplicativo tem as permissões corretas no Azure AD
- Pode ser necessário consentimento do administrador

### 3. Problema com Certificados SSL
Para produção, certifique-se de que:
- O certificado SSL está válido
- O domínio corresponde ao certificado

### 4. Dashboard Mostrando "Usuário Demo"
Se o dashboard mostrar "Usuário Demo" mesmo com autenticação habilitada:
- Limpe as sessões antigas: `rm -rf /root/finops/dashboard/flask_session/*`
- Reinicie o serviço: `sudo systemctl restart finops-dashboard`
- Acesse em nova aba/janela privada do navegador

### 5. Serviço SystemD
Se o serviço parar de funcionar:
- Verifique o status: `sudo systemctl status finops-dashboard`
- Reinicie: `sudo systemctl restart finops-dashboard`
- Veja os logs: `tail -f /root/finops/dashboard/dashboard.log`

### 6. Para Voltar ao Modo Demo
Caso precise desabilitar temporariamente:
```env
ENABLE_AZURE_AUTH=false
```
E reinicie o serviço: `sudo systemctl restart finops-dashboard`

## 📋 Próximos Passos

1. **Testar Login**: Verificar se o login funciona corretamente
2. **Configurar Produção**: Ajustar URLs para ambiente de produção
3. **Verificar Permissões**: Garantir que usuários adequados têm acesso
4. **Monitoramento**: Acompanhar logs de autenticação

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs do dashboard
2. Verifique as configurações do Azure AD
3. Confirme se todas as URLs estão corretas
4. Teste primeiro em ambiente local

---
**Data da Configuração**: 17 de Outubro de 2025
**Status**: ✅ Configurado e Funcionando