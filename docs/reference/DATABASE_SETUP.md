# Database Setup Guide

## Table Names (IMPORTANT!)

Your actual database uses Portuguese naming conventions:

| Table | Purpose | Columns |
|-------|---------|---------|
| `produtos_tabela` | Products to classify | id, description, ncm, categoria, size, quantity, data_classificacao |
| `regras_de_classificacao` | Classification rules | id, nome, ativo, prioridade, criterio_*, resultado_classificacao, data_criacao, data_atualizacao |
| `auditoria_classificacao` | Audit trail | id, id_regra, id_produto, descricao_produto, ncm_produto, resultado_classificacao, data_classificacao, etc |
| `criterios_palavras_chave` | Keyword matching | (if used) |

## Quick Check: Verify Your Database

```sql
-- List all tables in your database
\dt

-- Check products_tabela structure
\d produtos_tabela

-- Check rules structure
\d regras_de_classificacao

-- Check audit structure
\d auditoria_classificacao

-- Count products
SELECT COUNT(*) FROM produtos_tabela;

-- Count rules
SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;

-- Count classifications
SELECT COUNT(*) FROM auditoria_classificacao;
```

## Sample Data Setup

### Insert Sample Rules
```sql
-- Insert test classification rules
INSERT INTO regras_de_classificacao (
    nome, prioridade, ativo,
    criterio_palavras_chave,
    resultado_classificacao,
    data_criacao, data_atualizacao
) VALUES
('Laptop Rule', 50, true, 'laptop', 'ELECTRONICS', NOW(), NOW()),
('Monitor Rule', 50, true, 'monitor', 'ELECTRONICS', NOW(), NOW()),
('Cable Rule', 40, true, 'cable', 'ACCESSORIES', NOW(), NOW()),
('Smartphone Rule', 60, true, 'phone OR smartphone', 'ELECTRONICS', NOW(), NOW()),
('Tablet Rule', 55, true, 'tablet', 'ELECTRONICS', NOW(), NOW());

-- Verify rules inserted
SELECT id, nome, prioridade FROM regras_de_classificacao WHERE ativo = true ORDER BY prioridade DESC;
```

### Insert Sample Products
```sql
-- Insert unclassified products
INSERT INTO produtos_tabela (id, description, ncm, categoria, size, quantity) VALUES
('PROD_001', 'laptop dell inspiron 15', '84713090', NULL, 2.5, 50),
('PROD_002', 'monitor samsung 24 inch', '85287200', NULL, 5.2, 30),
('PROD_003', 'keyboard logitech wireless', '84711000', NULL, 0.8, 100),
('PROD_004', 'usb cable type c', '85444200', NULL, 0.05, 500),
('PROD_005', 'smartphone samsung galaxy', '85171200', NULL, 0.18, 75),
('PROD_006', 'tablet samsung', '85171200', NULL, 0.6, 40),
('PROD_007', 'unknown product', '99999999', NULL, 0.5, 10);

-- Verify products inserted
SELECT id, description, categoria FROM produtos_tabela LIMIT 10;

-- Count unclassified
SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NULL;
```

## Testing Your Setup

```bash
# Activate environment
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Test with statistics
classify-batch --stats

# Should show:
# Total Products: 7
# Classified: 0
# Unclassified: 7

# Test classification
classify-batch --limit 5

# Should classify the 5 products that match rules
# PROD_001 (laptop) → ELECTRONICS
# PROD_002 (monitor) → ELECTRONICS
# etc.
```

## Monitoring Your Data

### Check Classification Progress
```sql
-- See overall statistics
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN categoria IS NOT NULL THEN 1 END) as classified,
    COUNT(CASE WHEN categoria IS NULL THEN 1 END) as unclassified,
    ROUND(100.0 * COUNT(CASE WHEN categoria IS NOT NULL THEN 1 END) / COUNT(*), 2) as classification_rate
FROM produtos_tabela;
```

### Find Products Without Matches
```sql
-- Products that couldn't be classified
SELECT p.id, p.description, p.ncm
FROM produtos_tabela p
WHERE p.categoria IS NULL
ORDER BY p.id;
```

### See Classification History
```sql
-- Recent classifications
SELECT id_produto, resultado_classificacao, data_classificacao
FROM auditoria_classificacao
ORDER BY data_classificacao DESC
LIMIT 20;

-- Which rule classified what
SELECT 
    a.id_produto,
    r.nome as rule_name,
    a.resultado_classificacao,
    a.data_classificacao
FROM auditoria_classificacao a
LEFT JOIN regras_de_classificacao r ON a.id_regra = r.id
ORDER BY a.data_classificacao DESC
LIMIT 20;
```

### Rule Statistics
```sql
-- Most used rules
SELECT 
    r.id,
    r.nome,
    COUNT(*) as times_applied,
    ROUND(AVG(EXTRACT(EPOCH FROM (a.data_classificacao - r.data_criacao))), 2) as avg_seconds_to_apply
FROM auditoria_classificacao a
JOIN regras_de_classificacao r ON a.id_regra = r.id
WHERE a.resultado_classificacao != 'NO_MATCH'
GROUP BY r.id, r.nome
ORDER BY times_applied DESC;
```

## Troubleshooting Database Issues

### Error: "relation 'produtos_tabela' does not exist"
```sql
-- Check table name is correct
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check for typos in your query
-- Use exact name: produtos_tabela (not productos, not produto_tabela)
```

### Error: "column 'categoria' does not exist"
```sql
-- Check column names
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'produtos_tabela';
```

### Products Not Being Classified
```sql
-- Check if rules exist and are active
SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;

-- Check if any products match
SELECT p.id, p.description
FROM produtos_tabela p
WHERE p.categoria IS NULL
AND p.description ILIKE '%laptop%';  -- Test with a keyword you know exists
```

### Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d classifier -c "SELECT 1;"

# If connection fails, check:
# 1. PostgreSQL is running: sudo systemctl status postgresql
# 2. Database exists: psql -l | grep classifier
# 3. User has permissions: psql -U postgres -c "\du"
```

## Regular Maintenance

### Daily
```sql
-- Check unclassified count
SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NULL;

-- Monitor if new products are being added
SELECT COUNT(*) FROM produtos_tabela;
```

### Weekly
```sql
-- Review rule effectiveness
SELECT 
    r.nome,
    COUNT(*) as count
FROM auditoria_classificacao a
JOIN regras_de_classificacao r ON a.id_regra = r.id
GROUP BY r.nome
ORDER BY count DESC;

-- Find products still without matches
SELECT COUNT(*) FROM auditoria_classificacao 
WHERE resultado_classificacao = 'NO_MATCH';
```

### Monthly
```sql
-- Archive old audit entries (optional)
-- DELETE FROM auditoria_classificacao 
-- WHERE data_classificacao < CURRENT_DATE - INTERVAL '90 days';

-- Analyze table performance
ANALYZE produtos_tabela;
ANALYZE auditoria_classificacao;
```

## Summary

Your database structure:
- **Products table**: `produtos_tabela` (stores products to classify)
- **Rules table**: `regras_de_classificacao` (stores classification rules)
- **Audit table**: `auditoria_classificacao` (stores classification history)

The classifier system will:
1. Read unclassified products from `produtos_tabela`
2. Match them against rules in `regras_de_classificacao`
3. Write results to `auditoria_classificacao`
4. Update `categoria` column in `produtos_tabela`

All table and column names are in Portuguese!
