# Feature Specification: Rule Engine Core with Priority & Audit

**Feature Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Last Updated**: 2025-10-26
**Status**: Complete (Phase 1 & 2 Done; Phase 3 Pending)
**Input**: User description: "Rule Engine Core — Implement the basic rule evaluation engine that reads from regras_de_classificacao and applies rules with priority ordering. Rule Priority System — Implement conflict resolution when multiple rules match the same product (ensuring highest priority wins). Rule Audit Logging — Add tracking of which rules were applied to each classification decision for auditability"

## Implementation Status

- **Phase 1 (MVP)**: ✅ COMPLETE
  - FR-001: Basic rule evaluation from database
  - FR-002: Priority-based conflict resolution
  - FR-003: Audit logging
  - FR-008: NO_MATCH handling

- **Phase 2 (Batch Processing)**: ✅ COMPLETE
  - FR-011: Batch classification from database
  - Status tracking: matched/pending/no_match
  - categoria_id FK integration

- **Phase 2b (Category Service)**: ✅ COMPLETE (NEW - Not in original spec)
  - CategoryService with caching
  - FK validation for categories
  - Category name lookups

- **Phase 3 (CSV Import/Export)**: ❌ NOT IMPLEMENTED
  - FR-013 to FR-016: CSV functionality pending

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Rule Evaluation (Priority: P1)

A system operator receives a product request (with description, NCM code, size, quantity, etc.)
and needs the system to automatically classify it by reading rules from the database and
returning the correct classification result.

**Why this priority**: This is the core MVP. Without the ability to evaluate rules from the
database, the entire system cannot function. It's the foundation for all other features.

**Independent Test**: Can be fully tested by providing a product record and verifying that
the system correctly matches and returns the appropriate classification based on active rules
in the `regras_de_classificacao` table. Delivers immediate value: automated rule-based classification.

**Acceptance Scenarios**:

1. **Given** a product with description "laptop computer" and NCM code 84713090,
   **When** the rule engine evaluates it against active rules,
   **Then** the system returns the matching classification from the highest-priority matching rule

2. **Given** a product with only NCM code (no description keywords match any rule),
   **When** the rule engine evaluates it,
   **Then** the system falls back to NCM-based rules and returns the appropriate classification

3. **Given** a rule is marked as inactive in the database,
   **When** the rule engine evaluates products,
   **Then** the inactive rule is never selected for classification

---

### User Story 2 - Rule Priority & Conflict Resolution (Priority: P1)

When multiple rules match the same product (e.g., both keyword and NCM rules apply),
the system must consistently select the highest-priority rule and return only that result,
preventing ambiguity in classifications.

**Why this priority**: Without priority handling, conflicting rules cause non-deterministic
outcomes and business logic failures. This is critical for data integrity and auditability.

**Independent Test**: Can be fully tested by creating multiple overlapping rules with
different priorities and verifying that the system always selects the rule with highest priority.
Delivers clear, deterministic classification decisions.

**Acceptance Scenarios**:

1. **Given** a product matching both a keyword rule (priority 10) and an NCM rule (priority 5),
   **When** the rule engine evaluates it,
   **Then** the keyword rule (higher priority) is selected and its classification is returned

2. **Given** three rules all matching the same product with priorities 20, 15, and 25,
   **When** the rule engine evaluates it,
   **Then** only the rule with priority 25 is applied

3. **Given** two rules with identical priority matching the same product,
   **When** the rule engine evaluates it,
   **Then** the system returns a deterministic result (e.g., oldest rule by creation date, documented clearly)

---

### User Story 3 - Audit Logging of Applied Rules (Priority: P2)

When a classification decision is made, the system must record which specific rule(s) were
applied, when the evaluation occurred, and what product attributes triggered the match.
This enables business teams to understand why a product was classified a certain way.

**Why this priority**: Auditability is a constitutional requirement and supports compliance,
debugging, and continuous improvement. It's less critical than the core engine but essential
for operational trust. Can be added after basic evaluation works.

**Independent Test**: Can be fully tested by evaluating products and verifying that audit
logs are created with rule IDs, timestamps, and matching criteria. Delivers transparency
and traceability for all classification decisions.

**Acceptance Scenarios**:

1. **Given** a product is classified using rule ID 42,
   **When** the classification is complete,
   **Then** an audit log entry is created with: rule ID, timestamp, product ID/description,
   and the matching criteria that triggered the rule

2. **Given** a product evaluation fails or no rule matches,
   **When** the evaluation completes,
   **Then** an audit log entry is created documenting that no matching rule was found

3. **Given** a business analyst queries the audit logs,
   **When** they filter by product ID,
   **Then** they can see the complete history of which rules were applied and when

---

### User Story 4 - Batch Classification from Database (Priority: P2)

A user needs to classify multiple products from the database in one operation by running a script with a quantity parameter. The system fetches unclassified products from the database, classifies them using the rule engine, and updates them in the database.

