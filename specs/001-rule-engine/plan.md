# Implementation Plan: Rule Engine Core with Priority & Audit

**Branch**: `001-rule-engine` | **Date**: 2025-10-25 | **Spec**: [specs/001-rule-engine/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-rule-engine/spec.md`

## Summary

Build a generic, data-driven rule evaluation engine that reads classification rules from the database (`regras_de_classificacao`), applies them with deterministic priority ordering, and logs all classification decisions for auditability. The engine supports flexible rule criteria (keywords, NCM patterns, size/quantity ranges) without code changes, directly implementing Constitutional Principle I (Data-Driven Logic) and enabling business teams to manage rules without deployment cycles.

## Technical Context

**Language/Version**: Python 3.8+
**Primary Dependencies**: psycopg2 or SQLAlchemy (database driver), logging (built-in)
**Storage**: PostgreSQL 12+ (configured via `.env`: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)
**Testing**: pytest for unit and integration tests
**Target Platform**: Linux server (command-line/API backend)
**Project Type**: Single project — Python rule engine library with optional CLI/API wrapper
**Constraints**: Simple field matching without complex sub-query logic; stateless evaluation
**Scale/Scope**: Support thousands of active rules; millions of classification requests per day

## Category Management Strategy

**New in v1.2.0**: `categorias` table provides centralized category management with referential integrity.

**Schema Design**:
- `categorias` table created FIRST (dependency for rules and products)
- `regras_de_classificacao.categoria_id` → Foreign Key to `categorias.id` (ON DELETE RESTRICT, ON UPDATE CASCADE)
- `produtos_tabela.categoria_id` → Foreign Key to `categorias.id` (optional for product history)

**Category Seeding**:
- Base categories must be seeded during initialization (via migration or init script)
- Examples: ELETRÔNICOS, CABOS, ACESSÓRIOS, PERIFÉRICOS, COMPONENTES
- All rules MUST reference valid category IDs

**Benefits**:
- Data normalization (prevent category name duplication)
- Referential integrity (prevent orphaned/invalid category references)
- Flexible category management (rename, deactivate, group without code changes)
- Audit trail (track category usage via rule/product relationships)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Principles Alignment** ✅

✅ **Principle I - Data-Driven Logic**:
- All rules read from `regras_de_classificacao` table (no hardcoded logic)
- Classification decisions derive entirely from database records
- Rules are queryable and auditable through database

✅ **Principle II - Code Simplicity & Genericity**:
- Rule engine is generic, agnostic to rule content
- No product-specific hardcoded exceptions
- Complex logic expressed via rule composition, not code branching

✅ **Principle III - Rule Composition & Flexibility**:
- Schema accommodates keywords, NCM, size, quantity criteria
- New criteria types addable via schema extension only
- No code changes needed for new rule types

✅ **Principle IV - Test-First Strategy**:
- Tests required for: rule evaluation, priority resolution, edge cases, performance
- Database schema changes include migration tests

✅ **Principle V - Backward Compatibility & Auditability**:
- Audit logs table (`auditoria_classificacao`) required
- Every decision traceable to rule(s) that produced it
- Migrations must be reversible

**Database Infrastructure Requirements** (from Constitution):
- `.env` file MUST contain: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT ✅
- Three core tables MUST be created: `regras_de_classificacao`, `auditoria_classificacao`, `criterios_palavras_chave` ✅
- Database schema MUST match specifications in constitution.md ✅
- All migrations MUST be reversible with rollback procedures ✅

**Gate Status**: ✅ PASSED — All constitutional requirements can be met with proposed design

## Project Structure

### Documentation (this feature)

```text
specs/001-rule-engine/
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0 (research findings)
├── data-model.md                    # Phase 1 (entity definitions & schema)
├── quickstart.md                    # Phase 1 (getting started guide)
├── contracts/                       # Phase 1 (API/library contracts)
│   ├── rule_engine_api.md
│   └── audit_log_schema.md
├── checklists/
│   └── requirements.md              # Quality validation checklist
└── tasks.md                         # Phase 2 output (/speckit.tasks command)
```

### Source Code (Single Project Structure)

```text
.
├── .env                             # Database configuration (NOT in git)
├── .env.example                     # Template for developers
├── migrations/                      # Database migrations
│   ├── 002_create_categorias.sql    # Categories reference table (FIRST)
│   ├── 003_create_regras_de_classificacao.sql  # Rules with FK to categorias
│   └── 004_create_indexes.sql
├── src/
│   └── classifier/
│       ├── __init__.py
│       ├── models.py                # Database models (Product, Rule, AuditLog)
│       ├── engine.py                # Core RuleEngine class
│       ├── evaluator.py             # Rule evaluation logic
│       ├── matcher.py               # Criteria matching (keywords, NCM, ranges)
│       ├── audit.py                 # Audit logging
│       ├── utils.py                 # Utilities (config, db connection)
│       └── cli/                      # Command-line interface scripts (US4, US5)
│           ├── __init__.py
│           ├── classify_batch.py    # Batch classification from database (US4)
│           ├── classify_csv.py      # CSV import/classification/export (US5)
│           └── export_batch.py      # Export classified data to CSV (US5 optional)
├── tests/
│   ├── conftest.py                  # pytest fixtures
│   ├── contract/
│   │   └── test_rule_engine_api.py
│   ├── integration/
│   │   ├── test_rule_evaluation.py
│   │   ├── test_priority_resolution.py
│   │   ├── test_audit_logging.py
│   │   ├── test_batch_classification.py    # Tests for classify_batch.py (US4)
│   │   └── test_csv_classification.py      # Tests for classify_csv.py (US5)
│   └── unit/
│       ├── test_matcher.py
│       ├── test_evaluator.py
│       └── test_audit.py
├── docs/
│   ├── setup.md                     # Installation & configuration
│   ├── rules_guide.md               # How to create/manage rules
│   ├── batch_classification.md      # Guide for batch processing (US4)
│   └── csv_classification.md        # Guide for CSV import/export (US5)
├── input/                           # Example input directory for CSV files
│   └── .gitkeep
├── output/                          # Example output directory for CSV results
│   └── .gitkeep
├── requirements.txt                 # Python dependencies
└── setup.py                         # Package installation
```

**Structure Decision**: Single Python project with modular organization (models, engine, evaluator, matcher, audit). Database migrations stored separately. Comprehensive test suite organized by test type (contract, integration, unit). Clear separation of concerns enabling constitutional Principle II (Code Simplicity).

## Implementation Approach for User Stories 4 & 5 (Batch & CSV Processing)

### User Story 4: Batch Classification from Database

**Purpose**: Enable operators to classify multiple unclassified products from the database using a single command-line script.

**Command Pattern**:
```bash
python classify_batch.py -500              # Classify 500 products
python classify_batch.py -1000 --offset 100 # Classify 1000 products starting at offset 100
python classify_batch.py -500 --where "size < 10"  # Custom filter
```

**Implementation**:
- Script fetches unclassified products from database (WHERE categoria IS NULL)
- Uses core RuleEngine to classify each product
- Updates `categoria` field in products table
- Creates audit log entries for each classification (including NO_MATCH cases)
- Reports progress: "X of Y processed, estimated time: Z minutes"
- Handles database errors gracefully (logs error, continues with next product, reports summary)

**Key Features**:
- Supports `--limit` parameter to control batch size
- Supports `--offset` parameter for pagination
- Supports `--where` parameter for custom filtering
- Transaction handling: individual product transactions (not all-or-nothing batch)
- Performance target: 500 products in < 5 minutes

### User Story 5: CSV Classification Import & Export

**Purpose**: Enable flexible classification of products from CSV files for ad-hoc analysis, Excel integration, and external system workflows.

**Command Patterns**:
```bash
# Basic: CSV → Classify → Output CSV
python classify_csv.py --input productos.csv --output clasificados.csv

# With column mapping (for non-standard column names)
python classify_csv.py --input productos.csv --output clasificados.csv \
  --product-id id_coluna \
  --description desc_coluna \
  --ncm ncm_coluna

# With separate audit CSV
python classify_csv.py --input productos.csv --output clasificados.csv --audit audit.csv

# With database update (CSV → Classify → Output CSV + Update Database)
python classify_csv.py --input productos.csv --output clasificados.csv --update-db
```

**Output CSV Structure**:
```csv
id,description,ncm,size,quantity,categoria,rule_id,rule_name,matched_criteria,evaluation_time_ms
P001,Laptop Dell,84713090,0.5,1,ELECTRONICS,1,Laptop Rule,keywords: laptop,45
P002,USB Cable,85444290,0.02,100,CABLES,5,NCM 8544,ncm: 8544*,32
P003,Product,12345678,1.0,1,NO_MATCH,,None,none,25
```

**Implementation**:
- Reads CSV with flexible column mapping (default: id, description, ncm, size, quantity)
- For each row: validates data, classifies using RuleEngine, captures result and timing
- Writes output CSV with all original columns + classification metadata
- Optional: creates separate audit.csv with audit log entries
- Optional: updates database with classifications (using classify_batch logic)
- Handles CSV errors gracefully (reports line number, skips invalid rows, continues)
- Performance target: 50,000 rows in < 10 minutes

**Three Operating Modes** (documented in CSV_CLARIFICATION.md):
1. **CSV-Only**: Input CSV → Output CSV (no database changes)
2. **CSV→DB**: Input CSV → Classify → Output CSV + Update Database
3. **DB→CSV**: Batch classify database → Export to CSV

### Shared Components

Both scripts leverage:
- Core `RuleEngine` class from Phase 1-3 (User Stories 1-3)
- `AuditLog` class for recording classifications
- Database connection utilities from `utils.py`
- Progress reporting utility for CLI feedback
- Comprehensive error handling with detailed logging

### Testing Strategy for US4 & US5

**Batch Classification Tests** (`test_batch_classification.py`):
- Fetches correct number of products with limit/offset
- Updates categoria field correctly
- Creates audit log entries for all classifications
- Handles database errors (connection loss, constraint violations)
- Reports accurate progress metrics
- Performance: 500 products complete in under 5 minutes

**CSV Classification Tests** (`test_csv_classification.py`):
- Reads CSV with default and custom column mappings
- Validates data before processing (missing required fields, invalid formats)
- Classifies rows correctly and captures timing
- Writes output CSV with correct structure
- Handles invalid/missing data (skips invalid rows, continues valid ones)
- Creates separate audit CSV when requested
- Updates database when --update-db flag used
- Performance: 50,000 rows complete in under 10 minutes

## Complexity Tracking

**No Constitution Check violations.** Design fully aligns with all five core principles and infrastructure requirements. No complexity justifications needed.
