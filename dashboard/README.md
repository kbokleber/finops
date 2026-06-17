# Dashboard FinOps com Autenticação Azure AD

Dashboard para monitoramento de custos cloud com autenticação segura via Azure AD.

## 🚀 Recursos

- **Autenticação Azure AD**: Login seguro com Microsoft
- **Monitoramento OCI**: Status de provedores Oracle Cloud
- **Análise de Custos**: Visualização de dados processados
- **Status Docker**: Monitoramento de containers
- **Jobs Celery**: Status de processamento em tempo real
- **Interface Responsiva**: Bootstrap 5 com design moderno

## 📋 Pré-requisitos

1. **Python 3.8+**
2. **Aplicação registrada no Azure AD**
3. **Banco PostgreSQL configurado**
4. **Docker** (para monitoramento de containers)

## ⚙️ Configuração do Azure AD

### 1. Registrar Aplicação no Azure Portal

1. Acesse o [Azure Portal](https://portal.azure.com)
2. Vá para **Azure Active Directory** > **App registrations**
3. Clique em **New registration**
4. Configure:
   - **Name**: Dashboard FinOps
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Web - `http://localhost:5000/auth/callback`

### 2. Configurar Permissões

1. Na aplicação criada, vá para **API permissions**
2. Adicione as seguintes permissões:
   - Microsoft Graph > Delegated > User.Read
   - Microsoft Graph > Delegated > User.ReadBasic.All

### 3. Obter Credenciais

1. **Client ID**: Disponível na página Overview
2. **Tenant ID**: Disponível na página Overview  
3. **Client Secret**: Em **Certificates & secrets** > **New client secret**

## 🔧 Instalação

### 1. Instalar Dependências

```bash
cd /root/finops/dashboard
pip install -r ../requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

Configure no arquivo `.env`:

```env
# Azure AD
AZURE_CLIENT_ID=seu-client-id-aqui
AZURE_CLIENT_SECRET=seu-client-secret-aqui
AZURE_TENANT_ID=seu-tenant-id-aqui

# Flask
SECRET_KEY=sua-chave-secreta-muito-segura-aqui
FLASK_ENV=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=svc_finops
DB_PASSWORD=sua-senha-aqui
DB_NAME=finopsdatabase
```

### 3. Executar Dashboard

```bash
# Usando o script de inicialização (recomendado)
python start_dashboard.py

# Ou executar diretamente
python app.py
```

## 🌐 Acesso

1. Abra o navegador em: `http://localhost:5000`
2. Clique em **Entrar com Microsoft**
3. Faça login com sua conta Azure AD
4. Será redirecionado para o dashboard

## 🔒 Funcionalidades de Segurança

- **Sessões seguras**: Todas as sessões são protegidas
- **Middleware de autenticação**: Todas as rotas são protegidas
- **Logout seguro**: Limpa sessão local e redireciona para Azure
- **APIs protegidas**: Todas as APIs verificam autenticação

## 📊 Funcionalidades do Dashboard

### Cards de Resumo
- Número de provedores OCI configurados
- Jobs restantes para processamento
- Registros processados hoje
- Custo total do dia

### Tabelas de Dados
- Status detalhado dos provedores OCI
- Dados processados nos últimos 7 dias
- Informações de containers Docker
- Status do Celery e workers

### Monitoramento em Tempo Real
- Atualização automática a cada 30 segundos
- Indicadores visuais de status
- Logs de containers em tempo real

## 🛠️ Estrutura do Projeto

```
dashboard/
├── app.py                 # Aplicação principal Flask
├── auth.py               # Módulo de autenticação Azure AD
├── config.py             # Configurações da aplicação
├── start_dashboard.py    # Script de inicialização
├── .env.example         # Exemplo de variáveis de ambiente
├── routes/
│   └── auth_routes.py   # Rotas de autenticação
└── templates/
    ├── dashboard.html   # Template principal
    └── login.html       # Página de login
```

## 🔧 Desenvolvimento

### Modo Debug
O dashboard executa em modo debug por padrão em desenvolvimento:

```python
FLASK_ENV=development  # No arquivo .env
```

### Logs
Logs de erro são exibidos no console durante desenvolvimento.

### Customização
- Estilos CSS podem ser modificados nos templates
- Novas funcionalidades podem ser adicionadas via blueprints
- APIs podem ser estendidas no `app.py`

## 🚨 Solução de Problemas

### Erro de Autenticação
1. Verifique se as credenciais Azure AD estão corretas
2. Confirme se a URL de redirect está configurada no Azure
3. Verifique se as permissões estão concedidas

### Erro de Banco de Dados
1. Confirme se o PostgreSQL está rodando
2. Verifique as credenciais do banco no `.env`
3. Teste a conexão manualmente

### Erro de Containers
1. Verifique se o Docker está rodando
2. Confirme se os containers finops estão ativos
3. Verifique os logs dos containers

## 📱 Acesso Móvel

O dashboard é responsivo e funciona em dispositivos móveis através do Bootstrap 5.

## 🔄 Atualizações Automáticas

O dashboard atualiza automaticamente os dados a cada 30 segundos, incluindo:
- Status dos provedores OCI
- Dados de processamento
- Status de containers
- Informações do Celery

## 📞 Suporte

Para suporte técnico ou dúvidas sobre a implementação, consulte a documentação do projeto ou entre em contato com a equipe de desenvolvimento.