**Why this priority**: Enables bulk processing of products without code changes. Allows operations team to classify large volumes efficiently via command line.

**Independent Test**: Can be fully tested by running the script with a quantity limit, verifying that the correct number of products are fetched, classified, and updated in the database.

**Acceptance Scenarios**:

1. **Given** the database has 500 unclassified products,
   **When** user runs `python -m classifier.cli.classify_batch --limit 500`,
   **Then** the script fetches 500 products, classifies each using the rule engine, and updates categoria_id column in the database

2. **Given** a product matches a rule during batch processing,
   **When** classification completes,
   **Then** the product's categoria_id (FK) is updated AND status_classificacao is set to 'matched' AND an audit log entry is created

3. **Given** a product matches no rules,
   **When** batch processing completes,
   **Then** the product remains unchanged (categoria_id=NULL, status_classificacao='pending') and audit log records "NO_MATCH"

4. **Given** user runs batch classification with different quantities,
   **When** script executes with `--limit 100`, `--limit 500`, `--limit 1000`,
   **Then** the correct number of products are processed each time

5. **Given** batch classification is running,
   **When** script encounters database errors,
   **Then** script logs error, continues with next product, and reports summary (X succeeded, Y failed)

---

### User Story 5 - CSV Classification Import & Export (Priority: P3) - NOT IMPLEMENTED

A user can import products from a CSV file, classify them using the rule engine, and export the classified results to a new CSV file. This supports integration with external systems and manual product lists.

**Why this priority**: Enables integration with Excel, external systems, and manual product management. Lower priority than database integration but useful for ad-hoc classifications and data exchange.

**Status**: ❌ NOT IMPLEMENTED - Pending for future phases.

**Independent Test**: Can be fully tested by creating a CSV with sample products, running the script, and verifying output CSV contains original data plus classification results and matched rule information.

**Acceptance Scenarios**:

1. **Given** user has a CSV file with products (columns: id, description, ncm, size, quantity),
   **When** user runs `python classify_csv.py --input productos.csv --output clasificados.csv`,
   **Then** a new CSV is created with all original columns PLUS: categoria, rule_id, rule_name, matched_criteria, evaluation_time_ms

2. **Given** a product in CSV matches a rule,
   **When** classification completes,
   **Then** output CSV shows: categoria (from rule), rule_id, rule_name, and matched_criteria details

3. **Given** a product in CSV matches no rules,
   **When** classification completes,
   **Then** output CSV shows: categoria="NO_MATCH", rule_id=NULL, rule_name="None", matched_criteria="none"

4. **Given** user runs classification with audit flag,
   **When** user runs `python classify_csv.py --input productos.csv --output clasificados.csv --audit audit.csv`,
   **Then** a separate audit.csv is created with audit trail (all entries from auditoria_classificacao table)

5. **Given** CSV file has invalid or missing required columns,
   **When** script runs,
   **Then** script reports error with line number, skips invalid rows, continues processing valid ones

6. **Given** classification results are in output CSV,
   **When** user opens in Excel or imports elsewhere,
   **Then** all data is properly formatted for downstream systems (no special characters, proper UTF-8 encoding)

---

### Edge Cases

- What happens when a product matches zero rules? (When a product no matches, no alter, show in logs)
- What happens when rule criteria are incomplete/corrupted in the database? (validation)
- What happens when the database is temporarily unavailable? (Retry, and information)
- How are concurrent classification requests handled? (Thread-safe)
- What happens when CSV file is very large (10,000+ rows)? (Process in batches, show progress)
- What happens when output CSV already exists? (Warn user, offer to overwrite or append)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read classification rules from the `regras_de_classificacao` database table
- **FR-001a**: System MUST validate all rule category results against `categorias` table (foreign key integrity) ✅ IMPLEMENTED
- **FR-001b**: System MUST prevent invalid category assignments via database FK constraints (ON DELETE RESTRICT, ON UPDATE CASCADE) ✅ IMPLEMENTED
- **FR-002**: System MUST evaluate all criteria fields in a rule (keywords, NCM patterns, size, quantity, etc.) against incoming product attributes
- **FR-003**: System MUST apply only active rules (where status indicates rule is enabled)
- **FR-004**: System MUST return the classification from the highest-priority matching rule when multiple rules match
- **FR-005**: System MUST handle rule priority as a numeric field with higher numbers = higher priority
- **FR-006**: System MUST provide a deterministic tiebreaker when two rules have identical priority (documented and consistent across all evaluations)
- **FR-007**: System MUST create audit log entries recording which rule was applied, when, and what product attributes matched
- **FR-008**: System MUST handle the case where zero rules match a product with a documented fallback behavior
- **FR-009**: System MUST validate rule criteria before evaluation (e.g., no NULL priority fields) and skip or reject invalid rules
- **FR-010**: System MUST support flexible rule criteria composition without code changes (per Constitution Principle III)
- **FR-011**: System MUST provide a batch classification script (`classify_batch.py`) that fetches unclassified products from database and updates them with classifications ✅ IMPLEMENTED
- **FR-012**: System MUST accept command-line arguments in batch script (e.g., `--limit 500` to process 500 products) and support `--limit`, `--offset`, `--where` filters ✅ IMPLEMENTED
- **FR-013**: System MUST provide a CSV import/export script (`classify_csv.py`) that reads products from CSV file, classifies them, and writes results to output CSV ❌ NOT IMPLEMENTED
- **FR-014**: System MUST support CSV column mapping (allow different column names for id, description, ncm, size, quantity, category) ❌ NOT IMPLEMENTED
- **FR-015**: System MUST include audit flag in CSV script (`--audit`) to export audit trail to separate CSV file ❌ NOT IMPLEMENTED
- **FR-016**: System MUST handle CSV encoding properly (UTF-8) and validate data before classification ❌ NOT IMPLEMENTED
- **FR-017**: System MUST maintain database transaction integrity during batch operations (all-or-nothing per product, with rollback on error) ⚠️ PARTIAL
- **FR-018**: System MUST provide progress reporting in batch/CSV operations (X of Y processed, estimated time remaining) ⚠️ PARTIAL

