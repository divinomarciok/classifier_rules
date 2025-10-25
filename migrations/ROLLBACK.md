# Migration Rollback Procedures

**Last Updated**: 2025-10-25

This document provides instructions for rolling back database migrations in case of errors or need to revert to a previous state.

## ⚠️ Important Warnings

- **BACKUP FIRST**: Always backup your database before rolling back
- **DATA LOSS**: Rollbacks may result in data loss if tables contain data
- **ORDER MATTERS**: Rollbacks must be done in REVERSE order of migrations
- **TEST IN STAGING**: Always test rollback procedures in staging environment first

## Rollback Procedures

### Rolling Back All Migrations (Complete Reset)

```bash
# DANGER: This removes ALL tables. Only use for development/testing.

# From psql prompt or SQL file execution:
psql -h localhost -U classifier_user -d classifier_test -f - << 'EOF'

-- Rollback in REVERSE order (opposite of execution)

-- Drop Migration 003: Keywords table first (references Migration 001)
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;

-- Drop Migration 002: Audit log table (references Migration 001)
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;

-- Drop Migration 001: Rules table (base table)
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;

-- Verify tables are gone
\dt

EOF
```

### Rolling Back Individual Migrations

#### Rollback Migration 003 Only (Keywords Index)

```sql
-- Safe: No dependencies on this table
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
```

#### Rollback Migration 002 Only (Audit Log)

```sql
-- WARNING: Deletes audit log history
-- First, back up audit data if needed
CREATE TABLE auditoria_classificacao_backup AS SELECT * FROM auditoria_classificacao;

DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
```

#### Rollback Migration 001 Only (Rules Table)

```sql
-- DANGER: This will fail if other tables reference it
-- You MUST rollback 002 and 003 first

-- Step 1: Verify no dependent tables
SELECT table_name FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND table_schema = 'public';

-- Step 2: Drop references (if any remain)
ALTER TABLE auditoria_classificacao DROP CONSTRAINT auditoria_classificacao_id_regra_fkey;
ALTER TABLE criterios_palavras_chave DROP CONSTRAINT criterios_palavras_chave_id_regra_fkey;

-- Step 3: Drop the table
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;
```

### Partial Data Cleanup (Keep Structure, Clear Data)

```sql
-- Keep table structure, delete all data (for testing)
TRUNCATE TABLE regras_de_classificacao CASCADE;
TRUNCATE TABLE auditoria_classificacao CASCADE;
TRUNCATE TABLE criterios_palavras_chave CASCADE;

-- Or individually:
DELETE FROM criterios_palavras_chave;
DELETE FROM auditoria_classificacao;
DELETE FROM regras_de_classificacao;
```

## Recovery Procedures

### After Rollback, Re-apply Migrations

```bash
# Re-apply migrations in order
psql -h localhost -U classifier_user -d classifier_test -f migrations/001_create_regras_de_classificacao.sql
psql -h localhost -U classifier_user -d classifier_test -f migrations/002_create_auditoria_classificacao.sql
psql -h localhost -U classifier_user -d classifier_user -f migrations/003_create_criterios_palavras_chave.sql
```

### Restore from Backup

```bash
# If you have a backup from before the migration
pg_restore -h localhost -U classifier_user -d classifier_test /path/to/backup.dump
```

## Migration Dependencies

```
Migration 001: regras_de_classificacao
    ↓ (referenced by)
    ├─ Migration 002: auditoria_classificacao (id_regra FK)
    └─ Migration 003: criterios_palavras_chave (id_regra FK)
```

**Rollback Order** (REVERSE of execution):
1. Migration 003 (criterios_palavras_chave) - depends on nothing
2. Migration 002 (auditoria_classificacao) - depends on 001
3. Migration 001 (regras_de_classificacao) - no dependencies after 002+003 dropped

## Emergency Rollback Script

```bash
#!/bin/bash
# emergency_rollback.sh - Quick rollback for emergency situations

set -e

DB_HOST=${DB_HOST:-localhost}
DB_USER=${DB_USER:-classifier_user}
DB_NAME=${DB_NAME:-classifier_test}

echo "⚠️  EMERGENCY ROLLBACK - This will DESTROY all data"
read -p "Type 'ROLLBACK' to confirm: " confirm

if [ "$confirm" != "ROLLBACK" ]; then
    echo "Aborted."
    exit 1
fi

echo "Rolling back all migrations..."

psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;

SELECT 'All tables dropped successfully' AS status;
EOF

echo "✓ Rollback complete"
```

## Verification Commands

```sql
-- List all tables
\dt

-- Check table structure
\d regras_de_classificacao
\d auditoria_classificacao
\d criterios_palavras_chave

-- Check for foreign keys
SELECT constraint_name, table_name, column_name
FROM information_schema.key_column_usage
WHERE table_schema = 'public';

-- Count records (data check)
SELECT COUNT(*) FROM regras_de_classificacao;
SELECT COUNT(*) FROM auditoria_classificacao;
SELECT COUNT(*) FROM criterios_palavras_chave;
```

## Troubleshooting

### Error: "Cannot drop table ... because other objects depend on it"

**Solution**: Drop dependent tables first (in reverse order)

```sql
-- Identify dependencies
SELECT * FROM pg_constraint
WHERE conrelid = 'regras_de_classificacao'::regclass;

-- Drop tables in correct order
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;
```

### Error: "Connection refused"

**Solution**: Verify database is running and accessible

```bash
# Test connection
psql -h localhost -U classifier_user -d classifier_test -c "SELECT 1"

# Check PostgreSQL is running
sudo systemctl status postgresql
```

### Foreign Key Constraint Violations

**Solution**: Disable foreign key checks temporarily

```sql
-- Disable FK checks (PostgreSQL style)
ALTER TABLE auditoria_classificacao DISABLE TRIGGER ALL;
ALTER TABLE criterios_palavras_chave DISABLE TRIGGER ALL;

-- Now drop parent table
DROP TABLE regras_de_classificacao CASCADE;

-- Re-enable (if needed, not recommended)
ALTER TABLE auditoria_classificacao ENABLE TRIGGER ALL;
```

## Best Practices

1. **Always backup first**
   ```bash
   pg_dump -h localhost -U classifier_user classifier_test > backup_$(date +%s).dump
   ```

2. **Test rollback in staging**
   - Never first rollback in production

3. **Document changes**
   - Update IMPLEMENTATION_LOG.md with rollback reason

4. **Verify structure after rollback**
   ```sql
   -- Confirm clean state
   SELECT COUNT(*) FROM information_schema.tables
   WHERE table_schema = 'public' AND table_catalog = 'classifier_test';
   ```

5. **Keep migration files**
   - Don't delete .sql files, keep them for reference and re-application

---

**Last Updated**: 2025-10-25
**Tested**: Not yet (development)
**Status**: Ready for use
