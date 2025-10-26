# Database Verification Guide

Quick verification steps to ensure your classifier system is ready to work with your database.

## Step 1: Verify Table Names (Critical!)

Your database **must** use these exact Portuguese table names:

```bash
# Connect to your PostgreSQL database
psql -U postgres -d classifier -c "\dt"
```

**Expected Output** - you should see these three tables:
```
                  List of relations
 Schema |         Name         | Type  |  Owner
--------+----------------------+-------+---------
 public | auditoria_classificacao | table | postgres
 public | produtos_tabela      | table | postgres
 public | regras_de_classificacao | table | postgres
```

**If you see different names**, the classifier won't work. The exact names must be:
- ✅ `produtos_tabela` (NOT `productos`, NOT `produtos`, NOT `products`)
- ✅ `regras_de_classificacao` (classification rules)
- ✅ `auditoria_classificacao` (audit trail)

## Step 2: Verify Table Structure

Check that each table has the required columns:

```bash
# Check produtos_tabela structure
psql -U postgres -d classifier -c "\d produtos_tabela"
```

**Expected columns:**
- `id` (text) - product identifier
- `description` (text) - product description
- `ncm` (text) - NCM code
- `categoria` (text, nullable) - classification result
- `size` (numeric, optional)
- `quantity` (numeric, optional)
- `data_classificacao` (timestamp, optional)

```bash
# Check regras_de_classificacao structure
psql -U postgres -d classifier -c "\d regras_de_classificacao"
```

**Expected columns:**
- `id` (integer) - rule identifier
- `nome` (text) - rule name
- `ativo` (boolean) - is rule active
- `prioridade` (integer) - priority/precedence
- `criterio_palavras_chave` (text, optional) - keyword matching
- `resultado_classificacao` (text) - classification result
- `data_criacao` (timestamp)
- `data_atualizacao` (timestamp)

## Step 3: Verify Data Exists

Check that you have products and rules to classify:

```bash
# Count products to classify
psql -U postgres -d classifier -c "SELECT COUNT(*) as total, COUNT(CASE WHEN categoria IS NULL THEN 1 END) as unclassified FROM produtos_tabela;"
```

**Expected:** Should show total products and how many are unclassified.

```bash
# Count active rules
psql -U postgres -d classifier -c "SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;"
```

**Expected:** Should show at least 1 active rule. If 0, create test rules (see DATABASE_SETUP.md).

## Step 4: Quick System Test

Run the classifier with statistics to verify database connection:

```bash
# Activate environment
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Test database connection with statistics
classify-batch --stats
```

**Expected Output:**
```
BATCH CLASSIFICATION STATISTICS
============================================================
Total Products:       X products
Classified:           X products
Unclassified:        X products
Classification Rate:  X%
```

**If you get an error:**
- ❌ `relation "productos_tabela" does not exist` → Fix table name (see DATABASE_SETUP.md)
- ❌ `permission denied` → Grant PostgreSQL permissions
- ❌ `could not connect to database` → Check PostgreSQL is running

## Step 5: Test Classification (with Limit)

Try classifying a small batch to verify rules work:

```bash
# Classify 5 products (safe test)
classify-batch --limit 5 --dry-run
```

**Expected Output:**
```
BATCH CLASSIFICATION SUMMARY
============================================================
Total Processed:     5 products
Total Matched:       X products (0-5)
Total No Match:      X products
Match Rate:          X%
...
```

**If no products matched:**
1. Check that rules exist: `SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;`
2. Check that rule criteria is set: `SELECT nome, criterio_palavras_chave FROM regras_de_classificacao LIMIT 5;`
3. Review DATABASE_SETUP.md to understand how rules work

## Step 6: Verify CSV Processing (Optional)

Test CSV import/classify/export:

```bash
# Validate a sample CSV
classify-csv samples/products_basic.csv --validate

# Process CSV (creates output file)
classify-csv samples/products_basic.csv --dry-run
```

## Troubleshooting Table Names

### Why Portuguese names?

Your database was set up with Portuguese table names because this is a Brazilian product classification system. The classifier code now correctly uses these Portuguese names:

- `produtos_tabela` = "products table"
- `regras_de_classificacao` = "classification rules table"
- `auditoria_classificacao` = "audit trail table"

### Common Mistakes

❌ **Wrong**: `SELECT * FROM productos` (Spanish spelling)
✅ **Right**: `SELECT * FROM produtos_tabela` (Portuguese spelling + _tabela suffix)

❌ **Wrong**: `SELECT * FROM products` (English)
✅ **Right**: `SELECT * FROM produtos_tabela` (Portuguese)

❌ **Wrong**: `SELECT * FROM produto` (singular)
✅ **Right**: `SELECT * FROM produtos_tabela` (plural + _tabela)

### Verify Fix Applied

The classifier code has been updated to use the correct Portuguese table names:

```bash
# Verify the fix was applied
grep "produtos_tabela" src/classifier/batch.py src/classifier/csv_classifier.py

# You should see multiple matches confirming the table name is used
```

## Next Steps

1. ✅ **Verified tables exist** → Run `classify-batch --stats`
2. ✅ **Verified data exists** → Check product and rule counts
3. ✅ **Connection works** → System is ready to classify
4. ✅ **Rules are working** → Classified products appear in results

If all steps pass, your classifier system is ready! See HOW_TO_RUN.md for usage examples.

## Support

- **Database questions**: See DATABASE_SETUP.md for detailed SQL examples
- **How to run classifier**: See HOW_TO_RUN.md for all execution methods
- **Testing the system**: See TESTING_GUIDE.md for comprehensive test coverage
- **Project overview**: See PROJECT_SUMMARY.md for architecture details

---

**Last Updated**: Table name fixes verified (produtos_tabela)
**Status**: ✅ Code corrected, ready for database testing