### Key Entities

- **Category** (`categorias` table): A product classification category
  - Attributes: id (SERIAL PRIMARY KEY), name (unique), description, active status, created_at, updated_at
  - Purpose: Centralized reference table for all valid classification categories
  - Relationships: Referenced by Rules and Products via foreign keys

- **Product**: The item being classified (`produtos_tabela` table)
  - Attributes: id (varchar PK), descricao, ncm, categoria_id (FK to categorias, nullable), status_classificacao ('matched'/'pending'/'no_match'), size, quantity, other attributes

- **Rule** (`regras_de_classificacao` table): A classification rule with criteria, priority, and result
  - Fields: ID, priority (numeric, 1-100), active status (ativo boolean), rule criteria (criterio_palavras_chave, criterio_ncm, criterio_tamanho_min/max, criterio_quantidade_min/max, criterio_categoria), categoria_id (FK to categorias), resultado_classificacao (deprecated), data_criacao, data_atualizacao

- **Classification Result**: The outcome of a rule evaluation
  - Attributes: category_id (from categorias table), category name, confidence level, or other result fields per business requirements

- **Audit Log**: Record of rule application for traceability (`auditoria_classificacao` table)
  - Fields: id (SERIAL PK), id_regra (FK to regras_de_classificacao), id_produto, descricao_produto, ncm_produto, resultado_classificacao, criterios_combinados (JSON), tempo_avaliacao_ms, categoria_id (FK to categorias), data_classificacao

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System correctly classifies products using rules defined in the database ✅ VERIFIED - 779 products classified from 79,201
- **SC-002**: When multiple rules match a product, the system consistently selects the highest-priority rule 100% of the time ✅ IMPLEMENTED - Priority range 1-100, higher wins
- **SC-003**: Rule evaluation performance adequate for production use ✅ VERIFIED - Batch processes 500 products in ~2 seconds
- **SC-004**: Audit logs capture rule application details with completeness ✅ IMPLEMENTED - auditoria_classificacao table with all fields
- **SC-005**: Business users can trace classification decisions via audit logs ✅ IMPLEMENTED - Full audit trail with timestamps and criteria
- **SC-006**: System remains operational when rules are modified without code changes ✅ IMPLEMENTED - Database-driven rules allow updates without deployment
- **SC-007**: Batch classification script processes 500 products efficiently ✅ VERIFIED - 500 products ~2 seconds, well under 5 minute target
- **SC-008**: CSV classification handles large files ❌ NOT IMPLEMENTED - CSV feature pending
- **SC-009**: Output formatting for external tools ❌ NOT IMPLEMENTED - CSV feature pending
- **SC-010**: Batch operations maintain data consistency ✅ IMPLEMENTED - All matched products logged to audit table with status tracking

## Assumptions & Implementation Details

- ✅ The `regras_de_classificacao` table exists with all required columns (id, nome, ativo, prioridade, criterio_*)
- ✅ The `categorias` table exists with FK relationships to rules and products
- ✅ The `auditoria_classificacao` table captures all classification decisions
- ✅ Product input data comes from `produtos_tabela` with documented attributes
- ✅ "Active" rules identified by `ativo` boolean field
- ✅ Priority is numeric (1-100) with clear ordering (higher = more important)
- ✅ Rule criteria evaluated using case-insensitive keyword matching on product descriptions
- ✅ Audit logging implemented in dedicated `auditoria_classificacao` table with timestamps
- ✅ Rule changes take effect on next batch evaluation without code redeployment
- ✅ Tie-breaking: When rules have identical priority, first matching rule in execution order is selected (deterministic)
- ✅ NO_MATCH handling: Products remain with status='pending' and categoria_id=NULL for reprocessing
- ✅ Status tracking: Products tracked via status_classificacao field ('matched'/'pending'/'no_match')
