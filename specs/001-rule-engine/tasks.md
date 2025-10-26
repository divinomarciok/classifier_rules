---

description: "Task list for Rule Engine Core implementation"
---

# Tasks: Rule Engine Core with Priority & Audit

**Input**: Design documents from `/specs/001-rule-engine/`
**Prerequisites**: plan.md (complete), spec.md (complete), data-model.md (complete), contracts/ (complete), research.md (complete)

**Tests**: TDD approach — Test-first strategy is REQUIRED (per Constitutional Principle IV). Write tests FIRST, ensure they FAIL, then implement.

**Organization**: Tasks are grouped by user story (US1-US5) to enable independent implementation and testing of each story. Each user story can be developed independently and deployed as an increment. US1-US3 are core engine; US4-US5 are CLI/batch processing scripts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below use repository root structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `src/classifier/`, `tests/`, `migrations/`, `docs/`
- [ ] T002 Initialize Python project with setup.py and requirements.txt for psycopg2, pytest
- [ ] T003 [P] Create `.env.example` with DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT placeholders
- [ ] T004 [P] Create `.gitignore` to exclude `.env`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`
- [ ] T005 [P] Create `README.md` with project overview, installation, and quick start references

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Infrastructure & Database Setup (REQUIRED)

- [ ] T006 Create `.env` file by copying `.env.example` and updating with test database credentials (DB_HOST=localhost, DB_NAME=market_v1, DB_USER=user, DB_PASSWORD=password, DB_PORT=5432)
- [ ] T007 [P] Create database migration framework tracking file: `migrations/migrations_history.sql`
- [ ] T008 Create database schema migration: `migrations/002_create_categorias.sql` (MUST RUN FIRST)
  - Table: `categorias` with 5 columns (id SERIAL PRIMARY KEY, nome VARCHAR UNIQUE NOT NULL, descricao TEXT, ativo BOOLEAN DEFAULT TRUE, data_criacao TIMESTAMP, data_atualizacao TIMESTAMP)
  - UNIQUE INDEX on `nome` (prevents duplicate category names)
  - COMPOSITE INDEX on (ativo, nome) for efficient lookups
  - Use CREATE TABLE IF NOT EXISTS for idempotency
  - Seed base categories: ELETRÔNICOS, CABOS, ACESSÓRIOS, PERIFÉRICOS, COMPONENTES (via migration INSERT)
  - Include validation constraints (NOT NULL on nome)
- [ ] T009 Create database schema migration: `migrations/003_create_regras_de_classificacao.sql` (DEPENDS ON T008)
  - Table: `regras_de_classificacao` with updated columns (id, prioridade, nome, ativo, criterio_palavras_chave, criterio_ncm, criterio_tamanho_min, criterio_tamanho_max, criterio_quantidade_min, criterio_quantidade_max, criterio_categoria, categoria_id, data_criacao, data_atualizacao)
  - PRIMARY KEY on `id`, COMPOSITE INDEX on (prioridade DESC, ativo), SIMPLE INDEX on categoria_id
  - Foreign Key: `categoria_id` references `categorias(id)` with ON DELETE RESTRICT, ON UPDATE CASCADE
  - Use CREATE TABLE IF NOT EXISTS for idempotency
  - Include validation constraints (NOT NULL on prioridade, nome, categoria_id)
- [ ] T010 Create database schema migration: `migrations/004_create_auditoria_classificacao.sql` (DEPENDS ON T009)
  - Table: `auditoria_classificacao` with 10 columns (id, id_regra, id_produto, descricao_produto, ncm_produto, criterios_combinados, resultado_classificacao, data_classificacao, usuario_sistema, tempo_avaliacao_ms)
  - PRIMARY KEY on `id`, FOREIGN KEY on `id_regra` referencing regras_de_classificacao(id)
  - COMPOSITE INDEX on (id_produto, data_classificacao), COMPOSITE INDEX on (id_regra, data_classificacao), SIMPLE INDEX on data_classificacao
  - Use CREATE TABLE IF NOT EXISTS for idempotency
  - Include constraint: resultado_classificacao NOT NULL
- [ ] T011 Create database schema migration: `migrations/005_create_criterios_palavras_chave.sql` (optional table for normalized keywords)
  - Table: `criterios_palavras_chave` with 5 columns (id, id_regra, palavra_chave, peso, data_criacao)
  - PRIMARY KEY on `id`, FOREIGN KEY on `id_regra`, UNIQUE INDEX on (id_regra, palavra_chave)
  - Use CREATE TABLE IF NOT EXISTS for idempotency
- [ ] T012 Create idempotent database initialization script: `src/classifier/init_db.py`
  - Function: `init_database()` that executes all migration SQL files in order (002, 003, 004, 005...)
  - Reads .env for connection parameters
  - Rolls back and reports if any migration fails
  - Returns success/failure status
  - Special handling: Ensure T008 (categorias) runs BEFORE T009 (regras_de_classificacao)
- [ ] T013 Add rollback procedures file: `migrations/ROLLBACK.md`
  - Document DROP TABLE statements for each migration (in reverse order)
  - Include instructions for safe rollback
  - Note: Must drop regras_de_classificacao BEFORE categorias (FK dependency)

### Application Infrastructure

- [ ] T014 [P] Create application configuration module: `src/classifier/utils.py`
  - Function: `load_config()` reads from `.env` file and returns DB connection params
  - Function: `get_db_connection()` creates psycopg2 connection using config
  - Raises `ConfigError` if .env missing or invalid
  - Raises `DatabaseError` if connection fails
- [ ] T015 [P] Create exception classes module: `src/classifier/__init__.py`
  - Classes: `ConfigError`, `DatabaseError`, `ProductError`, `EvaluationError`
  - Each with clear error messages and inheritance from Exception
- [ ] T016 [P] Create `tests/conftest.py` with pytest fixtures
  - Fixture: `db_connection` — creates test database connection from .env
  - Fixture: `sample_categories` — inserts 5 test categories (MUST RUN FIRST)
  - Fixture: `sample_rules` — inserts 5 test rules into test database (depends on sample_categories)
  - Fixture: `cleanup` — truncates audit log, rules, and categories tables after each test (order: rules→categories)
  - Include: `@pytest.fixture(scope="function")`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Rule Evaluation (Priority: P1) 🎯 MVP

**Goal**: Implement core rule evaluation engine that reads rules from database and returns correct classification

**Independent Test**: Can be fully tested by providing a product record and verifying correct classification is returned based on active rules. Delivers immediate value: automated rule-based classification.

### Contract Tests for User Story 1 (Test-First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Contract test for RuleEngine.evaluate() in `tests/contract/test_rule_engine_api.py`
  - Test: `test_evaluate_with_keyword_match()` — Product with "laptop computer" description should match keyword rule and return ELECTRONICS
  - Test: `test_evaluate_with_ncm_match()` — Product with NCM 8471* should match NCM rule
  - Test: `test_evaluate_inactive_rule_ignored()` — Product should not match inactive rule
  - Test: `test_evaluate_returns_result_dict()` — Result contains keys: classification, rule_id, rule_name, matched_criteria, evaluation_time_ms, success
  - Use fixtures from conftest.py
- [ ] T019 [P] [US1] Integration test for rule evaluation flow in `tests/integration/test_rule_evaluation.py`
  - Test: `test_end_to_end_classification()` — Full flow: load rules → evaluate product → get result
  - Test: `test_evaluation_with_multiple_rules()` — Ensure only matching rules are evaluated
  - Test: `test_evaluation_performance()` — Evaluation completes in < 500ms for 100 rules
  - Include real database and cleanup

### Models for User Story 1

- [ ] T019 [P] [US1] Create Rule model in `src/classifier/models.py`
  - Class: `Rule` with attributes: id, prioridade, nome, ativo, criterio_*, resultado_classificacao, data_criacao, data_atualizacao
  - Method: `from_db_row(row)` — construct Rule from database tuple
  - Method: `is_active()` — returns True if ativo = TRUE
  - Method: `__repr__()` — for debugging

- [ ] T020 [P] [US1] Create Product model in `src/classifier/models.py`
  - Class: `Product` with attributes: id (optional), description, ncm, size (optional), quantity (optional), category (optional), other_fields (dict)
  - Method: `__init__()` with flexible keyword arguments
  - Method: `get_field(field_name)` — safely access any product attribute
  - Method: `__repr__()` — for debugging

### Services for User Story 1

- [ ] T021 [US1] Create Matcher service in `src/classifier/matcher.py`
  - Class: `Matcher` with method `matches_all_criteria(product, rule)`
  - Logic: Keyword matching (substring, case-insensitive), NCM matching (wildcard support with *), size range matching, quantity range matching, category exact matching
  - Return: True if ALL specified criteria in rule match product, False otherwise
  - Sub-methods: `_match_keywords()`, `_match_ncm()`, `_match_size()`, `_match_quantity()`, `_match_category()`
  - Handle NULL/None criteria gracefully (skip if not specified)

- [ ] T022 [US1] Create RuleEvaluator service in `src/classifier/evaluator.py`
  - Class: `Evaluator` with method `get_matching_rules(product, rules)`
  - Logic: Use Matcher to filter rules that match product
  - Return: List of matching Rule objects (or empty list if none match)
  - Handle errors gracefully (log, raise EvaluationError if needed)

### Core Engine for User Story 1

- [ ] T023 [US1] Create RuleEngine class in `src/classifier/engine.py`
  - Class: `RuleEngine` with constructor `__init__(db_connection=None, cache_rules=True)`
  - Method: `_load_rules()` — fetch active rules from regras_de_classificacao table
  - Method: `_initialize_cache()` — load rules into memory if caching enabled
  - Method: `get_rules(active_only=True)` — return list of all rules (optionally only active)
  - Method: `refresh_cache()` — reload rules from database
  - Method: `evaluate(product_data, user=None)` — CORE METHOD
    - Input: product_data (dict), user (str, optional)
    - Use Evaluator.get_matching_rules() to find matches
    - Measure evaluation time with timer
    - Return dict with: classification, rule_id, rule_name, priority, matched_criteria, evaluation_time_ms, success, message
    - Handle no-match case gracefully (classification = "NO_MATCH", rule_id = None)
    - Raise ProductError if product data invalid
    - Raise DatabaseError if rule fetch fails
  - Include connection initialization with load_config()

### Integration for User Story 1

- [ ] T024 [US1] Integrate Matcher, Evaluator, and RuleEngine in `src/classifier/engine.py`
  - Complete evaluate() method to call: get_rules() → Evaluator → Matcher → return result
  - Add error handling with try-catch for all exceptions
  - Add debug logging for rule matching process
- [ ] T025 [US1] Create unit tests for Matcher in `tests/unit/test_matcher.py`
  - Test: `test_match_keywords_substring()` — "laptop" matches "laptop computer"
  - Test: `test_match_keywords_case_insensitive()` — "LAPTOP" matches "laptop computer"
  - Test: `test_match_ncm_wildcard()` — "8471*" matches "84713090"
  - Test: `test_match_size_range()` — Range [1.0, 10.0] matches size=5.0 but not size=0.5
  - Test: `test_match_all_criteria_require_true()` — False if ANY criterion is false
  - Run AFTER T021 implementation

- [ ] T026 [US1] Create unit tests for RuleEvaluator in `tests/unit/test_evaluator.py`
  - Test: `test_get_matching_rules_filters_correctly()` — Only returns rules that Matcher confirms
  - Test: `test_get_matching_rules_empty_list()` — Returns empty list if no matches
  - Run AFTER T022 implementation

- [ ] T027 [US1] Create unit tests for RuleEngine in `tests/unit/test_rule_engine.py`
  - Test: `test_evaluate_returns_dict_with_required_keys()` — Result has all expected keys
  - Test: `test_evaluate_with_valid_product()` — Evaluation succeeds
  - Test: `test_evaluate_with_invalid_product()` — Raises ProductError
  - Test: `test_evaluate_handles_no_match()` — Returns NO_MATCH when appropriate
  - Run AFTER T023 implementation

- [ ] T028 [US1] Create unit tests for Rule and Product models in `tests/unit/test_models.py`
  - Test: `test_rule_from_db_row()` — Correctly construct Rule from database tuple
  - Test: `test_product_init_with_kwargs()` — Flexible initialization
  - Test: `test_product_get_field_optional()` — Safe field access
  - Run AFTER T019, T020 implementation

**Checkpoint**: User Story 1 complete and independently testable

---

## Phase 4: User Story 2 - Rule Priority & Conflict Resolution (Priority: P1)

**Goal**: When multiple rules match, consistently select highest-priority rule; handle tiebreaks deterministically

**Independent Test**: Can be tested by creating multiple overlapping rules with different priorities and verifying highest-priority rule always wins across 1000+ test scenarios.

### Contract Tests for User Story 2 (Test-First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Contract test for priority resolution in `tests/contract/test_priority_resolution.py`
  - Test: `test_highest_priority_wins()` — 3 matching rules with priorities 10, 20, 25 → rule 25 returned
  - Test: `test_identical_priority_tiebreak()` — 2 rules, same priority → older by creation date returned
  - Test: `test_priority_override_lower()` — Lower priority rule never selected if higher priority matches
  - Test: `test_priority_consistency()` — Same product evaluated 100 times → always same rule selected
  - Use sample_rules fixture with multiple overlapping rules

- [ ] T030 [P] [US2] Integration test for conflict resolution in `tests/integration/test_priority_resolution.py`
  - Test: `test_multiple_matching_rules_resolution()` — Full workflow with multiple matches
  - Test: `test_priority_with_different_criteria()` — Priority works across keyword, NCM, and range criteria
  - Test: `test_complex_scenario()` — 5+ rules, multiple matches, correct winner selected
  - Include performance validation: resolution completes in < 100ms

### Services for User Story 2

- [ ] T031 [US2] Create Selector/Resolver service in `src/classifier/evaluator.py`
  - Method: `select_winner(matching_rules)` in existing Evaluator class
  - Logic: Sort by prioridade DESC, then by data_criacao ASC (FIFO tiebreak)
  - Return: Single Rule object with highest priority (oldest if tied)
  - Document tiebreak behavior clearly in docstring
  - Handle empty list (raise EvaluationError)

### Core Engine Update for User Story 2

- [ ] T032 [US2] Update RuleEngine.evaluate() to use priority resolution in `src/classifier/engine.py`
  - Replace: "Return first matching rule" with "Get all matching rules, select winner"
  - Call: `Evaluator.select_winner(matching_rules)` after matching
  - Update return dict with: winner rule details
  - Ensure evaluation time includes selection logic
  - Add debug logging: "Matched N rules, selected rule_id=X with priority=Y"

### Testing for User Story 2

- [ ] T033 [US2] Add unit tests for priority selector in `tests/unit/test_evaluator.py`
  - Test: `test_select_winner_highest_priority()` — Correct rule selected from unsorted list
  - Test: `test_select_winner_tiebreak_fifo()` — Older rule wins when priorities identical
  - Test: `test_select_winner_empty_list()` — Raises error on empty input
  - Run AFTER T031 implementation

- [ ] T034 [US2] Add integration tests for full priority workflow in `tests/integration/test_priority_resolution.py`
  - Test: `test_full_workflow_with_priority()` — Load rules → match → select winner → return
  - Test: `test_consistency_across_evaluations()` — Same product, 100 evaluations → always same rule
  - Run AFTER T032 implementation

**Checkpoint**: User Stories 1 AND 2 both complete and independently testable. Priority resolution working correctly.

---

## Phase 5: User Story 3 - Audit Logging of Applied Rules (Priority: P2)

**Goal**: Record every classification decision with rule applied, timestamp, and matched criteria for full traceability

**Independent Test**: Can be tested by evaluating products and querying audit logs to verify every decision is logged with complete details.

### Contract Tests for User Story 3 (Test-First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T035 [P] [US3] Contract test for audit logging in `tests/contract/test_audit_logging.py`
  - Test: `test_audit_log_created_for_match()` — Classification creates audit entry with rule_id, timestamp
  - Test: `test_audit_log_created_for_no_match()` — NO_MATCH classifications also logged with id_regra=NULL
  - Test: `test_audit_log_contains_product_details()` — Log includes product id, description, ncm
  - Test: `test_audit_log_contains_matched_criteria()` — Log includes which criteria matched
  - Test: `test_audit_log_contains_result()` — Log includes resultado_classificacao
  - Test: `test_audit_log_contains_timestamp()` — Log has data_classificacao timestamp
  - Test: `test_audit_log_includes_evaluation_time()` — Log has tempo_avaliacao_ms
  - Use fixtures and database connection

- [ ] T036 [P] [US3] Integration test for audit trail queries in `tests/integration/test_audit_logging.py`
  - Test: `test_query_audit_by_product()` — Retrieve all classifications for a product
  - Test: `test_query_audit_by_rule()` — Retrieve all classifications using a rule
  - Test: `test_audit_completeness()` — Every evaluate() call creates exactly one log entry
  - Test: `test_audit_immutability()` — Can't update/delete audit logs
  - Include sorting and filtering by timestamp

### Audit Service for User Story 3

- [ ] T037 [US3] Create AuditLog service in `src/classifier/audit.py`
  - Class: `AuditLog` with constructor that takes db_connection
  - Method: `record(rule_id, product_data, matched_criteria, classification_result, evaluation_time_ms, user)`
    - Input: rule_id (int or None), product_data (dict), matched_criteria (list), classification_result (str), evaluation_time_ms (int), user (str)
    - Extract from product_data: id, description, ncm
    - Format matched_criteria as JSON string for storage
    - Execute INSERT into auditoria_classificacao
    - Return: entry ID
    - Raise DatabaseError if insert fails
  - Method: `get_product_history(product_id, limit=100)`
    - Query: SELECT from auditoria_classificacao WHERE id_produto = ? ORDER BY data_classificacao DESC LIMIT ?
    - Return: List of dicts with audit entry details
  - Method: `get_rule_statistics(rule_id)`
    - Query: Aggregate stats for a rule (times applied, last applied, avg/min/max evaluation_time_ms)
    - Return: Dict with statistics

### Core Engine Update for User Story 3

- [ ] T038 [US3] Update RuleEngine.evaluate() to log decisions in `src/classifier/engine.py`
  - Import: `from classifier.audit import AuditLog`
  - After evaluation completes:
    - Call: `AuditLog(self.connection).record(winner_rule_id, product, matched_criteria, classification, eval_time, user)`
    - Handle DatabaseError gracefully (log warning, don't block result)
  - Include matched_criteria as formatted list/JSON
  - Pass user parameter through (default: "system")

### Testing for User Story 3

- [ ] T039 [US3] Create unit tests for AuditLog in `tests/unit/test_audit.py`
  - Test: `test_record_inserts_correctly()` — Record method inserts and returns ID
  - Test: `test_record_with_null_rule_id()` — No-match case handled (rule_id = NULL)
  - Test: `test_get_product_history_returns_sorted()` — Results ordered by timestamp DESC
  - Test: `test_get_rule_statistics_calculates_correctly()` — Stats aggregation works
  - Run AFTER T037 implementation

- [ ] T040 [US3] Create integration tests for audit workflow in `tests/integration/test_audit_logging.py`
  - Test: `test_full_workflow_logs_decision()` — evaluate() → audit entry created
  - Test: `test_multiple_evaluations_all_logged()` — 100 evaluations → 100 audit entries
  - Test: `test_audit_queryable_after_classification()` — Log queryable immediately after creation
  - Run AFTER T038 implementation

- [ ] T041 [US3] Add audit logging to existing RuleEngine tests (update `tests/integration/test_rule_evaluation.py`)
  - Add: Query audit logs to verify each evaluation was recorded
  - Add: Verify matched_criteria populated correctly for different rule types
  - Run AFTER T038, T039 implementation

**Checkpoint**: All three user stories complete and independently testable. Full classification workflow with priority resolution and audit logging working.

---

## Phase 6: User Story 4 - Batch Classification from Database (Priority: P2)

**Goal**: Enable operators to classify multiple unclassified products from the database using a command-line script with quantity parameter

**Independent Test**: Can be tested by running the script with various limits and verifying correct number of products are fetched, classified, and updated in the database.

### Contract Tests for User Story 4 (Test-First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T055 [P] [US4] Contract test for batch classification in `tests/contract/test_batch_classification.py`
  - Test: `test_batch_classify_with_limit()` — Running with `-500` fetches and processes exactly 500 products
  - Test: `test_batch_classify_with_offset()` — Running with `--offset 100` starts from correct position
  - Test: `test_batch_classify_updates_database()` — Products categoria field updated in database
  - Test: `test_batch_classify_creates_audit_logs()` — Each classification creates audit entry
  - Test: `test_batch_classify_handles_no_match()` — Products with no matching rules are still logged
  - Test: `test_batch_classify_with_custom_where()` — Custom `--where` filter works correctly
  - Use fixtures and database connection

- [ ] T056 [P] [US4] Integration test for batch workflow in `tests/integration/test_batch_classification.py`
  - Test: `test_end_to_end_batch_workflow()` — Full workflow: fetch unclassified → classify all → update DB → audit logged
  - Test: `test_batch_performance()` — 500 products complete in under 5 minutes (SC-007)
  - Test: `test_batch_error_handling()` — Database errors logged, processing continues
  - Test: `test_batch_progress_reporting()` — Progress output shows X of Y processed
  - Include real database and cleanup

### CLI Service for User Story 4

- [ ] T057 [US4] Create BatchClassifier service in `src/classifier/cli/batch_classifier.py`
  - Class: `BatchClassifier` with constructor taking db_connection and rule_engine
  - Method: `classify_batch(limit, offset=0, where_clause=None, user="system")`
    - Input: limit (int), offset (int), where_clause (str or None), user (str)
    - Logic:
      1. Build SQL query to fetch unclassified products (WHERE categoria IS NULL) with optional custom filter
      2. Apply LIMIT and OFFSET
      3. For each product: classify using RuleEngine, capture result
      4. Update produto.categoria with classification result
      5. Record audit log entry via AuditLog
      6. Report progress: "X of Y classified, estimated time remaining: Z minutes"
    - Return: Dict with summary {total_fetched, total_classified, total_no_match, errors_count, elapsed_time_ms}
    - Raise DatabaseError if fetch/update fails
  - Method: `_get_unclassified_products(limit, offset, where_clause)` — private helper
  - Method: `_update_product_category(product_id, categoria)` — private helper
  - Include: Progress callback for CLI output

### CLI Script for User Story 4

- [ ] T058 [US4] Create CLI entry point in `src/classifier/cli/classify_batch.py`
  - Script: Command-line interface for batch classification
  - Arguments:
    - `limit` (positional, required): Number of products to classify (e.g., `-500`)
    - `--offset` (optional, default 0): Starting position
    - `--where` (optional): Custom SQL WHERE clause filter
    - `--user` (optional, default "system"): User running the batch
  - Logic:
    1. Load config and create database connection
    2. Create RuleEngine instance
    3. Create BatchClassifier instance
    4. Call classify_batch() with parameters
    5. Display progress/results
  - Error handling: Catch and display errors, exit with appropriate code
  - Usage examples in docstring:
    ```bash
    python classify_batch.py -500              # Classify 500 products
    python classify_batch.py -1000 --offset 100 # Skip first 100, classify next 1000
    python classify_batch.py -500 --where "size < 10"  # Custom filter
    ```

### Testing for User Story 4

- [ ] T059 [US4] Create unit tests for BatchClassifier in `tests/unit/test_batch_classifier.py`
  - Test: `test_build_query_with_limit()` — SQL query includes LIMIT correctly
  - Test: `test_build_query_with_offset()` — SQL query includes OFFSET correctly
  - Test: `test_build_query_with_custom_where()` — WHERE clause added correctly
  - Test: `test_update_product_category()` — UPDATE statement works
  - Test: `test_progress_calculation()` — Progress reporting accurate
  - Run AFTER T057 implementation

- [ ] T060 [US4] Create integration tests for CLI workflow in `tests/integration/test_batch_classification.py`
  - Test: `test_full_batch_workflow()` — Script runs, fetches, classifies, updates, logs
  - Test: `test_batch_with_real_database()` — Works with actual test database
  - Test: `test_performance_target_met()` — Meets SC-007 (500 products < 5 minutes)
  - Run AFTER T058 implementation

**Checkpoint**: User Story 4 complete. Batch classification working end-to-end.

---

## Phase 7: User Story 5 - CSV Classification Import & Export (Priority: P3)

**Goal**: Enable flexible classification of products from CSV files for ad-hoc analysis, Excel integration, and external workflows

**Independent Test**: Can be tested by creating CSV with sample products, running the script, and verifying output CSV contains original data plus classification results and audit information.

### Contract Tests for User Story 5 (Test-First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T061 [P] [US5] Contract test for CSV classification in `tests/contract/test_csv_classification.py`
  - Test: `test_csv_read_and_classify()` — CSV input → classified output CSV created
  - Test: `test_csv_output_contains_classification_columns()` — Output has categoria, rule_id, rule_name, matched_criteria, evaluation_time_ms
  - Test: `test_csv_column_mapping()` — Custom column names supported (--product-id, --description, --ncm)
  - Test: `test_csv_with_no_match()` — Products with no rule match show categoria="NO_MATCH", rule_id=NULL
  - Test: `test_csv_with_audit_flag()` — `--audit` flag creates separate audit.csv
  - Test: `test_csv_with_update_db()` — `--update-db` flag also updates database
  - Test: `test_csv_with_invalid_rows()` — Invalid rows skipped, valid ones processed, report generated
  - Use sample CSV files and check output

- [ ] T062 [P] [US5] Integration test for CSV workflow in `tests/integration/test_csv_classification.py`
  - Test: `test_end_to_end_csv_workflow()` — Full workflow: read CSV → classify all → write output → audit
  - Test: `test_csv_performance()` — 50,000 rows complete in under 10 minutes (SC-008)
  - Test: `test_csv_output_excel_compatible()` — Output CSV openable in Excel, no encoding issues
  - Test: `test_csv_error_handling()` — Errors logged, processing continues
  - Test: `test_csv_with_all_options()` — Custom columns + audit + update-db all work together
  - Include real CSV files and cleanup

### CSV Service for User Story 5

- [ ] T063 [US5] Create CSVClassifier service in `src/classifier/cli/csv_classifier.py`
  - Class: `CSVClassifier` with constructor taking db_connection, rule_engine, and audit_log
  - Method: `classify_csv(input_file, output_file, column_mapping=None, audit_file=None, update_db=False, user="system")`
    - Input: input_file (path), output_file (path), column_mapping (dict), audit_file (path or None), update_db (bool), user (str)
    - Logic:
      1. Read input CSV with provided column mapping (default: id, description, ncm, size, quantity)
      2. For each row:
         - Validate required fields present
         - Classify using RuleEngine
         - Capture: categoria, rule_id, rule_name, matched_criteria, evaluation_time_ms
         - If update_db: call BatchClassifier to update database
         - Add to audit logs list
      3. Write output CSV with original columns + classification metadata
      4. If audit_file specified: write separate audit CSV
      5. Report progress: "X of Y processed, estimated time remaining: Z minutes"
    - Return: Dict with summary {total_rows, total_classified, total_no_match, total_errors, elapsed_time_ms}
    - Raise IOError if file operations fail, ProcessingError if classification fails
  - Method: `_read_csv(input_file, column_mapping)` — private helper, returns list of dicts
  - Method: `_validate_row(row, required_fields)` — private helper, validates data
  - Method: `_write_csv(output_file, rows, extra_columns)` — private helper, writes CSV with all columns
  - Method: `_write_audit_csv(audit_file, audit_entries)` — private helper, writes audit log entries
  - Include: Progress callback for CLI output, error collection (report all errors at end)

### CLI Script for User Story 5

- [ ] T064 [US5] Create CLI entry point in `src/classifier/cli/classify_csv.py`
  - Script: Command-line interface for CSV classification
  - Arguments:
    - `--input` (required): Path to input CSV file
    - `--output` (required): Path to output CSV file
    - `--product-id` (optional, default "id"): Column name for product ID
    - `--description` (optional, default "description"): Column name for description
    - `--ncm` (optional, default "ncm"): Column name for NCM code
    - `--size` (optional, default "size"): Column name for size
    - `--quantity` (optional, default "quantity"): Column name for quantity
    - `--audit` (optional): Path to audit CSV file (if provided, creates separate audit file)
    - `--update-db` (optional flag): Also update database with classifications
    - `--user` (optional, default "system"): User running the classification
  - Logic:
    1. Validate input file exists and is readable
    2. Load config and create database connection
    3. Create RuleEngine instance
    4. Create CSVClassifier instance
    5. Call classify_csv() with parameters
    6. Display progress and summary
  - Error handling: Catch and display errors, exit with appropriate code
  - Usage examples in docstring:
    ```bash
    python classify_csv.py --input productos.csv --output result.csv
    python classify_csv.py --input in.csv --output out.csv --product-id id_col --description desc_col
    python classify_csv.py --input in.csv --output out.csv --audit audit.csv
    python classify_csv.py --input in.csv --output out.csv --update-db
    ```

### Export Service for User Story 5 (Optional)

- [ ] T065 [US5] Create ExportClassifier service in `src/classifier/cli/export_batch.py` (optional)
  - Class: `ExportClassifier` with constructor taking db_connection
  - Method: `export_classified_products(output_file, where_clause=None)`
    - Input: output_file (path), where_clause (str or None)
    - Logic: Query database for classified products (WHERE categoria IS NOT NULL), write to CSV
    - Return: Dict with summary {total_exported, elapsed_time_ms}
  - Purpose: Export previously classified products from database to CSV for backup/sharing

### Testing for User Story 5

- [ ] T066 [US5] Create unit tests for CSVClassifier in `tests/unit/test_csv_classifier.py`
  - Test: `test_read_csv_with_default_columns()` — Reads CSV correctly
  - Test: `test_read_csv_with_custom_mapping()` — Custom column names work
  - Test: `test_validate_row_missing_required()` — Validation detects missing fields
  - Test: `test_classify_row_and_capture_all_fields()` — Result dict has all fields
  - Test: `test_write_csv_with_extra_columns()` — Output includes all original + classification columns
  - Test: `test_progress_calculation()` — Progress reporting accurate for large files
  - Run AFTER T063 implementation

- [ ] T067 [US5] Create integration tests for CSV CLI workflow in `tests/integration/test_csv_classification.py`
  - Test: `test_full_csv_workflow()` — Script runs, reads CSV, classifies, writes output
  - Test: `test_csv_with_real_database()` — Works with actual test database
  - Test: `test_performance_target_met()` — Meets SC-008 (50k rows < 10 minutes)
  - Test: `test_csv_output_format()` — Output CSV matches expected format
  - Run AFTER T064 implementation

- [ ] T068 [US5] Create sample CSV files for testing in `input/` directory
  - File: `input/sample_productos.csv` with 10 test products (id, description, ncm, size, quantity)
  - File: `input/large_sample.csv` with 1000+ products for performance testing
  - Include: Products that should match various rule types (keyword, NCM, range)

**Checkpoint**: User Story 5 complete. CSV import/export working end-to-end with all options.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, documentation, and production readiness

- [ ] T042 [P] Create comprehensive API documentation in `docs/api.md`
  - Document RuleEngine.evaluate() with parameters, returns, exceptions, examples
  - Document Matcher, Evaluator, AuditLog public methods
  - Include: error handling patterns, retry strategies, performance considerations
  - Link to: `specs/001-rule-engine/contracts/rule_engine_api.md`

- [ ] T043 [P] Create user guide for business users in `docs/rules_guide.md`
  - Section: "How to Create a Rule" with SQL examples
  - Section: "Rule Priority Explanation" with examples
  - Section: "Debugging Classifications" using audit logs
  - Section: "Best Practices" for rule design
  - Examples: 5+ real-world rule scenarios

- [ ] T044 [P] Create troubleshooting guide in `docs/troubleshooting.md`
  - Common errors and solutions: Database connection, invalid product, no rules match
  - Performance troubleshooting: Slow evaluations, query optimization
  - Audit log analysis: Finding no-match cases, rule performance

- [ ] T045 Add logging throughout application in `src/classifier/`
  - Configure logging in `utils.py`: INFO level, console + file output
  - Add debug logs in `matcher.py`: Which criteria matched/failed
  - Add info logs in `engine.py`: Rule loaded, matches found, winner selected
  - Add info logs in `audit.py`: Entry recorded
  - Format: "[TIMESTAMP] [LEVEL] [MODULE] Message"

- [ ] T046 [P] Code review and refactoring
  - Ensure all modules follow project conventions
  - Remove dead code, simplify complex logic
  - Add type hints to function signatures (Python 3.8+)
  - Ensure all docstrings complete and clear

- [ ] T047 [P] Create `setup.py` with package metadata
  - Name: `classifier-rules`
  - Version: 0.1.0
  - Dependencies: psycopg2-binary, pytest (dev)
  - Include: author, description, license
  - Enable: `pip install -e .`

- [ ] T048 Create production deployment guide in `docs/deployment.md`
  - Database setup for production
  - Environment configuration best practices
  - Performance tuning: indexing, connection pooling, caching
  - Monitoring and alerting
  - Backup/restore procedures

- [ ] T049 [P] Performance testing and optimization
  - Load test: 10,000 rules, measure evaluation time
  - Profile: Identify slow sections (matcher, query, IO)
  - Optimize: Add indexes, refactor slow logic, cache if needed
  - Validate: < 500ms for 95th percentile (per SC-003)
  - Run: `pytest tests/unit/test_performance.py`

- [ ] T050 Create migration validation test in `tests/integration/test_migrations.py`
  - Test: All migrations execute successfully in order
  - Test: Schema matches data-model.md specification
  - Test: All indexes created correctly
  - Test: Constraints enforced (NOT NULL, FK, UNIQUE, etc.)
  - Run AFTER migrations implemented

- [ ] T051 Run full test suite and achieve target coverage
  - Execute: `pytest --cov=src/classifier tests/`
  - Target: 85%+ code coverage
  - Identify and test any uncovered paths
  - Generate coverage report: `pytest --cov-report=html`

- [ ] T052 Update `quickstart.md` with verified setup instructions
  - Test: Follow quickstart exactly, ensure it works
  - Test: Create, classify, and audit queries work
  - Test: First-time user experience
  - Fix any gaps or unclear steps

- [ ] T053 Create CHANGELOG.md documenting v0.1.0
  - Summary: Rule Engine Core MVP with priority resolution and audit logging
  - Features: Core evaluate(), priority handling, full audit trail
  - Supported: 3 user stories, 50+ tasks, comprehensive testing
  - Known limitations: No complex conditions (future enhancement)

- [ ] T054 Final validation against specification
  - Verify: All requirements from spec.md met
  - Verify: All success criteria achievable (SC-001 through SC-006)
  - Verify: Edge cases handled (no match, identical priority, invalid data)
  - Verify: Constitution principles upheld
  - Create validation report: `specs/001-rule-engine/validation.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately ✅
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories ⚠️
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): No dependencies on other stories → can start after Foundational
  - User Story 2 (P1): Depends on US1 completion → priority/tiebreak logic extends evaluation
  - User Story 3 (P2): Independent of US2 → but typically added after core engine works
  - User Story 4 (P2): Depends on US1 completion → uses RuleEngine for batch processing
  - User Story 5 (P3): Depends on US1 completion → uses RuleEngine for CSV classification
