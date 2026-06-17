# 👨‍💼 Scripts de Administração

Scripts para administração e validação do sistema FinOps.

## 📁 Conteúdo

### `validate_oci_final.py`
- **Função**: Validação final do sistema OCI
- **Uso**: `python3 validate_oci_final.py`
- **Saída**: Relatório de validação completa

### `check_oci_tables.py`
- **Função**: Verificar integridade das tabelas OCI
- **Uso**: `python3 check_oci_tables.py`
- **Saída**: Status das tabelas OCI

## 🚀 Como Usar

```bash
# Validação final do sistema
cd /root/finops/scripts/admin
python3 validate_oci_final.py

# Verificar tabelas
python3 check_oci_tables.py
```

## 📊 Informações dos Scripts

- **Dependências**: psycopg2, oci, datetime
- **Nível**: Administrador
- **Execução**: Sob demanda ou agendada
