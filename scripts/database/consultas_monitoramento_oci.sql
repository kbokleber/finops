-- Consultas para monitoramento e ajuste do sistema OCI

-- 1. Verificar status atual dos provedores OCI
SELECT 
    nome,
    tipo,
    datatime_ultimo_update,
    datatime_proximo_update,
    NOW() as agora,
    jobs_restantes,
    CASE 
        WHEN datatime_proximo_update <= NOW() THEN 'DEVE PROCESSAR'
        ELSE 'AGUARDANDO'
    END as status,
    CASE 
        WHEN datatime_ultimo_update IS NOT NULL AND datatime_proximo_update IS NOT NULL 
        THEN datatime_proximo_update - datatime_ultimo_update
        ELSE NULL
    END as intervalo_configurado
FROM provedor_nuvem 
WHERE tipo = 'oci';

-- 2. Forçar processamento imediato (definir próximo update para AGORA)
UPDATE provedor_nuvem 
SET datatime_proximo_update = NOW()
WHERE tipo = 'oci';

-- 3. Verificar histórico de processamento (últimos 7 dias)
SELECT 
    DATE(data) as dia,
    COUNT(*) as registros,
    COUNT(DISTINCT id_recurso) as recursos_distintos,
    SUM(custo_total::numeric) as custo_total,
    MIN(data) as primeiro_registro,
    MAX(data) as ultimo_registro
FROM utilizacao_recurso 
WHERE cloudproviderid = 3 
AND data >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(data)
ORDER BY dia DESC;

-- 4. Verificar últimos 10 processamentos
SELECT 
    datatime_ultimo_update,
    datatime_proximo_update,
    jobs_restantes
FROM provedor_nuvem 
WHERE tipo = 'oci'
ORDER BY datatime_ultimo_update DESC;

-- 5. Verificar se há tabelas de controle de arquivos
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as colunas,
       pg_size_pretty(pg_total_relation_size(table_name::regclass)) as tamanho
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name LIKE '%oci%'
ORDER BY table_name;
