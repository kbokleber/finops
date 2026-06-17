# 🔍 Scripts de Diagnóstico

Scripts para diagnosticar problemas e verificar o status do sistema FinOps.

## 📁 Conteúdo

### `diagnostico_completo.py`
- **Função**: Diagnóstico completo de discrepâncias entre banco e dashboard
- **Uso**: `python3 diagnostico_completo.py`
- **Saída**: Relatório detalhado de inconsistências

### `simple_diagnosis.py`
- **Função**: Diagnóstico rápido e simples do sistema
- **Uso**: `python3 simple_diagnosis.py`
- **Saída**: Status básico dos componentes

### `verificar_dados.py`
- **Função**: Verificação específica de dados OCI
- **Uso**: `python3 verificar_dados.py`
- **Saída**: Validação de registros e consistência

### `comprehensive_oci_diagnosis.py`
- **Função**: Diagnóstico abrangente específico para OCI
- **Uso**: `python3 comprehensive_oci_diagnosis.py`
- **Saída**: Análise completa do sistema OCI

## 🚀 Como Usar

```bash
# Executar diagnóstico completo
cd /root/finops/scripts/diagnosis
python3 diagnostico_completo.py

# Diagnóstico rápido
python3 simple_diagnosis.py

# Verificar dados específicos
python3 verificar_dados.py
```

## 📊 Informações dos Scripts

- **Dependências**: psycopg2, requests
- **Conexão**: Usa configuração padrão do banco FinOps
- **Logs**: Saída para console
