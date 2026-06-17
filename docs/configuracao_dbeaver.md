# Configuração DBeaver - Acesso ao PostgreSQL FinOps

## 📋 Informações de Conexão

**Dados para configurar no DBeaver:**

- **Server Host/IP**: `178.156.185.182` (IP público do servidor)
- **Port**: `5432`
- **Database**: `finopsdatabase`  
- **Username**: `svc_finops`
- **Password**: `<sua-senha-do-banco>`

## 🔧 Configuração Passo a Passo

### 1. Criar Nova Conexão
1. Abra o DBeaver
2. Clique em **Nova Conexão** ou `Ctrl+Shift+N`
3. Selecione **PostgreSQL**
4. Clique em **Próximo**

### 2. Configurar Conexão Principal
Na aba **Main**:
- **Server Host**: `178.156.185.182`
- **Port**: `5432`  
- **Database**: `finopsdatabase`
- **Username**: `svc_finops`
- **Password**: `<sua-senha-do-banco>`

### 3. Configurar SSL (IMPORTANTE!)
Na aba **SSL**:
- **Use SSL**: ✅ Marcar
- **SSL Mode**: `prefer` ou `require`
- **SSL Factory**: `org.postgresql.ssl.DefaultJavaSSLFactory`

### 4. Configurações Avançadas
Na aba **Driver Properties** (se necessário):
- `sslmode`: `prefer`
- `ssl`: `true`

### 5. Testar Conexão
1. Clique em **Test Connection**
2. Se aparecer erro de driver, clique em **Download** para baixar o driver PostgreSQL
3. Teste novamente

## ⚠️ Possíveis Problemas e Soluções

### Problema 1: "SSL encryption"
**Solução**: Certifique-se de configurar SSL como descrito acima.

### Problema 2: "Connection refused" 
**Solução**: Verifique se:
- O IP do servidor está correto: `178.156.185.182`
- A porta 5432 não está bloqueada por firewall
- Seu IP está liberado no servidor

### Problema 3: "Authentication failed"
**Solução**: 
- Verifique usuário e senha
- Certifique-se que está usando: `svc_finops` / `<sua-senha-do-banco>`

### Problema 4: Driver não encontrado
**Solução**:
1. No DBeaver, vá em **Database** > **Driver Manager**
2. Encontre **PostgreSQL** na lista
3. Clique em **Download/Update** se necessário

## 🔍 Teste Rápido de Conexão

Após configurar, execute esta query para testar:

```sql
SELECT 
    current_database() as database_name,
    current_user as user_name,
    version() as postgres_version,
    now() as current_time;
```

## 📊 Principais Tabelas do FinOps

```sql
-- Listar todas as tabelas
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Verificar dados recentes
SELECT 
    DATE(data) as data,
    COUNT(*) as registros,
    ROUND(SUM(custo_total::numeric), 2) as custo_total
FROM utilizacao_recurso 
WHERE cloudproviderid = 3 
AND data >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(data) 
ORDER BY DATE(data);
```

## 🚨 Importante

- **Não compartilhe** as credenciais do banco
- **Use sempre SSL** para conexões externas
- **Mantenha** o DBeaver atualizado
- **Faça backup** antes de executar alterações

## 📞 Suporte

Se ainda tiver problemas:
1. Verifique se seu IP está liberado no servidor
2. Confirme que não há firewall bloqueando a porta 5432
3. Entre em contato com a equipe para liberação de acesso

---
*Documento atualizado em: $(date)*