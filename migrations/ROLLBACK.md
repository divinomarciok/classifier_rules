# Migration Rollback Procedures

**Last Updated**: 2025-10-26
**Current Migrations**: 002_create_categorias, 003_create_regras_de_classificacao, 004_create_auditoria_classificacao, 005_create_criterios_palavras_chave

This document provides instructions for rolling back database migrations in case of errors or need to revert to a previous state.

## ⚠️ Critical: New categorias Table

**IMPORTANT**: As of 2025-10-26, a new `categorias` table has been added as a reference table. This creates a NEW dependency order:

**NEW Dependency Chain**:
```
Migration 002: categorias (no dependencies)
    ↓ (referenced by)
    ├─ Migration 003: regras_de_classificacao (categoria_id FK)
    ├─ Migration 004: auditoria_classificacao (references regras_de_classificacao)
    └─ Migration 005: criterios_palavras_chave (references regras_de_classificacao)
```

**Rollback MUST be in reverse order**:
1. Drop 005 (criterios_palavras_chave)
2. Drop 004 (auditoria_classificacao)
3. Drop 003 (regras_de_classificacao) - MUST be before categorias
4. Drop 002 (categorias) - LAST because rules depend on it

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

-- Rollback in REVERSE order (CRITICAL: categorias must be dropped LAST)

-- Drop Migration 005: Keywords table first (references Migration 003)
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;

-- Drop Migration 004: Audit log table (references Migration 003)
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;

-- Drop Migration 003: Rules table (references Migration 002 - categorias)
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;

-- Drop Migration 002: Categories table (referenced by Migration 003)
-- MUST be after regras_de_classificacao due to FK
DROP TABLE IF EXISTS categorias CASCADE;

-- Verify tables are gone
\dt

EOF
```

### Rolling Back Individual Migrations

#### Rollback Migration 005 Only (Keywords Index)

```sql
-- Safe: No other tables depend on this
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
```

#### Rollback Migration 004 Only (Audit Log)

```sql
-- WARNING: Deletes audit log history
-- First, back up audit data if needed
CREATE TABLE auditoria_classificacao_backup AS SELECT * FROM auditoria_classificacao;

DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
```

#### Rollback Migration 003 Only (Rules Table)

```sql
-- CRITICAL: You MUST rollback 004 and 005 first
-- regras_de_classificacao has FK reference to categorias
-- Cannot drop categorias while this table exists

-- Step 1: Verify dependencies
SELECT table_name FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND table_schema = 'public';

-- Step 2: Drop dependent references (4 and 5 must be gone first)
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;
```

#### Rollback Migration 002 Only (Categories Table)

```sql
-- DANGER: regras_de_classificacao depends on this!
-- You MUST rollback Migration 003 (regras_de_classificacao) first

-- Verify no tables reference categorias
SELECT *
FROM information_schema.referential_constraints
WHERE constraint_schema = 'public'
AND unique_constraint_name = 'categorias_pkey';

-- Only drop if regras_de_classificacao is already dropped
DROP TABLE IF EXISTS categorias CASCADE;
```

### Partial Data Cleanup (Keep Structure, Clear Data)

```sql
-- TRUNCATE in correct order (reverse of creation due to FKs)
TRUNCATE TABLE criterios_palavras_chave CASCADE;
TRUNCATE TABLE auditoria_classificacao CASCADE;
TRUNCATE TABLE regras_de_classificacao CASCADE;
TRUNCATE TABLE categorias CASCADE;

-- Or DELETE individually (slower but safer):
DELETE FROM criterios_palavras_chave;
DELETE FROM auditoria_classificacao;
DELETE FROM regras_de_classificacao;
DELETE FROM categorias;
```

## Recovery Procedures

### After Rollback, Re-apply Migrations

```bash
# Re-apply migrations in CORRECT order (categorias FIRST)
psql -h localhost -U classifier_user -d classifier_test -f migrations/002_create_categorias.sql
psql -h localhost -U classifier_user -d classifier_test -f migrations/003_create_regras_de_classificacao.sql
psql -h localhost -U classifier_user -d classifier_test -f migrations/004_create_auditoria_classificacao.sql
psql -h localhost -U classifier_user -d classifier_test -f migrations/005_create_criterios_palavras_chave.sql

# Verify
psql -h localhost -U classifier_user -d classifier_test -c "\dt"
```

### Restore from Backup

```bash
# If you have a backup from before the migration
pg_restore -h localhost -U classifier_user -d classifier_test /path/to/backup.dump
```

## Migration Dependencies

```
Migration 002: categorias (no dependencies)
    ↓ (referenced by)
    └─ Migration 003: regras_de_classificacao (categoria_id FK → categorias)
            ↓ (referenced by)
            ├─ Migration 004: auditoria_classificacao (id_regra FK)
            └─ Migration 005: criterios_palavras_chave (id_regra FK)
```

**Execution Order** (MUST be respected):
1. Migration 002: `categorias` (no dependencies, must be first)
2. Migration 003: `regras_de_classificacao` (depends on 002)
3. Migration 004: `auditoria_classificacao` (depends on 003)
4. Migration 005: `criterios_palavras_chave` (depends on 003)

**Rollback Order** (REVERSE of execution):
1. Migration 005 (criterios_palavras_chave) - safe to drop first
2. Migration 004 (auditoria_classificacao) - depends on 003
3. Migration 003 (regras_de_classificacao) - MUST be before 002
4. Migration 002 (categorias) - LAST because 003 references it

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

echo "Rolling back all migrations (correct order: 5→4→3→2)..."

psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Drop in REVERSE order (CRITICAL for FK dependencies)
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;

SELECT 'All tables dropped successfully' AS status;
EOF

echo "✓ Rollback complete - All migrations reverted"
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
