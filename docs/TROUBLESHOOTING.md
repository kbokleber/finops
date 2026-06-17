# 🔧 Resolução de Problemas - FinOps Dashboard

## 📋 Índice
- [Problemas Comuns](#problemas-comuns)
- [Correções de Dados](#correções-de-dados)
- [Problemas de Timezone](#problemas-de-timezone)
- [Diagnóstico Completo](#diagnóstico-completo)
- [Logs e Monitoramento](#logs-e-monitoramento)

## 🚨 Problemas Comuns

### ❌ Erro: "Address already in use"
**Solução Rápida:**
```bash
cd /root/finops
./scripts/dashboard_manager.sh cleanup  # Limpeza automática
./scripts/dashboard_manager.sh start    # Reinicia limpo
```

**Solução Manual:**
```bash
sudo fuser -k 5000/tcp  # Mata processos na porta 5000
./scripts/dashboard_manager.sh stop  # Para dashboard atual
./scripts/dashboard_manager.sh start  # Reinicia limpo
```

### ❌ Dashboard não para corretamente
**Solução:**
```bash
./scripts/dashboard_manager.sh cleanup  # Força parada de todos os processos
```
O comando `cleanup` detecta e para:
- ✅ Processos `run_dashboard.py`
- ✅ Processos `app.py` diretos
- ✅ Qualquer processo na porta 5000
- ✅ Remove arquivos de controle

### ❌ Dashboard para quando fecha terminal
**Solução:**
```bash
# Use sempre o método independente
./scripts/dashboard_manager.sh start  # Não use python app.py diretamente
```

### ❌ Erro: "Comando não encontrado"
**Solução:**
```bash
cd /root/finops  # Certifique-se de estar no diretório correto
chmod +x scripts/*.sh  # Torna scripts executáveis
./scripts/diagnostico_dashboard.sh  # Execute diagnóstico
```

### ❌ Serviço systemd falhando
**Solução:**
- Use o método principal: `./scripts/dashboard_manager.sh start`
- O systemd é opcional, o método shell é mais confiável

## 📊 Correções de Dados Implementadas

### ✅ Problema: Contagem Incorreta de Registros
**Situação**: Dashboard mostrava 2,767 registros, mas banco tinha 7,383

**Causa Identificada**: 
- Filtro SQL `WHERE cloudproviderid = 3` estava limitando resultados
- Filtro desnecessário aplicado nas consultas

**Correção Aplicada**:
```sql
-- ❌ Query anterior (incorreta)
SELECT COUNT(*) FROM utilizacao_recurso WHERE cloudproviderid = 3;

-- ✅ Query corrigida (atual)
SELECT COUNT(*) FROM utilizacao_recurso;
```

**Arquivos Alterados**:
- `/root/finops/dashboard/app.py` - Funções `api_recent_data()` e `api_summary()`

**Resultado**: ✅ Dashboard agora mostra 7,383 registros corretos

### ✅ Verificação de Dados
```bash
# Para verificar contagem atual no banco
cd /root/finops
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', database='finops', user='finops_user', password='finops2024')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM utilizacao_recurso')
print(f'Total de registros: {cur.fetchone()[0]}')
conn.close()
"
```

## 🕐 Correções de Timezone Implementadas

### ✅ Problema: Horários Incorretos nos Provedores
**Situação**: Status dos provedores mostrava horários 6 horas atrasados
- **Exemplo**: Banco tinha 14:13:05, dashboard mostrava 08:13:05

**Causa Identificada**:
- Função JavaScript `formatDateUTCToBrasilia` estava subtraindo 3 horas em vez de converter corretamente
- Cálculo manual incorreto de timezone

**Correção Aplicada**:
```javascript
// ❌ Código anterior (incorreto)
const brasiliaDate = new Date(utcDate.getTime() - (3 * 60 * 60 * 1000)); // Subtraindo 3h

// ✅ Código corrigido (atual)
return utcDate.toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',  // Conversão automática e precisa
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
});
```

**Arquivo Alterado**:
- `/root/finops/dashboard/templates/dashboard.html` - Função `formatDateUTCToBrasilia()`

**Resultado**: ✅ Horários agora são exibidos corretamente em Brasília

### ✅ Verificação de Timezone
```bash
# Para verificar dados de provedores no banco
cd /root/finops
python3 -c "
import psycopg2
from datetime import datetime
conn = psycopg2.connect(host='localhost', database='finops', user='finops_user', password='finops2024')
cur = conn.cursor()
cur.execute('SELECT tipo, datatime_ultimo_update, datatime_proximo_update FROM provedor_nuvem')
for row in cur.fetchall():
    print(f'Provedor: {row[0]}, Último: {row[1]}, Próximo: {row[2]}')
conn.close()
"
```

## 🔍 Diagnóstico Completo

### Script de Diagnóstico
```bash
./scripts/diagnostico_dashboard.sh
```

Este script verifica:
- ✅ Arquivos e diretórios
- ✅ Status da porta 5000
- ✅ Processos ativos
- ✅ Conectividade
- ✅ Dependências Python
- ✅ Logs recentes
- ✅ Configurações do banco
- ✅ Status dos serviços

### Verificação Manual
```bash
# Status dos processos
./scripts/dashboard_manager.sh status

# Teste de conectividade
./scripts/dashboard_manager.sh test

# Verificar porta
ss -tlnp | grep :5000

# Verificar processos Python
ps aux | grep python | grep -E '(app.py|run_dashboard.py)'
```

## 📝 Logs e Monitoramento

### Localizações dos Logs
- **Dashboard Principal**: `/root/finops/logs/dashboard.log`
- **Erro Python**: Console output dos scripts
- **Sistema**: `/var/log/syslog` (para systemd)

### Visualizar Logs em Tempo Real
```bash
# Logs do dashboard
./scripts/dashboard_manager.sh logs
# ou
tail -f /root/finops/logs/dashboard.log

# Logs do sistema
journalctl -f -u finops-dashboard.service
```

### Análise de Logs
```bash
# Últimas 50 linhas
tail -50 /root/finops/logs/dashboard.log

# Buscar por erros
grep -i error /root/finops/logs/dashboard.log

# Buscar por data específica
grep "2025-08-09" /root/finops/logs/dashboard.log
```

## 🚀 Testes de Validação

### Teste de Persistência
```bash
./scripts/test_persistence.sh
```

### Teste Manual de Independência
```bash
# 1. Iniciar dashboard
./scripts/dashboard_manager.sh start

# 2. Verificar status
./scripts/dashboard_manager.sh status

# 3. Fechar terminal (simulação)
# 4. Abrir novo terminal

# 5. Verificar se ainda está rodando
cd /root/finops
./scripts/dashboard_manager.sh status

# 6. Testar acesso web
curl -s http://localhost:5000 | grep -i "finops" && echo "✅ Dashboard funcionando"
```

## 📊 Métricas de Sistema

### Uso de Recursos
```bash
# CPU e memória do dashboard
ps aux | grep -E '(app.py|run_dashboard.py)' | awk '{print $3, $4, $11}'

# Conexões de rede
ss -tuln | grep :5000

# Espaço em disco dos logs
du -sh /root/finops/logs/
```

### Performance do Banco
```bash
cd /root/finops
python3 -c "
import psycopg2, time
start = time.time()
conn = psycopg2.connect(host='localhost', database='finops', user='finops_user', password='finops2024')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM utilizacao_recurso')
result = cur.fetchone()[0]
end = time.time()
print(f'Consulta retornou {result} registros em {end-start:.2f}s')
conn.close()
"
```

## 🆘 Contatos e Suporte

### Comandos de Emergência
```bash
# Parar tudo e recomeçar
./scripts/dashboard_manager.sh cleanup
./scripts/dashboard_manager.sh start

# Verificar se está funcionando
./scripts/dashboard_manager.sh status
curl -s http://localhost:5000 >/dev/null && echo "✅ OK" || echo "❌ FALHA"
```

### Backup de Emergência
```bash
# Backup da configuração atual
cd /root/finops
tar -czf finops_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    dashboard/ scripts/ config/ docs/ \
    requirements.txt .env.example .gitignore \
    --exclude="logs/" --exclude="__pycache__/" \
    --exclude=".git/" --exclude="dashboard_env/"
```

## ✅ Status Atual do Sistema

```
🟢 Dashboard - Funcionando independente do terminal
🟢 Dados - Contagens corretas (7,383 registros)
🟢 Timezone - Horários corretos de Brasília
🟢 Autenticação - Modo bypass ativo
🟢 Scripts - Todos funcionando
🟢 Logs - Monitoramento ativo
🟢 Documentação - Organizada e atualizada
```

**Última atualização**: August 9, 2025
