# Quick Start Guide - Classifier v2

The product classification system is now fully implemented and ready to use. This guide walks you through getting started in 5 minutes.

## 1. Prerequisites Check (1 minute)

Your system needs:
- ✅ Python 3.8+ with virtual environment activated
- ✅ PostgreSQL database with `produtos_tabela` table
- ✅ Classifier package installed (`pip install -e .`)

**Verify environment:**
```bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras
python3 -c "import classifier; print('✅ Classifier installed')"
```

## 2. Verify Database (1 minute)

Your database must have these three Portuguese tables:

```bash
# List tables in your database
psql -U postgres -d classifier -c "\dt"
```

**Must see:**
- `produtos_tabela` - Products to classify
- `regras_de_classificacao` - Classification rules
- `auditoria_classificacao` - Audit trail

**If tables are missing**, see DATABASE_SETUP.md for creation scripts.

## 3. Test Connection (1 minute)

```bash
# Check database statistics
classify-batch --stats
```

**Should output:**
```
BATCH CLASSIFICATION STATISTICS
============================================================
Total Products:       X products
Classified:           X products
Unclassified:        X products
Classification Rate:  X%
```

If you see `relation 'produtos_tabela' does not exist` error, your database table naming is incorrect (see VERIFY_DATABASE.md).

## 4. Classify Products (2 minutes)

### Option A: Batch from Database

```bash
# Classify next 10 unclassified products
classify-batch --limit 10

# Or with dry-run to preview what would happen
classify-batch --limit 10 --dry-run
```

### Option B: Import from CSV

```bash
# Process CSV file
classify-csv samples/products_basic.csv

# Output file: samples/products_basic_classified.csv
# Check results
head samples/products_basic_classified.csv
```

### Option C: Python API

```python
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

db = get_db_connection()
engine = RuleEngine(db)

# Classify single product
result = engine.evaluate({
    'id': 'PROD_001',
    'description': 'laptop dell',
    'ncm': '84713090'
})

print(f"Classification: {result.classification}")
print(f"Matched: {result.success}")
```

## 5. Monitor Results

```bash
# View overall statistics
classify-batch --stats

# See recent classifications
psql -U postgres -d classifier -c "
  SELECT id_produto, resultado_classificacao, data_classificacao
  FROM auditoria_classificacao
  ORDER BY data_classificacao DESC
  LIMIT 10;
"

# Find products that couldn't be classified
psql -U postgres -d classifier -c "
  SELECT id, description
  FROM produtos_tabela
  WHERE categoria IS NULL
  LIMIT 10;
"
```

## 6. Next Steps

- **See detailed instructions**: HOW_TO_RUN.md
- **Test the system**: TESTING_GUIDE.md
- **Understand database**: DATABASE_SETUP.md
- **Verify setup**: VERIFY_DATABASE.md
- **View full project**: PROJECT_SUMMARY.md

---

## Common Issues & Quick Fixes

### ❌ "relation 'productos_tabela' does not exist"
**Fix**: Your database table name is wrong. Check VERIFY_DATABASE.md for the correct Portuguese name: `produtos_tabela`

### ❌ "No such file or directory"
**Fix**: Make sure you're in the correct directory:
```bash
cd /home/divinopc/testes/projects/classifier_regras
source /tmp/classifier_venv/bin/activate
```

### ❌ "could not connect to database"
**Fix**: PostgreSQL must be running:
```bash
sudo systemctl start postgresql
# or
pg_ctl -D /usr/local/var/postgres start
```

### ❌ "No products matched"
**Fix**: Check that rules exist with active criteria:
```bash
psql -U postgres -d classifier -c "
  SELECT id, nome, criterio_palavras_chave, ativo
  FROM regras_de_classificacao
  WHERE ativo = true
  LIMIT 5;
"
```

If empty, create test rules (see DATABASE_SETUP.md).

---

## Architecture Overview

The classifier uses a **data-driven rule engine**:

1. **Rules in Database** (`regras_de_classificacao`)
   - Rules are stored as database records, not hardcoded
   - Each rule has: name, priority, criteria, result, status
   - Priority determines rule selection when multiple rules match

2. **Flexible Matching** (5 criteria types)
   - Keyword matching (substring search in description)
   - NCM pattern matching (wildcard patterns)
   - Size range matching (min/max)
   - Quantity range matching (min/max)
   - Category exact matching

3. **Deterministic Selection**
   - Higher priority rules win
   - Same priority: older rule wins (FIFO)
   - All decisions logged to `auditoria_classificacao`

4. **Audit Trail** (Immutable)
   - Every classification recorded with timestamp
   - Can trace which rule made each decision
   - Complete history for compliance

## Command Reference

### Batch Classification
```bash
# Classify 500 products
classify-batch

# Classify with custom limit
classify-batch --limit 100

# Dry-run (preview without updating DB)
classify-batch --limit 10 --dry-run

# Show statistics only
classify-batch --stats

# JSON output
classify-batch --limit 10 --json

# Filter specific products (e.g., NCM starting with 84)
classify-batch --where "ncm LIKE '84%'" --limit 50

# Verbose logging
classify-batch --limit 10 --verbose
```

### CSV Classification
```bash
# Process CSV file
classify-csv input.csv

# Specify output file
classify-csv input.csv --output results.csv

# Validate CSV before processing
classify-csv input.csv --validate

# Update database with results
classify-csv input.csv --update-db

# Skip already classified rows
classify-csv input.csv --skip-classified

# Custom CSV format (semicolon delimiter, Latin-1 encoding)
classify-csv input.csv --delimiter ";" --encoding "latin-1"

# Process in batches of 100 rows
classify-csv input.csv --batch-size 100

# JSON output
classify-csv input.csv --json

# Dry-run
classify-csv input.csv --dry-run
```

## Key Files

| File | Purpose |
|------|---------|
| `QUICK_START.md` | This guide (5-minute setup) |
| `HOW_TO_RUN.md` | Detailed execution methods |
| `TESTING_GUIDE.md` | Comprehensive testing |
| `DATABASE_SETUP.md` | Database configuration |
| `VERIFY_DATABASE.md` | Database verification |
| `PROJECT_SUMMARY.md` | Full project overview |
| `src/classifier/engine.py` | Core rule engine |
| `src/classifier/batch.py` | Batch classification service |
| `src/classifier/csv_classifier.py` | CSV processing service |
| `src/classifier/cli/` | Command-line interfaces |

## Testing

The system includes 277 automated tests:
- 150+ unit tests (components in isolation)
- 80+ integration tests (workflows)
- 35+ contract tests (API specifications)
- 12 CLI tests (command-line interfaces)

Run tests:
```bash
# Quick test (30 seconds)
pytest tests/unit/ tests/cli/ -q

# Full test (without database)
pytest tests/ -q

# With coverage report
pytest tests/ --cov=src/classifier
```

---

**Status**: ✅ System fully implemented and ready
**Latest Fix**: Database table names corrected to Portuguese (`produtos_tabela`)
**Documentation**: Complete guides provided for all use cases
**Tests**: 189 unit/CLI tests passing ✅

