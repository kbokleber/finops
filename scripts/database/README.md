# 🗄️ Scripts de Database

Scripts para gerenciamento e verificação do banco de dados PostgreSQL.

## 📁 Conteúdo

### `check_database_config.py`
- **Função**: Verificar configuração do banco de dados
- **Uso**: `python3 check_database_config.py`
- **Saída**: Status das configurações de conexão

### `check_db_structure.py`
- **Função**: Verificar estrutura das tabelas
- **Uso**: `python3 check_db_structure.py`
- **Saída**: Análise da estrutura do banco

### `list_all_tables.py`
- **Função**: Listar todas as tabelas e informações
- **Uso**: `python3 list_all_tables.py`
- **Saída**: Lista completa de tabelas com estatísticas

### `consultas_monitoramento_oci.sql`
- **Função**: Consultas SQL para monitoramento OCI
- **Uso**: `psql -f consultas_monitoramento_oci.sql`
- **Saída**: Resultados das consultas de monitoramento

## 🚀 Como Usar

```bash
# Verificar configuração do banco
cd /root/finops/scripts/database
python3 check_database_config.py

# Listar todas as tabelas
python3 list_all_tables.py

# Executar consultas de monitoramento
psql -h localhost -U svc_finops -d finopsdatabase -f consultas_monitoramento_oci.sql
```

## 📊 Informações dos Scripts

- **Dependências**: psycopg2, datetime
- **Banco**: PostgreSQL (finopsdatabase)
- **Usuário**: svc_finops
