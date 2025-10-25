# Classifier v2: Rule Engine Core

A data-driven product classification system with flexible rule evaluation, priority resolution, and comprehensive audit logging.

## Overview

**Classifier v2** moves classification logic from hardcoded Python rules to a database-driven architecture. Rules are stored in the database (`regras_de_classificacao` table), allowing non-technical users to manage classifications without code changes.

### Key Features

- **Data-Driven Rule Evaluation**: Rules defined in database, not code
- **Priority-Based Conflict Resolution**: Multiple matching rules always resolve consistently
- **Comprehensive Audit Logging**: Full traceability of all classification decisions
- **Batch Processing**: Classify multiple products from database with one command
- **CSV Import/Export**: Support for spreadsheet-based workflows
- **Flexible Criteria Matching**: Keywords, NCM patterns, size/quantity ranges

## Architecture

```
RuleEngine (Python)
    ├── Matcher (criteria matching)
    ├── Evaluator (rule selection)
    └── AuditLog (decision logging)
         ↓
    PostgreSQL Database
    ├── regras_de_classificacao (rules table)
    ├── auditoria_classificacao (audit log)
    └── criterios_palavras_chave (keyword index)
```

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd classifier-rules

# Create virtual environment
python3.8+ -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Install package in development mode
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your database credentials
# DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
```

### Database Setup

```bash
# Initialize database (creates tables and migrations)
python -c "from classifier.utils import init_database; init_database()"
```

### First Classification

```python
from classifier.engine import RuleEngine

# Create engine instance
engine = RuleEngine()

# Classify a product
product = {
    "id": "P001",
    "description": "laptop computer",
    "ncm": "84713090",
    "size": 0.5,
    "quantity": 1
}

result = engine.evaluate(product)
print(result)
# Output: {'classification': 'ELECTRONICS', 'rule_id': 1, 'priority': 100, ...}
```

## Usage

### Basic Rule Evaluation (US1)

```python
engine = RuleEngine()
product = {"id": "P001", "description": "laptop", "ncm": "84713090"}
result = engine.evaluate(product)
```

### Batch Classification from Database (US4)

```bash
# Classify 500 unclassified products
python -m classifier.cli.classify_batch -500

# With custom filters
python -m classifier.cli.classify_batch -1000 --offset 100
```

### CSV Classification (US5)

```bash
# Simple CSV classification
python -m classifier.cli.classify_csv \
  --input productos.csv \
  --output result.csv

# With audit trail
python -m classifier.cli.classify_csv \
  --input productos.csv \
  --output result.csv \
  --audit audit.csv

# Also update database
python -m classifier.cli.classify_csv \
  --input productos.csv \
  --output result.csv \
  --update-db
```

## Documentation

- **[Specification](specs/001-rule-engine/spec.md)**: Complete feature specification with 5 user stories
- **[Implementation Plan](specs/001-rule-engine/plan.md)**: Technical architecture and project structure
- **[Data Model](specs/001-rule-engine/data-model.md)**: Database schema and entity relationships
- **[CSV Guide](specs/001-rule-engine/CSV_CLARIFICATION.md)**: CSV modes and storage locations
- **[Quickstart](specs/001-rule-engine/quickstart.md)**: Detailed setup and usage guide

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/classifier tests/

# Run specific test file
pytest tests/unit/test_matcher.py

# Run tests matching pattern
pytest -k "test_priority" -v
```

## Project Structure

```
.
├── src/classifier/
│   ├── __init__.py          # Exception classes
│   ├── models.py            # Data models (Rule, Product, etc)
│   ├── engine.py            # Core RuleEngine class
│   ├── evaluator.py         # Rule evaluation logic
│   ├── matcher.py           # Criteria matching
│   ├── audit.py             # Audit logging service
│   ├── utils.py             # Config and database utilities
│   └── cli/
│       ├── classify_batch.py     # Batch classification script
│       ├── classify_csv.py       # CSV import/export script
│       └── export_batch.py       # Database export script
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── contract/            # API contract tests
│   ├── integration/         # End-to-end tests
│   └── unit/                # Component tests
├── migrations/              # Database migrations
│   ├── 001_create_tables.sql
│   ├── 002_create_indexes.sql
│   └── ROLLBACK.md
├── docs/                    # Documentation
├── specs/                   # Feature specifications
├── input/                   # Input CSV files
├── output/                  # Output files
├── setup.py                 # Package configuration
└── requirements.txt         # Dependencies
```

