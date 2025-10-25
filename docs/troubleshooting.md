# Troubleshooting Guide

**For**: System administrators, developers, and support teams

This guide covers common issues, diagnostics, and solutions.

## Table of Contents

1. [Connection Issues](#connection-issues)
2. [Classification Issues](#classification-issues)
3. [Performance Issues](#performance-issues)
4. [Audit Logging Issues](#audit-logging-issues)
5. [Database Issues](#database-issues)
6. [Diagnostic Queries](#diagnostic-queries)

---

## Connection Issues

### Issue: "Cannot connect to database"

**Error**: `psycopg2.OperationalError: connection failed`

**Diagnosis**:
```python
from classifier.utils import Config
config = Config()
print(f"Host: {config.db_host}")
print(f"Port: {config.db_port}")
print(f"Database: {config.db_name}")
print(f"User: {config.db_user}")
# Password: [REDACTED for security]
```

**Solutions**:

1. **Check environment variables**:
   ```bash
   echo $DB_HOST
   echo $DB_PORT
   echo $DB_NAME
   echo $DB_USER
   # Don't echo DB_PASSWORD for security reasons
   ```

2. **Test database accessibility**:
   ```bash
   # Test connection (requires psql)
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
   ```

3. **Verify database is running**:
   ```bash
   # PostgreSQL status
   sudo systemctl status postgresql

   # Or check if port is listening
   netstat -tuln | grep 5432
   ```

4. **Check firewall**:
   ```bash
   # Ensure port 5432 is open (if remote database)
   telnet $DB_HOST 5432
   ```

5. **Review .env file**:
   ```bash
   cat .env
   # Ensure all DB_* variables are set
   # Check for typos or missing values
   ```

---

### Issue: "Authentication failed for user"

**Error**: `psycopg2.OperationalError: password authentication failed for user "classifier"`

**Solutions**:

1. **Verify password is correct**:
   ```bash
   # Test with psql
   psql -h $DB_HOST -U $DB_USER -c "SELECT 1;"
   # Will prompt for password - try the value from .env
   ```

2. **Check pg_hba.conf** (PostgreSQL configuration):
   ```bash
   # Find pg_hba.conf (usually /etc/postgresql/*/main/pg_hba.conf)
   sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -A5 "local.*classifier"
   # Ensure authentication method is "md5" or "password" (not "reject")
   ```

3. **Reset password**:
   ```sql
   -- Connect as superuser
   sudo -u postgres psql

   -- Reset password
   ALTER USER classifier WITH PASSWORD 'new_password';

   -- Update .env
   echo "DB_PASSWORD=new_password" >> .env
   ```

---

### Issue: "Database does not exist"

**Error**: `psycopg2.OperationalError: database "classifier_db" does not exist`

**Solutions**:

1. **Create database**:
   ```sql
   sudo -u postgres psql
   CREATE DATABASE classifier_db;
   GRANT ALL PRIVILEGES ON DATABASE classifier_db TO classifier;
   ```

2. **Run migrations**:
   ```bash
   python -m classifier.utils --init-db
   # Or manually run migration scripts
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/001_create_regras_de_classificacao.sql
   ```

---

## Classification Issues

### Issue: "Product missing required fields"

**Error**: `ValueError: Product must have description and ncm`

**Solution**:
```python
from classifier.models import Product

# ✓ Correct: Provide both required fields
product = Product(description="Dell laptop", ncm="84713090")

# ✗ Wrong: Missing NCM
product = Product(description="Dell laptop")
# Raises ValueError

# Check your input data
product_dict = {"description": "test"}
if 'description' not in product_dict or 'ncm' not in product_dict:
    raise ValueError("Missing required fields")
```

---

### Issue: "NO_MATCH - Product not classified"

**Diagnosis**:

1. **Check if rules exist**:
   ```sql
   SELECT COUNT(*) as total,
          SUM(CASE WHEN ativo THEN 1 ELSE 0 END) as active
   FROM regras_de_classificacao;
   ```

2. **Check if product meets any rule criteria**:
   ```sql
   -- Find products that weren't matched
   SELECT id_produto, descricao_produto, data_classificacao
   FROM auditoria_classificacao
   WHERE id_regra IS NULL  -- No rule matched
   AND data_classificacao > NOW() - INTERVAL '1 hour'
   LIMIT 20;
   ```

3. **Test rule criteria manually**:
   ```python
   from classifier.matcher import Matcher
   from classifier.models import Rule, Product

   rule = Rule(id=1, prioridade=50, nome="Test", ativo=True,
               resultado_clasificacion="TEST",
               criterio_palavras_chave="laptop")

   product = Product(description="Dell laptop", ncm="84713090")

   print(Matcher.matches_all_criteria(rule, product))
   # Should return True if keyword matches
   ```

**Solutions**:

1. **Create more rules**:
   - Check what products are not matching
   - Query "NO_MATCH" entries in audit log
   - Create new rules to cover those products

2. **Adjust rule criteria**:
   ```sql
   -- Make keyword search more flexible
   UPDATE regras_de_classificacao SET
       criterio_palavras_chave = 'comput'  -- Matches "computer" and "compute"
   WHERE id = 42;
   ```

3. **Lower rule priority**:
   ```sql
   -- If a blocking rule has too high priority
   UPDATE regras_de_classificacao SET prioridade = 40
   WHERE id = 1;  -- Allow other rules to match
   ```

---

### Issue: "Wrong classification returned"

**Diagnosis**:

1. **Check audit log for this product**:
   ```sql
   SELECT id, id_regra, resultado_classificacao, data_classificacao
   FROM auditoria_classificacao
   WHERE id_produto = 'PROD123'
   ORDER BY data_classificacao DESC
   LIMIT 5;
   ```

2. **Check which rule matched**:
   ```sql
   SELECT * FROM regras_de_classificacao
   WHERE id = (
       SELECT id_regra FROM auditoria_classificacao
       WHERE id_produto = 'PROD123'
       ORDER BY data_classificacao DESC LIMIT 1
   );
   ```

3. **Check rule priority order**:
   ```sql
   SELECT id, nome, prioridade
   FROM regras_de_classificacao
   WHERE ativo = true
   ORDER BY prioridade DESC;
   ```

**Solutions**:

1. **Increase priority of correct rule**:
   ```sql
   -- Correct rule should have higher priority
   UPDATE regras_de_classificacao SET prioridade = 150
   WHERE id = 99;  -- Your correct rule

   UPDATE regras_de_classificacao SET prioridade = 100
   WHERE id = 42;  -- Wrong rule (lower priority)
   ```

2. **Add more specific criteria**:
   ```sql
   -- Make incorrect rule more restrictive
   UPDATE regras_de_classificacao SET
       criterio_tamanho_max = 0.5  -- Only match small items
   WHERE id = 42;  -- Currently matching too broadly
   ```

3. **Use tiebreaker (update creation date)**:
   ```sql
   -- If priorities are equal, oldest rule wins
   UPDATE regras_de_classificacao SET data_criacao = '2020-01-01'
   WHERE id = 99;  -- Make this rule older (wins tiebreaker)
   ```

---

## Performance Issues

### Issue: "Evaluation is slow (> 500ms)"

**Diagnosis**:

1. **Check evaluation time in audit log**:
   ```sql
   SELECT
       id_regra,
       COUNT(*) as evaluations,
       AVG(tempo_avaliacao_ms) as avg_time,
       MAX(tempo_avaliacao_ms) as max_time,
       MIN(tempo_avaliacao_ms) as min_time
   FROM auditoria_classificacao
   WHERE data_classificacao > NOW() - INTERVAL '1 hour'
   GROUP BY id_regra
   ORDER BY avg_time DESC
   LIMIT 10;
   ```

2. **Count rules**:
   ```sql
   SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;
   ```

3. **Check database indexes**:
   ```sql
   SELECT * FROM pg_stat_user_indexes
   WHERE schemaname = 'public';
   ```

**Solutions**:

1. **Deactivate unused rules**:
   ```sql
   -- Remove rules that never match
   UPDATE regras_de_classificacao SET ativo = false
   WHERE id IN (
       SELECT id FROM regras_de_classificacao r
       WHERE NOT EXISTS (
           SELECT 1 FROM auditoria_classificacao a
           WHERE a.id_regra = r.id
           AND a.data_classificacao > NOW() - INTERVAL '90 days'
       )
   );
   ```

2. **Add database indexes** (database administrator):
   ```sql
   -- Index for rule loading
   CREATE INDEX idx_regras_ativo_prioridade
   ON regras_de_classificacao(ativo, prioridade DESC, data_criacao);

   -- Index for audit queries
   CREATE INDEX idx_auditoria_produto
   ON auditoria_classificacao(id_produto, data_classificacao DESC);
   ```

3. **Use connection pooling** (application administrator):
   ```python
   # Instead of creating new connection each time
   # Use connection pool for concurrent requests
   from psycopg2 import pool

   connection_pool = pool.SimpleConnectionPool(
       1, 20,
       host=config.db_host,
       port=config.db_port,
       user=config.db_user,
       password=config.db_password,
       database=config.db_name
   )

   # Reuse connections from pool
   ```

4. **Batch evaluations**:
   ```python
   # Instead of evaluating one-by-one
   # Load rules once, reuse for multiple products
   engine = RuleEngine()
   rules = engine.get_rules()  # Cached

   for product in many_products:
       result = engine.evaluate(product)  # Uses cached rules
   ```

---

### Issue: "Database queries are slow"

**Solutions** (database administrator):

1. **Enable slow query log**:
   ```sql
   -- In PostgreSQL postgresql.conf
   log_min_duration_statement = 100  -- Log queries > 100ms
   ```

2. **Analyze table statistics**:
   ```sql
   ANALYZE regras_de_classificacao;
   ANALYZE auditoria_classificacao;
   ```

3. **Reindex tables**:
   ```sql
   REINDEX TABLE regras_de_classificacao;
   REINDEX TABLE auditoria_classificacao;
   ```

---

## Audit Logging Issues

### Issue: "Audit entries not being recorded"

**Diagnosis**:

1. **Check if audit table is growing**:
   ```sql
   SELECT COUNT(*) FROM auditoria_classificacao;
   -- Run this twice with 10 minutes between queries
   -- Should see count increasing
   ```

2. **Check recent audit entries**:
   ```sql
   SELECT * FROM auditoria_classificacao
   ORDER BY id DESC
   LIMIT 5;
   ```

3. **Check application logs**:
   ```bash
   tail -100 /var/log/classifier/app.log | grep -i audit
   ```

**Solutions**:

1. **Verify database write permissions**:
   ```sql
   -- Check if classifier user can insert
   INSERT INTO auditoria_classificacao
   (id_regra, id_produto, descricao_produto, resultado_classificacao,
    data_classificacao, usuario, criterios_correspondentes, tempo_avaliacao_ms)
   VALUES (42, 'TEST001', 'Test', 'TEST', NOW(), 'system', 'test', 100);
   ```

2. **Check if audit logging is enabled**:
   ```python
   # In RuleEngine.evaluate()
   if result.success:
       audit_id = self.audit_log.record(...)
       # Check if audit_id is being returned
   ```

---

### Issue: "Can't query audit history"

**Solutions**:

1. **Verify product ID exists in audit log**:
   ```sql
   SELECT DISTINCT id_produto FROM auditoria_classificacao
   WHERE id_produto LIKE '%YOUR_PRODUCT%'
   LIMIT 10;
   ```

2. **Check time range**:
   ```sql
   SELECT MIN(data_classificacao), MAX(data_classificacao)
   FROM auditoria_classificacao;
   -- Verify entries exist in your time period
   ```

3. **Inspect audit data**:
   ```python
   from classifier.audit import AuditLog

   audit = AuditLog(db_connection)
   history = audit.get_product_history('PROD123')

   if not history:
       print("No audit entries found for this product")
   else:
       for entry in history:
           print(entry)
   ```

---

## Database Issues

### Issue: "Database is out of disk space"

**Diagnosis**:

```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Solutions**:

1. **Archive old audit entries**:
   ```sql
   -- Move old entries to archive table
   CREATE TABLE auditoria_classificacao_archive AS
   SELECT * FROM auditoria_classificacao
   WHERE data_classificacao < NOW() - INTERVAL '1 year';

   DELETE FROM auditoria_classificacao
   WHERE data_classificacao < NOW() - INTERVAL '1 year';
   ```

2. **Vacuum database**:
   ```sql
   VACUUM ANALYZE regras_de_classificacao;
   VACUUM ANALYZE auditoria_classificacao;
   ```

3. **Expand disk space** (system administrator):
   ```bash
   # Add more space to PostgreSQL data directory
   # Follow your hosting provider's instructions
   ```

---

### Issue: "Cannot create or modify rules"

**Error**: `psycopg2.DatabaseError: permission denied`

**Solutions**:

1. **Check user permissions**:
   ```sql
   -- Connect as superuser
   sudo -u postgres psql -d classifier_db

   -- Check what classifier user can do
   SELECT grantee, privilege_type
   FROM information_schema.role_table_grants
   WHERE table_name = 'regras_de_classificacao';
   ```

2. **Grant permissions**:
   ```sql
   -- Connect as superuser
   GRANT SELECT, INSERT, UPDATE, DELETE ON regras_de_classificacao TO classifier;
   GRANT USAGE ON SEQUENCE regras_de_classificacao_id_seq TO classifier;
   ```

---

## Diagnostic Queries

### Get System Health Summary

```sql
-- Check overall system status
SELECT
    'Rules' as metric,
    COUNT(*)::text as value
FROM regras_de_classificacao
WHERE ativo = true

UNION ALL

SELECT 'Audit entries (24h)', COUNT(*)::text
FROM auditoria_classificacao
WHERE data_classificacao > NOW() - INTERVAL '1 day'

UNION ALL

SELECT 'No-match classifications', COUNT(*)::text
FROM auditoria_classificacao
WHERE id_regra IS NULL
AND data_classificacao > NOW() - INTERVAL '1 day'

UNION ALL

SELECT 'Avg evaluation time (ms)',
    ROUND(AVG(tempo_avaliacao_ms)::numeric, 1)::text
FROM auditoria_classificacao
WHERE data_classificacao > NOW() - INTERVAL '1 day';
```

### Find Problematic Rules

```sql
-- Rules that never match
SELECT r.id, r.nome, r.prioridade
FROM regras_de_classificacao r
LEFT JOIN auditoria_classificacao a ON r.id = a.id_regra
WHERE r.ativo = true
GROUP BY r.id
HAVING COUNT(a.id) = 0
ORDER BY r.prioridade DESC;
```

### Find Products Needing Rules

```sql
-- Products that don't match any rule
SELECT
    id_produto,
    descricao_produto,
    COUNT(*) as no_match_count,
    MAX(data_classificacao) as last_attempt
FROM auditoria_classificacao
WHERE id_regra IS NULL
GROUP BY id_produto, descricao_produto
ORDER BY last_attempt DESC
LIMIT 20;
```

### Rule Performance Report

```sql
-- Detailed rule performance
SELECT
    r.id,
    r.nome,
    r.prioridade,
    COUNT(a.id) as times_applied,
    ROUND(AVG(a.tempo_avaliacao_ms)::numeric, 1) as avg_time_ms,
    MIN(a.tempo_avaliacao_ms) as min_time_ms,
    MAX(a.tempo_avaliacao_ms) as max_time_ms,
    MAX(a.data_classificacao) as last_applied
FROM regras_de_classificacao r
LEFT JOIN auditoria_classificacao a ON r.id = a.id_regra
WHERE r.ativo = true
AND a.data_classificacao > NOW() - INTERVAL '7 days'
GROUP BY r.id, r.nome, r.prioridade
ORDER BY times_applied DESC;
```

---

## When to Contact Support

Contact your system administrator or support team if:

1. **Database won't connect** after following "Connection Issues" steps
2. **Performance is consistently slow** (> 2000ms) after optimization
3. **Audit logs are missing** without explanation
4. **Database is corrupted** (data inconsistency, constraint violations)
5. **You don't understand** why a classification is wrong after debugging

**Include in your support request**:
- Error message (full text)
- Relevant database queries and their output
- Application logs (last 50 lines)
- Product example that's failing
- Expected vs actual classification

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Can't connect | Check .env, test `psql -h $HOST -U $USER` |
| NO_MATCH | Create more rules, check audit log |
| Wrong classification | Increase priority of correct rule |
| Slow evaluation | Deactivate unused rules, add indexes |
| Audit not recording | Check database write permissions |
| Product not found | Check spelling, use DISTINCT query |