- **Polish (Final Phase)**: Depends on all desired user stories being complete ✅

### User Story Dependencies

```
┌─────────────┐
│  Phase 2    │
│ Foundational│
└──────┬──────┘
       │
       ├──────────────────────┬─────────────────┬──────────────────┬──────────────────┐
       │                      │                 │                  │                  │
       ▼                      ▼                 ▼                  ▼                  ▼
  ┌────────────┐        ┌────────────┐   ┌────────────┐    ┌────────────┐   ┌────────────┐
  │    US1     │        │    US1     │   │    US1     │    │    US1     │   │    US1     │
  │  (Tests)   │───┬───▶│(Impl)      │   │(Validation)│    │  (Tests)   │   │  (Tests)   │
  └────────────┘   │    └────────────┘   └────────────┘    └────────────┘   └────────────┘
                   │           ▲                                  ▲               ▲
                   │           │                                  │               │
                   ├───────────┼──────────────────────────────────┼───────────────┤
                   │           │                                  │               │
       ┌───────────┘           │                                  │               │
       │                       │                                  │               │
       ▼                       │                                  │               │
  ┌────────────┐              │                          ┌────────────┐   ┌────────────┐
  │    US2     │              │                          │    US4     │   │    US5     │
  │  (Tests)   │──────────────┤                          │  (Tests)   │   │  (Tests)   │
  └────────────┘              │                          └────────────┘   └────────────┘
       │                       │                                  │               │
       ▼                       │                                  ▼               ▼
  ┌────────────┐              │                          ┌────────────┐   ┌────────────┐
  │    US2     │              │                          │    US4     │   │    US5     │
  │ (Priority) │──────────────┤                          │ (Impl)     │   │ (Impl)     │
  └────────────┘              │                          └────────────┘   └────────────┘
       │                       │                                  │               │
       ▼                       │                                  ▼               ▼
  ┌────────────┐              │                          ┌────────────┐   ┌────────────┐
  │    US3     │              │                          │    US4     │   │    US5     │
  │  (Tests)   │──────────────┤                          │(Validation)│   │(Validation)│
  └────────────┘              │                          └────────────┘   └────────────┘
       │                       │                                  │               │
       ▼                       │                                  │               │
  ┌────────────┐              │                                  │               │
  │    US3     │              │                                  │               │
  │  (Audit)   │──────────────┴──────────────────────────────────┴───────────────┤
  └────────────┘                                                                  │
       │                                                                          │
       ▼                                                                          │
  ┌────────────────────────────────────────────────────────────────────────────┐ │
  │                   Polish & Cross-Cutting Concerns                           │◀┘
  └────────────────────────────────────────────────────────────────────────────┘
```

