# Research: Rule Engine Core Implementation

**Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Purpose**: Document research findings, technology choices, and patterns for rule engine implementation

## 1. Rule Evaluation Engine Design

### Decision: Generic, Stateless Engine

**What was chosen**: Build a stateless rule evaluation engine that reads rules from database each time, with optional in-memory caching for performance.

**Rationale**:
- Enables real-time rule updates (disable/enable without restart)
- Supports constitutional Principle I (Data-Driven Logic)
- Simple to test and debug
- No state management complexity

**Alternatives considered**:
- A. Pre-compile rules to bytecode: Faster but breaks data-driven requirement; rejected
- B. Cache rules in memory with refresh: Good performance; chosen as optional feature
- C. Stream rules from queue: Adds complexity; rejected for MVP

**Implementation approach**:
- Load active rules from `regras_de_classificacao` on each evaluation (or cached)
- Evaluate each rule independently
- Collect all matching rules
- Select winner by priority (then by creation date for tiebreak)
- Log decision to audit table

## 2. Priority & Conflict Resolution

### Decision: Numeric Priority with FIFO Tiebreaker

**What was chosen**: Use numeric priority field (higher = more important); for identical priorities, use creation timestamp (oldest wins).

**Rationale**:
- Simple and deterministic
- No complex weighting algorithms
- FIFO tiebreaker is fair and reproducible
- Easy to explain to business users

**Alternatives considered**:
- A. Complex scoring algorithm: Too complex, violates Principle II; rejected
- B. Random tiebreaker: Non-deterministic, bad for debugging; rejected
- C. Last-created wins (LIFO): Less intuitive; rejected
- D. Creation date + creation time microseconds: Selected for full determinism

**Implementation**:
```python
# Sort matching rules
sorted_rules = sorted(
    matching_rules,
    key=lambda r: (-r['prioridade'], r['data_criacao'])  # desc priority, asc date
)
winner = sorted_rules[0]
```

## 3. Criteria Matching Strategy

### Decision: Simple Field Matching (No Complex Expressions)

**What was chosen**: Support simple, independent criteria checks (keywords, NCM wildcard, size range, quantity range, category). All specified criteria must match (AND logic).

**Rationale**:
- Satisfies Principle II (Code Simplicity)
- Business can express complex logic via multiple rules with different priorities
- Easy to understand and maintain
- Consistent matching semantics

**Alternatives considered**:
- A. SQL WHERE clause in rule: Dangerous (SQL injection), complex; rejected
- B. Full boolean expression language: Requires parser, too complex; rejected
- C. Elasticsearch-style queries: Overkill for requirements; rejected
- D. Simple field matching (chosen): Matches spec requirements exactly

**Criteria fields supported**:
1. Keywords: Comma-separated, substring match (case-insensitive)
2. NCM: Pattern with wildcards (8471* matches 84710000, 84713090, etc.)
3. Size: Range [min, max] (both must match if either specified)
4. Quantity: Range [min, max] (both must match if either specified)
5. Category: Exact match (case-sensitive)

**Matching logic**:
- For each rule: check all specified criteria
- If ANY specified criterion is false: rule doesn't match
- If all specified criteria are true: rule matches

## 4. Audit Logging Strategy

### Decision: Append-Only Audit Table with Detailed Matching Info

**What was chosen**: Create `auditoria_classificacao` table with full classification context. Log every decision (including no-match cases).

**Rationale**:
- Satisfies Principle V (Auditability)
- Enables rule performance analysis and debugging
- Traceable to specific product and rule
- Immutable audit trail

**Alternatives considered**:
- A. No audit logging: Violates constitution; rejected
- B. Log only to file: Harder to query; rejected
- C. Log to separate audit service: Extra complexity; rejected
- D. Database audit table (chosen): Simple, queryable, reliable

**What gets logged**:
- Rule ID that matched (NULL for no-match)
- Product identifier and description
- NCM code
- Which criteria matched (JSON)
- Classification result
- Timestamp
- Evaluation time in ms
- System user/process name

**Query patterns**:
- Find all classifications for a product
- Find all uses of a specific rule
- Get performance stats per rule
- Find no-match cases
- Trace why a product was classified a certain way

## 5. Performance Optimization

### Decision: Database Indexes + Optional In-Memory Caching

**What was chosen**:
- Key indexes on (prioridade DESC, ativo) for efficient rule lookup
- Optional in-memory rule cache with manual refresh
- Performance target: < 500ms for 10,000 active rules

**Rationale**:
- Indexes handle database-side filtering
- Caching reduces round-trip latency for repeated evaluations
- Manual refresh keeps behavior predictable

**Alternatives considered**:
- A. No optimization: Would fail performance targets; rejected
- B. Redis cache layer: Extra infrastructure complexity; rejected
- C. Database-only with good indexes: Works well for most cases; selected
- D. In-memory cache + manual refresh (chosen): Good balance

