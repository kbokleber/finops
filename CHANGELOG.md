# Changelog - FinOps Project

## [2.1.0] - 2025-08-07

### ✅ Adicionado
- **Dashboard integrado** ao projeto principal FinOps
- Script `run_dashboard.py` para inicialização individual do dashboard
- Script `start_finops.sh` para inicialização completa do sistema
- Documentação de migração da estrutura (`atualizacao_estrutura_dashboard.md`)
- Dependência `pytz` para tratamento de fusos horários

### 🔄 Modificado
- **Dashboard movido** de `/root/scripts/dashboard_simple.py` para `/root/finops/dashboard/app.py`
- **README.md principal** atualizado com nova estrutura
- **Templates do dashboard** atualizados com títulos mais apropriados
- Script `dashboard_service.sh` atualizado para nova localização
- Script `check_dashboard.sh` atualizado para detectar nova estrutura
- Script `setup_dashboard.sh` atualizado com instruções da nova estrutura
- README.md do diretório scripts com seção específica sobre dashboard

### 🏗️ Estrutura Nova
```
/root/finops/
├── dashboard/              # 🆕 Dashboard integrado
│   ├── app.py             # 🔄 Antes: /root/scripts/dashboard_simple.py
│   ├── templates/         # Templates HTML
│   └── __init__.py        
├── run_dashboard.py       # 🆕 Inicializador do dashboard
├── start_finops.sh        # 🆕 Inicializador completo
└── ...
```

### 📊 Dashboard
- **Nova localização**: `/root/finops/dashboard/`
- **Arquivo principal**: `app.py` (antes: `dashboard_simple.py`)
- **URL de acesso**: http://localhost:5000
- **Título atualizado**: "Dashboard FinOps - Monitoramento de Custos Cloud"

### 🔧 Scripts Atualizados
1. `/root/scripts/dashboard_service.sh` - Compatibilidade com nova estrutura
2. `/root/scripts/check_dashboard.sh` - Detecção atualizada
3. `/root/scripts/setup_dashboard.sh` - Instruções atualizadas
4. `/root/scripts/diagnostico_completo.py` - Comentários sobre migração

### 🚀 Formas de Inicialização
```bash
# 1. Sistema completo (recomendado)
cd /root/finops && ./start_finops.sh

# 2. Apenas dashboard
cd /root/finops && python3 run_dashboard.py

# 3. Via script de serviço (compatibilidade)
/root/scripts/dashboard_service.sh start
```

### 🎯 Benefícios
- ✅ **Estrutura profissional**: Dashboard integrado ao projeto
- ✅ **Facilidade de uso**: Scripts automatizados
- ✅ **Manutenibilidade**: Dependências centralizadas
- ✅ **Compatibilidade**: Scripts antigos funcionam
- ✅ **Organização**: Estrutura modular

---

## [2.0.0] - 2025-08-07 (Anterior)
- Melhorias scripts OCI
- Novos helpers de controle
- Debug logs implementados
- Estrutura modularizada

---

**Responsável**: DevOps ServiceIT Team  
**Data**: 07/08/2025
