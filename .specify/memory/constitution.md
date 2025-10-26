<!--
SYNC IMPACT REPORT
==================
Version Change: 1.1.0 → 1.2.0
Rationale: Added categorias reference table with FK relationships for data normalization and integrity
New Sections Added:
  - categorias table specification in "Required Tables & Columns"
Modified Sections:
  - Core Tables list: Added categorias as REQUIRED core table
  - regras_de_classificacao: Changed resultado_classificacao (VARCHAR) to categoria_id (FK)
  - regras_de_classificacao: Added ON DELETE RESTRICT, ON UPDATE CASCADE constraints
Sections Affected:
  - Data Schema Governance (added referential integrity requirements)
  - Governance (updated compliance verification for FK constraints)
Templates & Docs Requiring Updates:
  ⚠️ spec.md (add Category entity, update Rule/Product entities, add FR-001b)
  ⚠️ plan.md (update database schema, add categorias migration)
  ⚠️ tasks.md (reorder migrations: categorias FIRST, renumber T008-T012)
  ⚠️ CLAUDE.md (add categorias setup, seed categories examples, troubleshooting)
  ⚠️ conftest.py fixtures (insert categorias before regras_de_classificacao)
  ⚠️ models.py (when implemented: add Category class, update Rule.categoria_id, Product.categoria_id)
Follow-up TODOs:
  - Create migration: 002_create_categorias.sql
  - Update migrations: 003_create_regras_de_classificacao.sql (add FK)
  - Create seed script: src/classifier/seed_categories.py
  - Update all tests to handle category relationships
-->

# Classifier v2 Constitution

## Core Principles

### I. Data-Driven Logic

The Python application is a generic rules engine that reads and applies classification logic
from the database. **Logic resides in data, not in code.**

**Non-negotiable rules:**
- All classification rules MUST be stored in the `regras_de_classificacao` table
- No hardcoded classification logic is permitted in Python code
- Validation and classification decisions MUST derive from database records
- Rules MUST be queryable and auditable through the database

**Rationale:** Enables business teams to modify rules without code changes, reduces
deployment risk, and maintains a single source of truth for classification logic.

### II. Code Simplicity & Genericity

The codebase MUST remain simple and generic; special cases belong in database rules,
not in conditional logic.

**Non-negotiable rules:**
- No product-specific hardcoded classifications or exceptions
- Rule evaluation engine MUST be agnostic to rule content and structure
- Complex logic (AND/OR conditions, priority cascading) MUST be expressed through
  database record composition, not code branching
- Avoid technical debt through ad-hoc special cases

**Rationale:** Maintainability, scalability to thousands of rules, and reduced
cognitive load for future developers.

### III. Rule Composition & Flexibility

Rules MUST support flexible composition without requiring code changes, including
complex conditions (AND/OR logic) and arbitrary criteria combinations.

**Non-negotiable rules:**
- The schema MUST accommodate: keywords, product descriptions, NCM patterns,
  size, quantity, and other attributes as criteria
- Rule priority/precedence MUST be enforced consistently across all evaluations
- New rule types or criteria MUST be addable via schema extension, not code modification

**Rationale:** Enables rapid business rule iteration and scaling to complex
classification scenarios without development cycles.

### IV. Test-First Strategy

Testing MUST verify both rule logic and data consistency, given the data-driven nature.

**Non-negotiable rules:**
- Rule evaluation tests MUST validate: given input → correct rule matched
- Priority conflict tests MUST ensure highest-priority rule wins
- Edge case tests MUST cover: missing data, ambiguous matches, rule conflicts
- Performance tests MUST validate efficient lookup with large rule sets
- Database schema changes MUST include migration tests

**Rationale:** Data-driven systems require test coverage beyond code paths;
database integrity is critical to classification correctness.

### V. Backward Compatibility & Auditability

All schema and rule changes MUST maintain backward compatibility or provide
explicit migration paths. Business logic MUST remain auditable.