### Within Each User Story

- Tests (if included) MUST be written FIRST, ensure they FAIL before implementation
- Models before services
- Services before core integration
- Core integration tested, then optional polish tasks
- Validation tests run after implementation
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 Setup** — All marked [P] can run in parallel:
- T003, T004, T005 (env, gitignore, README)

**Phase 2 Foundational** — Groups can run in parallel:
- T008, T009, T010 (migrations in parallel)
- T013, T014, T015 (config, exceptions, fixtures)
- BUT: All must complete before Phase 3 begins

**User Story 1** — Within story:
- T016, T018 (contract + integration tests, no dependencies)
- T019, T020 (models, independent)
- T021, T022 (services, independent)
- BUT: Tests before implementation

**User Story 2** — Depends on US1 complete:
- T029, T030 (tests, independent)
- T031 can start once T022 done (needs Evaluator)
- T032 depends on T023 + T031

**User Story 3** — Can start parallel to US2:
- T035, T036 (tests, independent of US2)
- T037 independent service
- T038 needs T023 (RuleEngine)

**User Story 4** — Depends on US1 complete (needs RuleEngine):
- T055, T056 (tests, independent)
- T057 independent service
- T058 needs T057 (CLI script)
- T059, T060 can run after implementation

**User Story 5** — Depends on US1 complete (needs RuleEngine):
- T061, T062 (tests, independent)
- T063 independent service
- T064 needs T063 (CLI script)
- T065 optional export service
- T066, T067, T068 can run after implementation

