# Data Model: Rule Engine Core

**Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Purpose**: Define entities, attributes, relationships, and validation rules for the Rule Engine

## Entity Definitions

### 1. Rule (`regras_de_classificacao`)

**Purpose**: Defines a single classification rule that can be applied to products

**Fields**:
- `id` (INTEGER, PRIMARY KEY) — Unique rule identifier
- `prioridade` (INTEGER, NOT NULL) — Priority level (higher = more important)
- `nome` (VARCHAR(255), NOT NULL) — Rule name/description
- `ativo` (BOOLEAN, DEFAULT TRUE) — Whether rule is active/enabled
- `criterio_palavras_chave` (TEXT) — Comma-separated keywords to match in product description
- `criterio_ncm` (VARCHAR(20)) — NCM pattern (supports wildcards, e.g., "8471*")
- `criterio_tamanho_min` (DECIMAL(10,2)) — Minimum size threshold (nullable)
- `criterio_tamanho_max` (DECIMAL(10,2)) — Maximum size threshold (nullable)
- `criterio_quantidade_min` (INTEGER) — Minimum quantity threshold (nullable)
- `criterio_quantidade_max` (INTEGER) — Maximum quantity threshold (nullable)
- `criterio_categoria` (VARCHAR(100)) — Product category filter (nullable)
- `resultado_classificacao` (VARCHAR(100), NOT NULL) — Classification result/code to return
- `data_criacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Rule creation timestamp
- `data_atualizacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Last update timestamp

**Indexes**:
- PRIMARY KEY: `id`
- COMPOSITE: `(prioridade DESC, ativo)` for efficient rule lookup
- SIMPLE: `(data_criacao)` for tiebreaker resolution

**Validation Rules**:
- `prioridade` MUST NOT be NULL
- `nome` MUST NOT be empty
- `resultado_classificacao` MUST NOT be empty
- At least ONE criteria field MUST be non-NULL (keyword, NCM, size, quantity, or category)
- If `criterio_tamanho_min` is set, `criterio_tamanho_max` MUST be >= `criterio_tamanho_min`
- If `criterio_quantidade_min` is set, `criterio_quantidade_max` MUST be >= `criterio_quantidade_min`

**State Transitions**:
- NEW → ACTIVE (ativo = TRUE)
- ACTIVE → INACTIVE (ativo = FALSE)
- Any state → ANY state (data_atualizacao timestamp updated)

### 2. AuditLog (`auditoria_classificacao`)

**Purpose**: Tracks every classification decision for auditability and debugging

**Fields**:
- `id` (BIGINT, PRIMARY KEY) — Unique audit log entry ID
- `id_regra` (INTEGER, FOREIGN KEY → `regras_de_classificacao.id`) — Rule that was applied
- `id_produto` (VARCHAR(100)) — Product identifier being classified (nullable for manual classifications)
- `descricao_produto` (TEXT) — Product description
- `ncm_produto` (VARCHAR(20)) — NCM code of product
- `criterios_combinados` (TEXT) — Which criteria matched (JSON or CSV format)
- `resultado_classificacao` (VARCHAR(100), NOT NULL) — Resulting classification
- `data_classificacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — When classified
- `usuario_sistema` (VARCHAR(100)) — System user/process that triggered classification
- `tempo_avaliacao_ms` (INTEGER) — Evaluation time in milliseconds (performance tracking)

**Indexes**:
- PRIMARY KEY: `id`
- COMPOSITE: `(id_produto, data_classificacao)` for fast product history queries
- COMPOSITE: `(id_regra, data_classificacao)` for rule audit trails
- SIMPLE: `(data_classificacao)` for time-range queries

**Validation Rules**:
- `id_regra` MUST reference a valid rule (foreign key constraint)
- `resultado_classificacao` MUST NOT be empty
- `data_classificacao` MUST NOT be in the future
- `tempo_avaliacao_ms` MUST be >= 0

**Special Cases**:
- When NO rule matches: `id_regra` = NULL, `resultado_classificacao` = "NO_MATCH" or fallback value
- When multiple rules match (only one applies): `id_regra` = winner rule ID, `criterios_combinados` shows all matching rules evaluated

### 3. KeywordCriteria (`criterios_palavras_chave`)

**Status**: NOT USED IN V1 - Reserved for future normalization

**Purpose**: Normalized keyword storage (optional, for normalized keyword matching in V2+)

**Note**: V1 uses `regras_de_classificacao.criterio_palavras_chave` (comma-separated keywords stored directly in rule).
This table is prepared for future normalization but not utilized in current implementation.

**Fields** (for future reference):
- `id` (INTEGER, PRIMARY KEY) — Keyword entry ID
- `id_regra` (INTEGER, FOREIGN KEY → `regras_de_classificacao.id`) — Rule this keyword belongs to
- `palavra_chave` (VARCHAR(100), NOT NULL) — Individual keyword (lowercase)
- `peso` (DECIMAL(3,2), DEFAULT 1.0) — Optional: keyword importance weight
- `data_criacao` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP) — Creation timestamp

**Indexes** (prepared, not used):
- PRIMARY KEY: `id`
- UNIQUE: `(id_regra, palavra_chave)` prevents duplicate keywords per rule
- SIMPLE: `(palavra_chave)` for keyword-based searches

**Validation Rules** (for future use):
- `id_regra` MUST reference a valid rule (foreign key constraint)
- `palavra_chave` MUST NOT be empty and MUST be lowercase
- `peso` MUST be between 0.0 and 10.0

## Relationships

```
Rule (regras_de_classificacao)
  ├─ has many ← KeywordCriteria (criterios_palavras_chave)
  └─ has many ← AuditLog (auditoria_classificacao)
