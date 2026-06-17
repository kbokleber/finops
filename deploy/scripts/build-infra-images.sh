#!/bin/bash
# =============================================================================
# build-infra-images.sh
# Builda e pusha as 3 imagens da stack de INFRA para o registry do Coolify.
#
# USO:
#   ./deploy/scripts/build-infra-images.sh                    # builda tudo
#   ./deploy/scripts/build-infra-images.sh postgres           # builda soh postgres
#   ./deploy/scripts/build-infra-images.sh redis rabbitmq     # builda redis e rabbitmq
#
# VARIAVEIS DE AMBIENTE OBRIGATORIAS:
#   COOLIFY_REGISTRY   ex: "registry.seu-servidor.com/seu-projeto" ou
#                           "ghcr.io/kbokleber" ou
#                           "docker.io/kbokleber"
#
# Quando o registry eh o proprio Coolify (Coolify Cloud v4+), o endereco
# segue o padrao:  registry.<host-coolify>/<project-slug>
# Exemplo: COOLIFY_REGISTRY=registry.125.123.45.10.sslip.io/finops
#
# ROTEIRO:
#   1. Rode este script 1x NA SUA MAQUINA (ou em qualquer host com Docker).
#   2. O build da imagem do postgres demora ~10-15min (compila pg_repack).
#   3. Apos o push, no Coolify:
#      - Crie a stack "finops-infra" usando docker-compose.infra.yml
#      - Aponte o COOLIFY_REGISTRY para o registry onde voce pushou
#   4. Em deploys futuros do app, NAO eh necessario rebuildar essas imagens.
# =============================================================================

set -e

COOLIFY_REGISTRY="${COOLIFY_REGISTRY:?Defina COOLIFY_REGISTRY (ex: registry.x.com/finops)}"

# Diretorio raiz do repo (onde o docker/ esta).
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

build_postgres() {
    echo ">>> [1/3] Buildando postgres:17 (com pg_repack + pg_partman)..."
    echo "    Isso pode demorar ~10-15 min na primeira vez (compila pg_repack)."
    docker build \
        --tag "${COOLIFY_REGISTRY}/postgres:17" \
        --file docker/postgres/Dockerfile \
        .
    echo ">>> [1/3] Pushando ${COOLIFY_REGISTRY}/postgres:17..."
    docker push "${COOLIFY_REGISTRY}/postgres:17"
}

build_redis() {
    echo ">>> [2/3] Buildando redis:7 (combinando configuracoes)..."
    # Redis nao precisa de Dockerfile custom, mas renomeamos para finops/redis:7
    # para consistencia com as outras imagens. Usa a imagem oficial como base
    # mas cria uma tag nossa para que o COOLIFY_REGISTRY funcione uniforme.
    cat > /tmp/redis.Dockerfile <<'EOF'
FROM redis:7-alpine
# Configuracao padrao com appendonly (durabilidade).
CMD ["redis-server", "--appendonly", "yes"]
EOF
    docker build \
        --tag "${COOLIFY_REGISTRY}/redis:7" \
        --file /tmp/redis.Dockerfile \
        /tmp
    rm -f /tmp/redis.Dockerfile
    echo ">>> [2/3] Pushando ${COOLIFY_REGISTRY}/redis:7..."
    docker push "${COOLIFY_REGISTRY}/redis:7"
}

build_rabbitmq() {
    echo ">>> [3/3] Buildando rabbitmq:3 (com painel de gestao)..."
    cat > /tmp/rabbitmq.Dockerfile <<'EOF'
FROM rabbitmq:3-management
# Imagem oficial com plugin de management ja habilitado na porta 15672.
EOF
    docker build \
        --tag "${COOLIFY_REGISTRY}/rabbitmq:3" \
        --file /tmp/rabbitmq.Dockerfile \
        /tmp
    rm -f /tmp/rabbitmq.Dockerfile
    echo ">>> [3/3] Pushando ${COOLIFY_REGISTRY}/rabbitmq:3..."
    docker push "${COOLIFY_REGISTRY}/rabbitmq:3"
}

# Filtra o que o usuario pediu (ou tudo, se vazio)
TARGETS="${@:-postgres redis rabbitmq}"

for target in $TARGETS; do
    case $target in
        postgres)  build_postgres ;;
        redis)     build_redis ;;
        rabbitmq)  build_rabbitmq ;;
        *)
            echo "AVISO: target '$target' desconhecido. Opcoes: postgres, redis, rabbitmq." >&2
            exit 1
            ;;
    esac
done

echo ""
echo "=================================================="
echo "IMAGENS BUILDADAS E PUSHADAS:"
echo "  - ${COOLIFY_REGISTRY}/postgres:17"
echo "  - ${COOLIFY_REGISTRY}/redis:7"
echo "  - ${COOLIFY_REGISTRY}/rabbitmq:3"
echo "=================================================="
echo ""
echo "PROXIMOS PASSOS:"
echo "  1. No Coolify, crie uma nova Stack 'finops-infra'."
echo "  2. Source: aponte para o mesmo repo GitHub."
echo "  3. Compose Path: docker-compose.infra.yml"
echo "  4. Em 'Environment Variables', adicione COOLIFY_REGISTRY=${COOLIFY_REGISTRY}"
echo "  5. Deploy. Os 3 servicos devem subir usando as imagens que voce acabou de pushar."
echo "  6. Depois, crie outra Stack 'finops-app' com docker-compose.app.yml."