**Polish Phase** — All marked [P] can run in parallel:
- T042, T043, T044, T045, T046, T047, T048, T049

---

## Parallel Execution Example: User Story 1

### Scenario: 2-person team working on US1

**Developer A**:
```
1. T016 — Write RuleEngine contract tests (test first!)
2. T021 — Implement Matcher service
3. T025 — Write + run matcher unit tests
```

**Developer B** (simultaneous, different files):
```
1. T018 — Write integration test for full flow
2. T019 — Create Rule model
3. T020 — Create Product model
4. T028 — Write + run model unit tests
```

**Sequential together**:
```
5. T022 — Implement Evaluator service (depends on models from B)
6. T026 — Write + run evaluator unit tests
7. T023 — Implement RuleEngine.evaluate() (depends on Matcher + Evaluator)
8. T024 — Integrate all components
9. T027 — Write + run engine unit tests
10. Validate: All tests pass, US1 independently testable ✅
```

---

## Parallel Execution Example: Across Phases

### Scenario: 3-person team with staggered starts

**Person 1** (starts immediately):
```
T001-T005 (Phase 1 Setup) → 2 hours
T006-T012 (Phase 2 Foundational) → 4 hours
T016-T028 (Phase 3 US1 Tests + Implementation) → 8 hours
TOTAL: 14 hours (start now, done in ~3 days at 5h/day)
```