**Non-negotiable rules:**
- Rule schema changes MUST NOT break existing active rules without migration
- Every classification decision MUST be traceable to the rule(s) that produced it
- Rule changes MUST be logged with timestamps and audit context
- Deprecated rule structures MUST have clear migration documentation

**Rationale:** Maintains trust in the system, enables compliance audits, and
protects against unexpected behavior shifts.

## Maintenance Patterns

**Rule Management:**
- Rules are added/modified/disabled by updating database records, never by
  changing code
- Each rule type or matching strategy MUST be documented with examples in the
  database or a rules guide
- Rules MUST include clear descriptions of their purpose and applicability

**Performance Expectations:**
- Rule lookups MUST scale to support thousands of active rules
- Query performance MUST be optimized at the database level (indexing,
  partitioning, query design)
- Slow rule evaluations MUST be flagged and refactored through rule composition
  or database optimization, not code workarounds

## Data Schema Governance

**Table: `regras_de_classificacao`**

The classification rules table is the system's heart. All changes MUST follow
this governance:

- **Schema integrity:** Column additions MUST maintain backward compatibility
- **Naming consistency:** Attributes MUST use Portuguese naming per project convention
- **Documentation:** Every column MUST have clear meaning and example values
- **Validation:** Database constraints MUST enforce rule consistency (e.g., no
  orphaned priorities, no circular dependencies)
- **Migration:** Any breaking schema changes MUST include explicit migration
  scripts and rollback procedures

**Core Tables MUST include:**
- `categorias` — Category reference table with all valid classification categories
- `regras_de_classificacao` — Classification rules with priority and criteria, foreign key to categorias
- `auditoria_classificacao` — Audit logs tracking rule application history
- Any supporting tables for rule criteria (e.g., keywords, ranges, patterns)

## Infrastructure & Database Configuration

**Database Connection:**
All database configuration MUST be managed through environment variables in `.env`:

- **Required variables:**
  - `DB_HOST` — Database server hostname or IP address
  - `DB_NAME` — Database name (default: `market_v1`)
  - `DB_USER` — Database user account
  - `DB_PASSWORD` — Database user password
  - `DB_PORT` — Database port (default: 5432 for PostgreSQL)

- **Configuration governance:**
  - `.env` MUST NOT be committed to version control (add to `.gitignore`)
  - All developers/deployments MUST have a valid `.env` file before running
  - Environment variables MUST be documented in `docs/setup.md` or `README.md`
  - Default values MUST be provided for non-sensitive configuration
  - Sensitive values (passwords) MUST be provided via `.env` or deployment secrets

**Database Initialization:**
All required tables and schemas MUST be created before the application runs.
This governance includes:

- **Schema creation:** MUST use explicit migration scripts (SQL or ORM migrations)
- **Migration tracking:** MUST maintain version history of schema changes
- **Idempotent migrations:** Creating tables MUST be safe to run multiple times
  (use `CREATE TABLE IF NOT EXISTS` or equivalent)
- **Data initialization:** Required reference data and default rules MUST be
  seeded via migrations or initialization scripts
- **Rollback capability:** Every migration MUST have a documented rollback procedure

**Required Tables & Columns:**

**1. `categorias` (Product Categories - Reference Table)**
- `id` (PRIMARY KEY, INTEGER/SERIAL) — Unique category identifier
- `nome` (VARCHAR, NOT NULL, UNIQUE) — Category name (e.g., "ELETRÔNICOS", "CABOS")
- `descricao` (TEXT) — Detailed category description
- `ativo` (BOOLEAN, DEFAULT true) — Whether category is currently in use
- `data_criacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Creation timestamp
- `data_atualizacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Last update timestamp
- INDEX on (`ativo`, `nome`) for efficient category lookup
- CONSTRAINT: `nome` must be UNIQUE (prevents duplicate category names)