**Index strategy**:
```sql
-- Primary lookup: find matching rules
CREATE INDEX idx_rules_active_priority
ON regras_de_classificacao(prioridade DESC, ativo);

-- Audit queries: product history
CREATE INDEX idx_audit_product_time
ON auditoria_classificacao(id_produto, data_classificacao DESC);

-- Audit queries: rule analysis
CREATE INDEX idx_audit_rule_time
ON auditoria_classificacao(id_regra, data_classificacao DESC);
```

**Caching behavior**:
- Load all active rules at startup (or first evaluation)
- Use in-memory list if cache enabled
- Call `refresh_cache()` after bulk rule updates
- Cache invalidates on timeout or explicit refresh

## 6. Database Technology

### Decision: PostgreSQL 12+ with psycopg2 Driver

**What was chosen**: PostgreSQL for reliability, ACID guarantees, and JSON support.

**Rationale**:
- Mature, production-grade database
- ACID compliance ensures audit log integrity
- JSON type for flexible `criterios_combinados` field
- Good performance with proper indexing
- Compatible with existing `market_v1` database

**Alternatives considered**:
- A. MySQL: Lacks some JSON features; rejected
- B. SQLite: Not suitable for multi-process usage; rejected
- C. MongoDB: No strong schema enforcement for audit; rejected
- D. PostgreSQL (chosen): Best fit for requirements

**Driver**: psycopg2 (mature, widely used)

## 7. Error Handling & Resilience

### Decision: Explicit Error Types with Fallback Options

**What was chosen**:
- Define custom exception types (ConfigError, DatabaseError, ProductError, EvaluationError)
- Caller chooses fallback behavior (fail-safe or return NO_MATCH)
- Audit logs track errors for debugging

**Rationale**:
- Clear error semantics help developers handle failures appropriately
- Different failure modes need different responses
- No silent failures; explicit error reporting

**Error types**:
1. `ConfigError`: .env missing or database unreachable → system won't start
2. `DatabaseError`: Query failed → caller can retry or use fallback
3. `ProductError`: Invalid product data → skip product or return error
4. `EvaluationError`: Unexpected logic error → log and alert

## 8. Testing Strategy

### Decision: Test-First with Unit, Integration, and Contract Tests

**What was chosen**:
- Unit tests: Matcher, Evaluator, Audit components in isolation
- Integration tests: Full evaluate() flow with real database
- Contract tests: Public API expectations and behavior
- Performance tests: Ensure < 500ms with 10k rules

**Test coverage targets**:
- Core logic (matcher, evaluator): 95%+ coverage
- Error handling: All exception paths tested
- Edge cases: From spec (no match, identical priority, NULL fields)

**Alternatives considered**:
- A. No testing: Violates Principle IV; rejected
- B. Integration only: Miss unit-level bugs; rejected
- C. Unit only: Can't catch integration issues; rejected
- D. Comprehensive multi-level testing (chosen): Best coverage

## 9. Backward Compatibility

### Decision: Schema Versioning + Migration Scripts

**What was chosen**:
- Track schema version in migration history table
- Write reversible (UP/DOWN) migrations
- New columns nullable with sensible defaults
- Active rules table remains backward-compatible

**Rationale**:
- Satisfies Principle V (Backward Compatibility)
- Allows incremental feature additions
- Can rollback if needed

**Migration approach**:
```sql
-- V1 (initial)
CREATE TABLE regras_de_classificacao ( ... );
CREATE TABLE auditoria_classificacao ( ... );

-- V2+ (future)
ALTER TABLE regras_de_classificacao ADD COLUMN new_field VARCHAR DEFAULT NULL;
-- Migration tracks: CREATE MIGRATION 002_add_new_field UP/DOWN
```

## 10. Documentation

### Decision: API Contracts + Quickstart + Rules Guide

**What was chosen**:
- API contracts document library interface and behavior
- Quickstart guide for 5-minute setup
- Data model documentation for schema details
- Rules guide for business users (future)

**Rationale**:
- Clear contracts enable multiple implementations/languages if needed
- Quickstart onboards new developers quickly
- Schema docs prevent errors

## Summary of Key Decisions

| Aspect | Decision | Reason |
|--------|----------|--------|
| Engine | Stateless + optional cache | Real-time updates, simple |
| Priority | Numeric + FIFO tiebreak | Deterministic, explainable |
| Criteria | Simple field matching | Code simplicity (Principle II) |
| Audit | Database append-only table | Full traceability (Principle V) |
| Database | PostgreSQL 12+ | Maturity, ACID, JSON support |
| Caching | Optional in-memory | Performance without complexity |
| Errors | Custom exceptions | Explicit, handleable errors |
| Testing | Multi-level coverage | Comprehensive validation |
| Compatibility | Schema versioning | Incremental changes |

## References

- Constitution: `.specify/memory/constitution.md` (5 principles, infrastructure requirements)
- Feature Spec: `specs/001-rule-engine/spec.md` (user stories, requirements)
- Implementation Plan: `specs/001-rule-engine/plan.md` (technical context, project structure)