**Person 2** (starts after Phase 2 done):
```
Wait for T012 completion (can start ~day 1 afternoon)
T029-T041 (Phase 4 US2 + US3 Tests + Implementation) → 12 hours
TOTAL: 12 hours (start day 2, done by day 4)
```

**Person 3** (starts during Phase 3):
```
T042-T054 (Phase 5 Polish) → 6 hours
Can start parallel to US1 tests/implementation (day 1 afternoon)
TOTAL: 6 hours (spread across days 2-4)
```

**Team parallel execution**: 3 people, ~4 days calendar time (vs 32 days serial)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

Recommended for fastest MVP delivery:

1. **Day 1**: Complete Phase 1 (Setup) + Phase 2 (Foundational)
   - Tasks: T001-T015
   - Time: ~6 hours
   - Deliverable: Project structure, database ready

2. **Day 2**: Complete Phase 3 (User Story 1)
   - Tasks: T016-T028
   - Time: ~8 hours
   - Deliverable: Working rule evaluation engine

3. **Day 3**: Validate + Polish
   - Tasks: T042-T052 (subset for MVP)
   - Time: ~4 hours
   - Deliverable: MVP-ready with docs + tests

**Result**: Functional Rule Engine that can classify products based on rules. Deploy and get user feedback.

### Incremental Delivery (Recommended for Production)