**2. `regras_de_classificacao` (Classification Rules)**
- `id` (PRIMARY KEY) — Unique rule identifier
- `prioridade` (INTEGER, NOT NULL) — Priority level (higher = more important)
- `nome` (VARCHAR, NOT NULL) — Rule name/description
- `ativo` (BOOLEAN, DEFAULT true) — Active status
- `criterio_palavras_chave` (TEXT) — Comma-separated keywords to match
- `criterio_ncm` (VARCHAR) — NCM pattern (e.g., "8471*" for wildcard)
- `criterio_tamanho_min` (DECIMAL) — Minimum size threshold
- `criterio_tamanho_max` (DECIMAL) — Maximum size threshold
- `criterio_quantidade_min` (INTEGER) — Minimum quantity threshold
- `criterio_quantidade_max` (INTEGER) — Maximum quantity threshold
- `criterio_categoria` (VARCHAR) — Product category filter (if applicable)
- `categoria_id` (INTEGER, NOT NULL, FOREIGN KEY → `categorias`.`id`) — Result category
  - CONSTRAINT: ON DELETE RESTRICT (prevent deleting categories in use)
  - CONSTRAINT: ON UPDATE CASCADE (update references if category ID changes)
- `data_criacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Creation timestamp
- `data_atualizacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Last update timestamp
- INDEX on (`prioridade DESC`, `ativo`) for efficient rule lookup
- INDEX on (`categoria_id`) for queries filtering by result category
- CONSTRAINT: NOT NULL on `prioridade`, `nome`, `categoria_id`

**2. `auditoria_classificacao` (Audit Logs)**
- `id` (PRIMARY KEY) — Unique audit log entry ID
- `id_regra` (FOREIGN KEY → `regras_de_classificacao`.`id`) — Rule that was applied
- `id_produto` (VARCHAR) — Product identifier being classified
- `descricao_produto` (TEXT) — Product description
- `ncm_produto` (VARCHAR) — NCM code of product
- `criterios_combinados` (TEXT) — Which criteria matched (JSON or CSV)
- `resultado_classificacao` (VARCHAR) — Resulting classification
- `data_classificacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — When classified
- `usuario_sistema` (VARCHAR) — System user/process that triggered classification
- INDEX on (`id_produto`, `data_classificacao`) for query performance
- INDEX on (`id_regra`, `data_classificacao`) for audit trail by rule

**3. `criterios_palavras_chave` (Optional - normalized keywords)**
- `id` (PRIMARY KEY) — Keyword entry ID
- `id_regra` (FOREIGN KEY → `regras_de_classificacao`.`id`) — Rule this keyword belongs to
- `palavra_chave` (VARCHAR, NOT NULL) — Individual keyword
- `peso` (DECIMAL, DEFAULT 1.0) — Optional: keyword importance weight
- UNIQUE INDEX on (`id_regra`, `palavra_chave`)

**Migration & Deployment:**
- All schema changes MUST be tracked in a migrations directory
- Migrations MUST be reversible (DOWN procedure required)
- Database MUST be initialized as part of deployment/setup process
- Schema version MUST be queryable (via migration history table or equivalent)

## Governance

**Constitution Authority:**
This constitution supersedes all other development practices and guidelines.
All features, pull requests, and architectural decisions MUST be evaluated
against these principles.

**Amendment Process:**
- Proposed amendments MUST include rationale and impact analysis
- Amendments affecting principles require documentation of how existing code
  achieves compliance
- Version bumping follows semantic versioning: MAJOR for principle removals/
  redefinitions, MINOR for new principles or guidance expansion, PATCH for
  clarifications
- All stakeholders MUST acknowledge amendments before implementation

**Compliance Verification:**
- All PR reviews MUST verify alignment with core principles
- New features MUST be specified, planned, and implemented using SpecKit workflow
- Architecture decisions MUST be justified against simplicity and data-driven
  principles
- Infrastructure setup MUST include valid `.env` file with all required database
  connection variables
- Database schema MUST match the tables and columns defined in this constitution
- All migrations MUST be reversible and tracked in version control
- Use CLAUDE.md for runtime development guidance and implementation patterns

**Version**: 1.2.0 | **Ratified**: 2025-10-25 | **Last Amended**: 2025-10-26
