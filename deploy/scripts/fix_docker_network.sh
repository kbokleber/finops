#!/bin/bash

# Script para corrigir problemas de rede Docker
# Execute este script se tiver problemas com a rede brigde

set -e

echo "=== Corrigindo problemas de rede Docker ==="

# Parar todos os containers que podem estar usando a rede
echo "Parando containers Docker..."
docker stop $(docker ps -q) 2>/dev/null || echo "Nenhum container rodando"

# Remover rede problemática
echo "Removendo rede brigde problemática..."
docker network rm brigde 2>/dev/null || echo "Rede brigde não existe ou não pode ser removida"

# Recriar rede com configurações corretas
echo "Criando rede brigde com configurações corretas..."
docker network create brigde \
    --driver bridge \
    --label com.docker.compose.network=default \
    --label com.docker.compose.project=default

# Verificar se a rede foi criada corretamente
echo "Verificando rede criada..."
docker network inspect brigde | grep -A 10 "Labels"

# Limpar containers e volumes órfãos
echo "Limpando recursos órfãos..."
docker system prune -f

echo "=== Correção de rede concluída ==="
echo "Agora você pode executar novamente:"
echo "./06_setup_services.sh"