1. **Sprint 1** (Days 1-3): Deliver MVP (US1 only)
   - Phase 1-3 complete (T001-T028)
   - Deploy to staging
   - Get user feedback

2. **Sprint 2** (Days 4-5): Add Priority Resolution (US2)
   - Phase 4 complete (T029-T034)
   - Enhance engine with conflict resolution
   - Deploy improvements

3. **Sprint 3** (Days 6-7): Add Audit Logging (US3)
   - Phase 5 complete (T035-T041)
   - Full traceability
   - Production ready

4. **Sprint 4** (Days 8-9): Add Batch Processing (US4)
   - Phase 6 complete (T055-T060)
   - CLI script for bulk database classification
   - Enable automated processing

5. **Sprint 5** (Days 10-11): Add CSV Support (US5)
   - Phase 7 complete (T061-T068)
   - CSV import/export capabilities
   - Enable flexible integrations

6. **Sprint 6**: Optimization + Documentation
   - Phase N polish (T042-T054)
   - Performance tuning
   - Comprehensive docs

**Result**: Gradual feature rollout, lower risk, earlier user value. Core engine first, then scripting.

### Alternative: Fast Delivery (All Features at Once)

1. **Day 1**: Setup + Foundational phases
   - Phase 1-2 complete (T001-T015)
   - Time: ~6 hours

