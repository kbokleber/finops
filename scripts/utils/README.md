# 🔧 Scripts Utilitários

Scripts utilitários para configuração e manutenção do sistema.

## 📁 Conteúdo

### `create_settings_container.py`
- **Função**: Criar configurações para containers
- **Uso**: `python3 create_settings_container.py`
- **Saída**: Arquivos de configuração gerados

### `test_oci_connectivity.py`
- **Função**: Testar conectividade com OCI
- **Uso**: `python3 test_oci_connectivity.py`
- **Saída**: Status da conectividade

### `init_oci_tables.py`
- **Função**: Inicializar tabelas OCI
- **Uso**: `python3 init_oci_tables.py`
- **Saída**: Tabelas criadas/atualizadas

### `oci_file_control_container.py`
- **Função**: Controle de arquivos OCI em container
- **Uso**: `python3 oci_file_control_container.py`
- **Saída**: Status do controle de arquivos

## 🚀 Como Usar

```bash
# Testar conectividade OCI
cd /root/finops/scripts/utils
python3 test_oci_connectivity.py

# Inicializar tabelas
python3 init_oci_tables.py

# Criar configurações
python3 create_settings_container.py
```

## 📊 Informações dos Scripts

- **Dependências**: Variáveis (oci, psycopg2, etc.)
- **Configuração**: Usa .env do projeto
- **Logs**: Console e arquivos quando aplicável
