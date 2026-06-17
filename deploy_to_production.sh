#!/bin/bash
# ==============================================================================
# Script de Deploy - FinOps Dashboard com Azure AD
# ==============================================================================
# Uso: ./deploy_to_production.sh
# ==============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo ""
echo "======================================================================"
echo "  FinOps Dashboard - Deploy para Produção"
echo "======================================================================"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "dashboard/.env.production" ]; then
    log_error "Arquivo dashboard/.env.production não encontrado!"
    log_info "Execute este script a partir do diretório /root/finops"
    exit 1
fi

# Verificar se já existe um .env
if [ -f "dashboard/.env" ]; then
    log_warning "Arquivo dashboard/.env já existe!"
    echo ""
    read -p "Deseja fazer backup e substituir? [s/N]: " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        BACKUP_FILE="dashboard/.env.backup.$(date +%Y%m%d_%H%M%S)"
        cp dashboard/.env "$BACKUP_FILE"
        log_success "Backup criado: $BACKUP_FILE"
    else
        log_info "Deploy cancelado pelo usuário"
        exit 0
    fi
fi

# Copiar template de produção
log_info "Copiando template de produção..."
cp dashboard/.env.production dashboard/.env
log_success "Template copiado para dashboard/.env"

# Gerar SECRET_KEY
log_info "Gerando SECRET_KEY única para produção..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
log_success "SECRET_KEY gerada: ${SECRET_KEY:0:20}..."

# Atualizar SECRET_KEY no .env
sed -i "s/SECRET_KEY=GERAR_UMA_CHAVE_UNICA_AQUI/SECRET_KEY=$SECRET_KEY/" dashboard/.env
log_success "SECRET_KEY atualizada no .env"

echo ""
log_warning "ATENÇÃO: Verifique as seguintes configurações no arquivo .env:"
echo ""
echo "  1. SERVER_DOMAIN - Deve ser o domínio de produção"
echo "  2. DB_PASSWORD - Verifique se a senha do banco está correta"
echo "  3. AZURE_* - Credenciais do Azure AD"
echo ""
read -p "Deseja editar o arquivo .env agora? [S/n]: " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    ${EDITOR:-nano} dashboard/.env
fi

# Verificar configuração
log_info "Verificando configuração..."

# Ativar ambiente virtual se existir
if [ -d "dashboard_env" ]; then
    source dashboard_env/bin/activate
    log_success "Ambiente virtual ativado"
fi

# Testar se as variáveis carregam corretamente
log_info "Testando carregamento de variáveis..."
python3 << EOF
import sys
sys.path.insert(0, 'dashboard')
try:
    from config import Config
    assert Config.ENABLE_AZURE_AUTH == True, "ENABLE_AZURE_AUTH deve ser true"
    assert Config.CLIENT_ID, "AZURE_CLIENT_ID não pode estar vazio"
    assert Config.FLASK_ENV == 'production', "FLASK_ENV deve ser production"
    assert Config.SECRET_KEY != 'GERAR_UMA_CHAVE_UNICA_AQUI', "SECRET_KEY deve ser atualizada"
    print("✓ Todas as configurações estão corretas!")
except Exception as e:
    print(f"✗ Erro na configuração: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    log_success "Configuração validada com sucesso!"
else
    log_error "Erro na validação da configuração"
    exit 1
fi

# Verificar dependências
log_info "Verificando dependências do Python..."
pip list | grep -E "msal|python-dotenv|Flask" > /dev/null
if [ $? -eq 0 ]; then
    log_success "Dependências instaladas"
else
    log_warning "Algumas dependências podem estar faltando"
    read -p "Deseja instalar as dependências agora? [S/n]: " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        pip install msal==1.33.0 python-dotenv==1.1.1 Flask==3.1.1
        log_success "Dependências instaladas"
    fi
fi

echo ""
echo "======================================================================"
log_success "Deploy preparado com sucesso!"
echo "======================================================================"
echo ""
log_info "Próximos passos:"
echo ""
echo "  1. Configure as URLs no Azure AD Portal:"
echo "     https://monitorfinops.service.com.br/auth/callback"
echo ""
echo "  2. Reinicie o dashboard:"
echo "     sudo systemctl restart finops-dashboard"
echo "     # ou"
echo "     python dashboard/start_dashboard.py"
echo ""
echo "  3. Teste o acesso:"
echo "     https://monitorfinops.service.com.br"
echo ""
log_info "Documentação completa: /root/finops/DEPLOY_AZURE_AD.md"
echo ""
