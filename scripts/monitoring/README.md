# 📈 Scripts de Monitoramento

Scripts para monitoramento em tempo real do sistema FinOps.

## 📁 Conteúdo

### `check_oci_structure.py`
- **Função**: Verificar estrutura e status do sistema OCI
- **Uso**: `python3 check_oci_structure.py`
- **Saída**: Status detalhado dos componentes OCI

### `monitor_oci_interativo.py`
- **Função**: Monitor interativo para sistema OCI
- **Uso**: `python3 monitor_oci_interativo.py`
- **Saída**: Interface interativa de monitoramento

### `monitor_progress.py`
- **Função**: Monitorar progresso de processamento
- **Uso**: `python3 monitor_progress.py`
- **Saída**: Progresso em tempo real

### `analyze_oci_complete.py`
- **Função**: Análise completa dos dados OCI
- **Uso**: `python3 analyze_oci_complete.py`
- **Saída**: Relatório completo de análise

## 🚀 Como Usar

```bash
# Monitor interativo
cd /root/finops/scripts/monitoring
python3 monitor_oci_interativo.py

# Verificar estrutura OCI
python3 check_oci_structure.py

# Análise completa
python3 analyze_oci_complete.py
```

## 📊 Informações dos Scripts

- **Dependências**: psycopg2, datetime, time
- **Atualização**: Tempo real
- **Interface**: Console interativo