2. **Days 2-5**: All user stories in parallel
   - Developer A: US1 (T016-T028)
   - Developer B: US2 (T029-T034)
   - Developer C: US3 (T035-T041)
   - Developer D: US4 (T055-T060)
   - Developer E: US5 (T061-T068)
   - Time: ~4 days, 8+ hours/day each

3. **Days 6-7**: Polish + validation
   - Phase N polish (T042-T054)
   - Performance tuning, docs
   - Time: ~2 days

**Result**: Complete feature set in 7 days with 5+ developers. Higher parallelism, coordinated testing needed.

### Parallel Team Strategy (5+ developers)

1. **Team** (all, day 1): Setup + Foundational phases
   - All work together on T001-T015
   - Time: 1 day, ~6 hours
   - Establish foundation

2. **Developer A**: US1 Tests + Implementation (days 2-3)
   - Focus: Contract tests (T016-T018), models (T019-T020), services (T021-T022), core engine (T023-T028)
   - Delivers: Working RuleEngine that others depend on

3. **Developer B**: US2 Tests + Implementation (starts day 3, after US1 tests pass)
   - Focus: Priority resolution tests (T029-T030), selector service (T031), engine update (T032)
   - Depends on: A's work (RuleEngine.evaluate)

4. **Developer C**: US3 Tests + Implementation (starts day 3, parallel to B)
   - Focus: Audit logging tests (T035-T036), audit service (T037), engine integration (T038)
   - Depends on: A's work (RuleEngine.evaluate)

5. **Developer D**: US4 Tests + Implementation (starts day 3, parallel to B & C)
   - Focus: Batch tests (T055-T056), batch classifier (T057), CLI script (T058)
   - Depends on: A's work (RuleEngine.evaluate)

6. **Developer E**: US5 Tests + Implementation (starts day 3, parallel to B, C, & D)
   - Focus: CSV tests (T061-T062), CSV classifier (T063), CLI script (T064), sample files (T068)
   - Depends on: A's work (RuleEngine.evaluate)

7. **All**: Polish + Validation (days 5-6)
   - Phase N tasks (T042-T054)
   - Docs, performance, final testing
   - Deployment readiness

**Result**: Full feature set in 6 days with 5+ developers. Coordinated testing, US1 blocks others for 1 day only.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests FIRST before implementation (TDD approach per Constitutional Principle IV)
- Verify tests FAIL before implementing (red-green-refactor cycle)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- See `/specs/001-rule-engine/quickstart.md` for testing commands
- See `/specs/001-rule-engine/plan.md` for project structure reference