```

## State Machines

### Rule Lifecycle

```
[CREATED (ativo=TRUE)]
       ↓
   [ACTIVE]
       ↓ (DISABLE)
   [INACTIVE (ativo=FALSE)]
       ↓ (RE-ENABLE)
   [ACTIVE]
       ↓ (DELETE)
   [DELETED]
```

### Classification Workflow

```
[INCOMING PRODUCT]
       ↓
[FETCH ACTIVE RULES]
       ↓
[EVALUATE EACH RULE AGAINST CRITERIA]
       ↓
[SELECT HIGHEST PRIORITY MATCHING RULE]
       ↓
[CREATE AUDIT LOG ENTRY]
       ↓
[RETURN CLASSIFICATION RESULT]
```

## Domain Constraints

### Rule Priority

- Priority is numeric integer (no tied weights or complex calculations)
- Higher number = higher priority
- Tiebreaker: oldest rule by creation date wins (FIFO for same priority)
- Priority MUST be set for all rules

### Criteria Matching

- Keywords: Case-insensitive substring matching in product description
- NCM: Supports wildcard patterns (e.g., "8471*" matches any 8471XX)
- Size & Quantity: Range-based matching (both min AND max must be satisfied if specified)
- Category: Exact string match
- All specified criteria must be satisfied (AND logic within rule)

### Classification Results

- MUST be non-null string
- MUST be documented in business rules
- Examples: "CLASSIFICATION_A", "CATEGORY_B", "TYPE_C", "FALLBACK"

## Performance Considerations

### Indexing Strategy

- Fast priority-based rule lookup: `(prioridade DESC, ativo)` for efficient TOP 1 queries
- Fast product history: `(id_produto, data_classificacao)` for audit trail queries
- Fast rule audit: `(id_regra, data_classificacao)` for rule performance analysis

### Query Patterns

**Find matching rules for a product**:
```sql
SELECT * FROM regras_de_classificacao
WHERE ativo = TRUE
ORDER BY prioridade DESC
LIMIT 1  -- Return only highest priority rule
```

**Log classification decision**:
```sql
INSERT INTO auditoria_classificacao (...)
VALUES (...)
```

**Query product classification history**:
```sql
SELECT * FROM auditoria_classificacao
WHERE id_produto = ?
ORDER BY data_classificacao DESC
```

## Migration Strategy

### V1 (Initial Schema)

- Create `regras_de_classificacao` table with all core columns
- Create `auditoria_classificacao` table for audit logging
- Create indexes for performance
- Idempotent: use `CREATE TABLE IF NOT EXISTS`

### V2+ (Future Enhancements)

- Optional: Create `criterios_palavras_chave` for normalized keywords
- Add new criteria columns to `regras_de_classificacao` as needed
- Always backward-compatible: new columns nullable with defaults
- Migration scripts must be reversible

## Assumptions

- Rules do not change during an active evaluation (cached/immutable during request processing)
- Audit logs are append-only (never deleted, only archived)
- Performance targets assume proper indexing and database configuration
- Tiebreaker (oldest rule by creation date) is acceptable for identical-priority situations
