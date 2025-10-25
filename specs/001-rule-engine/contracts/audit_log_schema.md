# Audit Log Schema Contract

**Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Purpose**: Define the expected structure and guarantees of audit logs

## Guarantees

1. **100% Logging**: Every classification decision creates exactly one audit log entry
2. **Immutable**: Audit logs are append-only (never updated or deleted)
3. **Complete Traceability**: Every entry contains enough information to understand why a classification was made
4. **Timestamped**: All entries have precise timestamps for ordering
5. **Queryable**: Can efficiently retrieve by product, rule, or time range

## Table: `auditoria_classificacao`

### Schema

```sql
CREATE TABLE auditoria_classificacao (
    id BIGSERIAL PRIMARY KEY,
    id_regra INTEGER REFERENCES regras_de_classificacao(id),
    id_produto VARCHAR(100),
    descricao_produto TEXT,
    ncm_produto VARCHAR(20),
    criterios_combinados TEXT,  -- JSON or CSV of matched criteria
    resultado_classificacao VARCHAR(100) NOT NULL,
    data_classificacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_sistema VARCHAR(100),
    tempo_avaliacao_ms INTEGER,

    -- Indexes for query performance
    INDEX (id_produto, data_classificacao),
    INDEX (id_regra, data_classificacao),
    INDEX (data_classificacao)
);
```

### Columns

| Column | Type | Null | Default | Purpose |
|--------|------|------|---------|---------|
| `id` | BIGSERIAL | NO | auto | Unique audit entry identifier |
| `id_regra` | INTEGER | YES | NULL | Rule that was applied (NULL if no match) |
| `id_produto` | VARCHAR(100) | YES | NULL | Product identifier (business key) |
| `descricao_produto` | TEXT | YES | NULL | Product description at time of classification |
| `ncm_produto` | VARCHAR(20) | YES | NULL | NCM code at time of classification |
| `criterios_combinados` | TEXT | YES | NULL | JSON/CSV of criteria that matched |
| `resultado_classificacao` | VARCHAR(100) | NO | - | Classification result code (never NULL) |
| `data_classificacao` | TIMESTAMP | NO | CURRENT_TIMESTAMP | When classification occurred |
| `usuario_sistema` | VARCHAR(100) | YES | NULL | System user/process name |
| `tempo_avaliacao_ms` | INTEGER | YES | NULL | Evaluation time in milliseconds |

## Query Patterns

### Find all classifications for a product

```sql
SELECT id, data_classificacao, id_regra, resultado_classificacao
FROM auditoria_classificacao
WHERE id_produto = 'PROD_001'
ORDER BY data_classificacao DESC;
```

**Expected result**: All classification attempts for product, newest first

### Find recent classifications by rule

```sql
SELECT id, id_produto, resultado_classificacao, data_classificacao
FROM auditoria_classificacao
WHERE id_regra = 5
AND data_classificacao >= NOW() - INTERVAL '1 day'
ORDER BY data_classificacao DESC;
```

**Expected result**: All classifications using rule 5 in last 24 hours

### Find no-match cases

```sql
SELECT id, id_produto, data_classificacao
FROM auditoria_classificacao
WHERE id_regra IS NULL
ORDER BY data_classificacao DESC
LIMIT 100;
```

**Expected result**: Products that matched no rules (up to 100)

### Get rule performance statistics

```sql
SELECT
    id_regra,
    COUNT(*) as times_applied,
    MAX(data_classificacao) as last_applied,
    AVG(tempo_avaliacao_ms) as avg_time_ms,
    MIN(tempo_avaliacao_ms) as min_time_ms,
    MAX(tempo_avaliacao_ms) as max_time_ms
FROM auditoria_classificacao
WHERE data_classificacao >= NOW() - INTERVAL '7 days'
GROUP BY id_regra
ORDER BY times_applied DESC;
```

**Expected result**: Performance metrics for each rule over last 7 days

### Get classification distribution

```sql
SELECT
    resultado_classificacao,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM auditoria_classificacao
WHERE data_classificacao >= NOW() - INTERVAL '1 day'
GROUP BY resultado_classificacao
ORDER BY count DESC;
```

**Expected result**: How many products fell into each classification yesterday

## Entry Examples

### Successful Match

