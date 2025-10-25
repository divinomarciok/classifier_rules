# Quickstart: Rule Engine Core

**Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Purpose**: Get up and running with the Rule Engine in 5 minutes

## 1. Setup Database

### Prerequisites
- PostgreSQL 12+ running
- Database created (e.g., `market_v1`)
- User with permissions to create tables

### Configure Environment

Copy `.env.example` to `.env` and update with your database details:

```bash
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_NAME=market_v1
DB_USER=your_user
DB_PASSWORD=your_password
DB_PORT=5432
```

### Create Schema

Run migrations to create required tables:

```bash
python -m classifier.migrations init
# OR manually run SQL:
# psql -h localhost -U your_user -d market_v1 -f migrations/001_create_tables.sql
```

This creates:
- `regras_de_classificacao` (rules table)
- `auditoria_classificacao` (audit logs)
- `criterios_palavras_chave` (optional keywords)

## 2. Install Package

```bash
pip install -e .
```

Or from requirements.txt:
```bash
pip install -r requirements.txt
```

## 3. Create Your First Rule

Insert a test rule into the database:

```python
from classifier.models import Rule
from classifier.utils import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Insert a keyword-based rule
cursor.execute("""
    INSERT INTO regras_de_classificacao
    (prioridade, nome, ativo, criterio_palavras_chave, resultado_classificacao)
    VALUES (100, 'Laptop Rule', TRUE, 'laptop,computer', 'ELECTRONICS')
""")
conn.commit()
```

Or use SQL directly:

```sql
INSERT INTO regras_de_classificacao
(prioridade, nome, ativo, criterio_palavras_chave, resultado_classificacao)
VALUES (100, 'Laptop Rule', TRUE, 'laptop,computer', 'ELECTRONICS');
```

## 4. Classify a Product

```python
from classifier.engine import RuleEngine

# Initialize engine
engine = RuleEngine()

# Create product data
product = {
    'id': 'PROD_001',
    'description': 'Dell XPS 13 laptop computer',
    'ncm': '84713090',
    'size': 0.5,
    'quantity': 1,
    'category': 'COMPUTERS'
}

# Classify
result = engine.evaluate(product)

print(result)
# Output:
# {
#   'classification': 'ELECTRONICS',
#   'rule_id': 1,
#   'rule_name': 'Laptop Rule',
#   'matched_criteria': ['keywords: laptop, computer'],
#   'evaluation_time_ms': 45
# }
```

## 5. Check Audit Logs

View what rules were applied:

```python
from classifier.audit import AuditLog

# Get recent classifications
audit = AuditLog()
history = audit.get_product_history('PROD_001')

for entry in history:
    print(f"Rule {entry['rule_id']} applied at {entry['timestamp']}")
    print(f"Result: {entry['classification']}")
    print(f"Criteria matched: {entry['criteria']}")
```

Or query directly:

```sql
SELECT * FROM auditoria_classificacao
WHERE id_produto = 'PROD_001'
ORDER BY data_classificacao DESC;
```

## 6. Run Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/test_evaluator.py
pytest tests/integration/test_rule_evaluation.py

# Run with coverage
pytest --cov=classifier
```

## Common Tasks

### Add a Priority-Based Rule

```sql
INSERT INTO regras_de_classificacao
(prioridade, nome, ativo, criterio_ncm, resultado_classificacao)
VALUES (90, 'NCM 8471 Rule', TRUE, '8471*', 'COMPUTERS');
```

### Disable a Rule

```sql
UPDATE regras_de_classificacao SET ativo = FALSE WHERE id = 1;
```

### Create a Complex Rule

```sql
INSERT INTO regras_de_classificacao
(prioridade, nome, ativo,
 criterio_palavras_chave,
 criterio_tamanho_min, criterio_tamanho_max,
 criterio_quantidade_min, criterio_quantidade_max,
 resultado_classificacao)
VALUES (110, 'Large Electronics', TRUE,
        'laptop,computer,tablet',
        1.0, 10.0,
        1, 100,
        'LARGE_ELECTRONICS');
```

### Find Rules by Priority

```sql
SELECT id, nome, prioridade FROM regras_de_classificacao
WHERE ativo = TRUE
ORDER BY prioridade DESC;
```

### Trace a Classification

```sql
SELECT * FROM auditoria_classificacao
WHERE id_produto = 'PROD_001'
LIMIT 5;
```

## Architecture Overview

```
┌─────────────────┐
│  Product Data   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  RuleEngine                     │
│  ├─ Fetches active rules        │
│  ├─ Matcher.evaluate()          │
│  ├─ Evaluator.select_winner()   │
│  └─ AuditLog.record()           │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Classification       │
│ Result + Rule ID     │
└──────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ auditoria_classificacao (DB)       │
│ - Rule applied                     │
│ - Timestamp                        │
│ - Matched criteria                 │
└────────────────────────────────────┘
```

## Troubleshooting

### "Connection refused" error
- Check DB_HOST, DB_PORT, DB_USER in `.env`
- Verify PostgreSQL is running: `psql -h localhost`

### "Table does not exist"
- Run migrations: `python -m classifier.migrations init`

### "No rule matches product"
- Check `criterio_*` fields in rules
- Ensure rule is `ativo = TRUE`
- Review audit logs to see what criteria were evaluated

### Rules not applied in expected order
- Check `prioridade` values in `regras_de_classificacao`
- Higher priority wins: sort by `ORDER BY prioridade DESC`

## Next Steps

1. Create more rules for your product types
2. Test with your own product data
3. Monitor audit logs for classification patterns
4. Adjust priorities based on accuracy metrics
5. Add new criteria types as needed (via schema migration)

See `/specs/001-rule-engine/data-model.md` for detailed schema information and `/docs/rules_guide.md` for business rule creation guidelines.