## Database Schema

### regras_de_classificacao (Rules)
```sql
id              | SERIAL PRIMARY KEY
prioridade      | INTEGER (higher = more important)
nome            | VARCHAR (rule name)
ativo           | BOOLEAN (enabled/disabled)
criterio_palavras_chave     | VARCHAR (keywords to match)
criterio_ncm    | VARCHAR (NCM pattern with *)
criterio_tamanho_min | FLOAT
criterio_tamanho_max | FLOAT
criterio_quantidade_min | INT
criterio_quantidade_max | INT
resultado_classificacao | VARCHAR
data_criacao    | TIMESTAMP
data_atualizacao | TIMESTAMP
```

### auditoria_classificacao (Audit Log)
```sql
id              | SERIAL PRIMARY KEY
id_regra        | INTEGER FOREIGN KEY
id_produto      | VARCHAR
descricao_produto | VARCHAR
criterios_combinados | VARCHAR (JSON)
resultado_classificacao | VARCHAR
data_classificacao | TIMESTAMP
tempo_avaliacao_ms | INTEGER
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | - | PostgreSQL server hostname |
| `DB_NAME` | Yes | - | Database name |
| `DB_USER` | Yes | - | Database user |
| `DB_PASSWORD` | Yes | - | Database password |
| `DB_PORT` | No | 5432 | PostgreSQL port |
| `APP_LOG_LEVEL` | No | INFO | Logging level |
| `ENABLE_RULE_CACHING` | No | true | Cache rules in memory |

## Development

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_matcher.py -v

# With coverage report
pytest --cov=src/classifier --cov-report=html

# Performance tests
pytest tests/performance/ -v
```

### Code Style

```bash
# Format code with black
black src/ tests/

# Check code with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

## Performance Targets

- **Rule Evaluation**: < 500ms for 95th percentile with 10,000 active rules
- **Batch Processing**: 500 products in < 5 minutes
- **CSV Processing**: 50,000 rows in < 10 minutes
- **Audit Logging**: 100% completeness for all classifications

## Troubleshooting

### Database Connection Issues

```python
from classifier.utils import get_db_connection
try:
    conn = get_db_connection()
except DatabaseError as e:
    print(f"Connection failed: {e}")
```

### No Rules Match

```python
result = engine.evaluate(product)
if result['classification'] == 'NO_MATCH':
    print(f"Product {product['id']} did not match any rules")
    # Check audit logs for attempted matching
```

### CSV Encoding Issues

Ensure CSV files are UTF-8 encoded:

```bash
# Convert CSV to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 input.csv > input_utf8.csv
```

## Contributing

1. Create feature branch from `main`
2. Follow the specification in `specs/001-rule-engine/spec.md`
3. Write tests first (TDD approach)
4. Ensure all tests pass: `pytest`
5. Follow code style: `black` and `flake8`
6. Create pull request with description

## License

[Your License Here]

## Support

For issues, questions, or suggestions:
- Check the [Specification](specs/001-rule-engine/spec.md)
- Review the [Quickstart Guide](specs/001-rule-engine/quickstart.md)
- Open an issue on GitHub

## Roadmap

### Phase 1: MVP (User Stories 1-3)
- ✓ Basic rule evaluation
- ✓ Priority resolution
- ✓ Audit logging

### Phase 2: Scripting (User Stories 4-5)
- ⏳ Batch classification from database
- ⏳ CSV import/export support

### Phase 3: Polish & Deployment
- ⏳ Performance optimization
- ⏳ Comprehensive documentation
- ⏳ Production deployment guide

---

**Last Updated**: 2025-10-25
**Version**: 0.1.0-alpha
**Status**: In Development