```json
{
    "id": 10001,
    "id_regra": 5,
    "id_produto": "SKU_ABC123",
    "descricao_produto": "Dell XPS 13 laptop computer",
    "ncm_produto": "84713090",
    "criterios_combinados": "{\"matched_criteria\": [\"keywords: laptop,computer\"], \"keyword_matches\": [\"laptop\", \"computer\"]}",
    "resultado_classificacao": "ELECTRONICS",
    "data_classificacao": "2025-10-25T14:30:45.123456",
    "usuario_sistema": "batch_import_v2",
    "tempo_avaliacao_ms": 42
}
```

### No Match

```json
{
    "id": 10002,
    "id_regra": null,
    "id_produto": "SKU_XYZ789",
    "descricao_produto": "Obscure product with no matching rules",
    "ncm_produto": "99999999",
    "criterios_combinados": "{\"evaluated_rules\": 25, \"all_mismatches\": true}",
    "resultado_classificacao": "NO_MATCH",
    "data_classificacao": "2025-10-25T14:31:12.654321",
    "usuario_sistema": "batch_import_v2",
    "tempo_avaliacao_ms": 187
}
```

### Multiple Rules Evaluated (Winner Selected)

```json
{
    "id": 10003,
    "id_regra": 8,
    "id_produto": "SKU_DEF456",
    "descricao_produto": "Samsung 24-inch monitor",
    "ncm_produto": "85287000",
    "criterios_combinados": "{\"matched_rules\": [8, 12, 3], \"evaluated_rules\": 5, \"winner\": 8, \"winner_priority\": 150, \"reason\": \"highest priority\"}",
    "resultado_classificacao": "MONITORS",
    "data_classificacao": "2025-10-25T14:32:00.789012",
    "usuario_sistema": "rest_api_service",
    "tempo_avaliacao_ms": 125
}
```

## Data Quality Rules

### Validation

- `resultado_classificacao` MUST NOT be NULL or empty
- `data_classificacao` MUST NOT be in the future (at time of insert)
- `id_regra` is NULL when NO rule matched; otherwise must reference valid rule ID
- `tempo_avaliacao_ms` MUST be >= 0 and < 60000 (reasonable bounds)
- If `id_regra` is NOT NULL, that rule must have `ativo=TRUE` at time of classification

### Data Retention

- Audit logs are IMMUTABLE (never updated or deleted in normal operations)
- Retention policy: Keep indefinitely (or per business/compliance requirements)
- Archive older entries only via explicit archival process (if needed)

## Performance Targets

### Query Performance

- **By product**: < 50ms (with proper indexing)
- **By rule + date range**: < 100ms for 7+ days of data
- **Recent unmatched**: < 50ms (most recent 100)
- **Statistics aggregation**: < 1s for 30 days of data

### Storage

- Expected growth: ~100-500 bytes per entry (JSON `criterios_combinados` varies)
- Example: 1M classifications/day = 100MB-500MB/day storage
- Yearly: ~36-180 GB (before compression/archival)

## Integration Points

### RuleEngine.evaluate()

After evaluation completes, RuleEngine MUST:
1. Create ONE audit log entry with all details
2. Include `id_regra` (NULL if no match)
3. Include `resultado_clasificacao` (never NULL)
4. Include `tempo_avaliacao_ms` measured by evaluation engine
5. Execute INSERT within same transaction as rule fetch (or separate, explicit log)

### Example Flow

```
RuleEngine.evaluate(product) called
  ↓
Fetch active rules from DB
  ↓
Matcher.evaluate() each rule
  ↓
Evaluator.select_winner() if multiple matches
  ↓
Measure evaluation time
  ↓
AuditLog.record(rule_id, product, criteria, result, time, user)
  ↓
INSERT into auditoria_classificacao
  ↓
Return {classification, rule_id, ...} to caller
```

## Compliance & Auditing

### Access Control

- Audit logs should be readable by: developers, operators, compliance team
- Audit logs should be write-protected (append-only, no updates/deletes in normal ops)
- Sensitive data: product descriptions and NCM codes logged (use database-level encryption if needed)

### Reports

Common reports from audit logs:
1. **Classification Distribution**: By product category, result type, time period
2. **Rule Performance**: Which rules match products, which are unused
3. **Coverage**: What percentage of products matched at least one rule
4. **No-Match Analysis**: Product descriptions that triggered no rules
5. **Performance**: Evaluation time trends, slow queries

## Future Enhancements

- Add `metadata` JSONB column for future extensibility
- Add `rule_version` to track rule schema changes
- Add `confidence_score` if probabilistic matching added
- Archive tables for historical data
