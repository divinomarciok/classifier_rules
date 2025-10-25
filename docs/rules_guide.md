# Rules Guide - For Business Users

**Audience**: Business analysts, rule creators, compliance managers

This guide explains how to create and manage classification rules in the database without needing to modify code.

## Table of Contents

1. [How to Create a Rule](#how-to-create-a-rule)
2. [Rule Priority Explanation](#rule-priority-explanation)
3. [Matching Criteria Types](#matching-criteria-types)
4. [Real-World Examples](#real-world-examples)
5. [Debugging Classifications](#debugging-classifications)
6. [Best Practices](#best-practices)

---

## How to Create a Rule

All rules are stored in the `regras_de_classificacao` database table. You don't need to write Python code - just insert a row into this table.

### Basic SQL Syntax

```sql
INSERT INTO regras_de_classificacao (
    nome,
    prioridade,
    resultado_classificacao,
    criterio_palavras_chave,
    criterio_ncm,
    criterio_tamanho_min,
    criterio_tamanho_max,
    criterio_quantidade_min,
    criterio_quantidade_max,
    criterio_categoria,
    ativo,
    data_criacao
) VALUES (
    'Rule Name Here',
    50,              -- Priority (higher = evaluated first)
    'CLASSIFICATION',
    'keyword1',      -- Optional: product description search
    '8471*',         -- Optional: NCM pattern
    0.5,             -- Optional: minimum size
    2.0,             -- Optional: maximum size
    1,               -- Optional: minimum quantity
    100,             -- Optional: maximum quantity
    'CATEGORY',      -- Optional: product category
    true,            -- true = active, false = inactive
    NOW()
);
```

### Required Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `nome` | TEXT | "Electronics Rule" | Human-readable rule name |
| `prioridade` | INT | 50 | Higher number = higher priority |
| `resultado_classificacao` | TEXT | "ELECTRONICS" | The classification to apply |
| `ativo` | BOOLEAN | true | Must be true for rule to apply |
| `data_criacao` | TIMESTAMP | NOW() | Auto-set to current time |

### Optional Fields (Criteria)

Leave these NULL if not needed:

| Field | Type | Example | Behavior |
|-------|------|---------|----------|
| `criterio_palavras_chave` | TEXT | "laptop" | Substring search in description (case-insensitive) |
| `criterio_ncm` | TEXT | "8471*" | NCM code pattern (supports `*` wildcard) |
| `criterio_tamanho_min` | FLOAT | 0.5 | Minimum product size (product.size >= this) |
| `criterio_tamanho_max` | FLOAT | 2.0 | Maximum product size (product.size <= this) |
| `criterio_quantidade_min` | INT | 1 | Minimum quantity (product.quantity >= this) |
| `criterio_quantidade_max` | INT | 100 | Maximum quantity (product.quantity <= this) |
| `criterio_categoria` | TEXT | "ELECTRONICS" | Exact category match (case-insensitive) |

---

## Rule Priority Explanation

When multiple rules match a product, the system uses **priority** to determine which rule wins.

### How Priority Works

1. **Higher Priority Wins**: A rule with priority 100 is evaluated before priority 50
2. **All Criteria Must Match**: ALL specified criteria in a rule must match for the rule to apply
3. **First Match Wins**: Once a rule matches, its classification is returned (no further rules checked)

### Priority Levels (Recommendations)

```
Priority 100+    → Very specific rules (keywords + multiple criteria)
Priority 50-99   → Specific rules (keywords or specific NCM patterns)
Priority 10-49   → General rules (broad NCM patterns)
Priority 1-9     → Fallback/default rules
Priority 0       → Emergency catch-all (rarely used)
```

### Example: Priority Order

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao, criterio_palavras_chave) VALUES
('Laptop Keyword Rule', 100, 'ELECTRONICS', 'laptop'),
('Computer NCM Rule', 50, 'IT_EQUIPMENT', NULL),
('Catch-All Electronics', 10, 'GENERAL_ELECTRONICS', NULL);
```

**Evaluation Order:**
1. Check rule with priority 100 (Laptop Keyword Rule)
   - If product description contains "laptop" → return ELECTRONICS
2. If not matched, check priority 50 (Computer NCM Rule)
   - If NCM matches → return IT_EQUIPMENT
3. If not matched, check priority 10 (Catch-All)
   - Return GENERAL_ELECTRONICS

### Tiebreaker: Oldest Rule Wins

If two rules have the **same priority**, the oldest rule (earliest `data_criacao`) is used.

**Example:**
```
Rule A: priority=50, created 2025-01-01 → WINS
Rule B: priority=50, created 2025-01-02 → Not checked
```

**Reason**: Ensures consistent, predictable behavior. Oldest rules are considered "stable" and get priority in ties.

---

## Matching Criteria Types

Rules support 5 types of matching criteria. A rule matches only if ALL of its specified criteria match (AND logic).

### 1. Keyword Criteria (`criterio_palavras_chave`)

**What it does**: Searches for a substring in the product description (case-insensitive)

**SQL Example**:
```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao, criterio_palavras_chave, ativo)
VALUES ('Laptop Rule', 100, 'ELECTRONICS', 'laptop', true);
```

**Matches**:
- ✅ "Dell laptop computer"
- ✅ "LAPTOP GAMING DEVICE"
- ✅ "laptop for work"
- ❌ "Desktop computer" (no "laptop")

**Use Cases**:
- High-priority specific product names
- Brand-specific rules
- Product type keywords

---

### 2. NCM Criteria (`criterio_ncm`)

**What it does**: Matches product NCM code using wildcard patterns

**Wildcards**:
- `*` = matches any characters
- `8471*` matches any code starting with 8471

**SQL Example**:
```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao, criterio_ncm, ativo)
VALUES ('Computer NCM Rule', 50, 'IT_EQUIPMENT', '8471*', true);
```

**Matches**:
- ✅ "84713090" (starts with 8471)
- ✅ "84713010"
- ❌ "84701000" (doesn't start with 8471)

**Common Patterns**:
- `84*` = All computers and peripherals
- `8471*` = Automatic data processing machines
- `85171200` = Exact code (no wildcard)

**Use Cases**:
- Broad category matching by NCM chapter
- Standard tariff classification rules

---

### 3. Size Range Criteria (`criterio_tamanho_min` / `criterio_tamanho_max`)

**What it does**: Matches products within a size range (inclusive)

**SQL Example**:
```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_tamanho_min, criterio_tamanho_max, ativo)
VALUES ('Small Item Rule', 30, 'SMALL_ITEM', 0.1, 0.5, true);
```

**Matches**: Products with `size >= 0.1` AND `size <= 0.5`
- ✅ size = 0.1
- ✅ size = 0.3
- ✅ size = 0.5
- ❌ size = 0.05 (too small)
- ❌ size = 0.6 (too large)

**Use Cases**:
- Shipping cost rules
- Handling/storage categorization
- Size-based pricing tiers

---

### 4. Quantity Range Criteria (`criterio_quantidade_min` / `criterio_quantidade_max`)

**What it does**: Matches products ordered in a quantity range (inclusive)

**SQL Example**:
```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_quantidade_min, criterio_quantidade_max, ativo)
VALUES ('Bulk Order Rule', 25, 'BULK_PRICING', 100, 500, true);
```

**Matches**: Products with `quantity >= 100` AND `quantity <= 500`
- ✅ quantity = 100
- ✅ quantity = 250
- ✅ quantity = 500
- ❌ quantity = 50 (too small)
- ❌ quantity = 1000 (too large)

**Use Cases**:
- Bulk vs. retail classification
- Wholesale pricing rules
- Stock category rules

---

### 5. Category Criteria (`criterio_categoria`)

**What it does**: Exact match on product category (case-insensitive)

**SQL Example**:
```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_categoria, ativo)
VALUES ('Electronics Category Rule', 40, 'ELECTRONICS', 'ELECTRONICS', true);
```

**Matches**: Product with `category = "ELECTRONICS"` (case-insensitive)
- ✅ "ELECTRONICS"
- ✅ "electronics"
- ✅ "Electronics"
- ❌ "COMPUTER" (not an exact match)

**Use Cases**:
- Category-based refinement rules
- Pre-categorized product rules

---

## Real-World Examples

### Example 1: Laptop Classification

**Business Rule**: "Products described as 'laptop' should be classified as ELECTRONICS"

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao, criterio_palavras_chave, ativo)
VALUES
('Laptop Identification', 100, 'ELECTRONICS', 'laptop', true);
```

**Products Affected**:
- Dell laptop → ELECTRONICS ✅
- Asus Gaming Laptop → ELECTRONICS ✅
- Desktop PC → Not matched ❌

---

### Example 2: IT Equipment by NCM

**Business Rule**: "Products with NCM 8471* (automatic data processing) → IT_EQUIPMENT"

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao, criterio_ncm, ativo)
VALUES
('IT Equipment NCM', 60, 'IT_EQUIPMENT', '8471*', true);
```

**Products Affected**:
- Motherboard (NCM 84713090) → IT_EQUIPMENT ✅
- CPU (NCM 84713010) → IT_EQUIPMENT ✅
- Monitor (NCM 85287200) → Not matched ❌

---

### Example 3: Small Item Handling

**Business Rule**: "Items < 0.5kg should be classified as SMALL_PARCEL for shipping"

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_tamanho_max, ativo)
VALUES
('Small Item Handling', 30, 'SMALL_PARCEL', 0.5, true);
```

**Products Affected**:
- USB Cable (0.05kg) → SMALL_PARCEL ✅
- Keyboard (0.4kg) → SMALL_PARCEL ✅
- Monitor (5kg) → Not matched ❌

---

### Example 4: Bulk Discount Rule

**Business Rule**: "Orders of 100+ units qualify for BULK_PRICING"

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_quantidade_min, ativo)
VALUES
('Bulk Order Discount', 25, 'BULK_PRICING', 100, NULL, true);
```

**Products Affected**:
- 500 units ordered → BULK_PRICING ✅
- 150 units ordered → BULK_PRICING ✅
- 50 units ordered → Not matched ❌

---

### Example 5: Complex Rule (Multiple Criteria)

**Business Rule**: "Laptops under 2kg with 'gaming' keyword → GAMING_LAPTOP (high priority)"

```sql
INSERT INTO regras_de_classificacao
(nome, prioridade, resultado_classificacao,
 criterio_palavras_chave, criterio_tamanho_max, ativo)
VALUES
('Gaming Laptop Rule', 150, 'GAMING_LAPTOP', 'gaming', 2.0, true);
```

**Required for Match**:
- Description must contain "gaming" AND
- Size must be <= 2.0kg

**Products Affected**:
- "Gaming laptop 1.5kg" → GAMING_LAPTOP ✅
- "Gaming desktop 10kg" → Not matched (size too large) ❌
- "Regular laptop 1.5kg" → Not matched (no "gaming" keyword) ❌

---

## Debugging Classifications

If a product isn't being classified as expected, use the audit log to investigate.

### Step 1: Check Audit Log

Query the audit log to see what happened:

```sql
SELECT * FROM auditoria_classificacao
WHERE id_produto = 'PROD123'
ORDER BY data_classificacao DESC
LIMIT 10;
```

**Key Columns**:
- `id_regra`: Which rule matched (NULL = no match)
- `resultado_classificacao`: What result was returned
- `criterios_correspondentes`: Which criteria actually matched
- `tempo_avaliacao_ms`: How long evaluation took

### Step 2: Check Active Rules

Verify that the rule you expect to apply is actually active:

```sql
SELECT * FROM regras_de_classificacao
WHERE ativo = true
ORDER BY prioridade DESC;
```

**Check**:
- Is your rule in this list?
- Is `ativo` set to true?
- Are priorities correct relative to other rules?

### Step 3: Test Criteria Manually

Test if the criteria should match:

```sql
-- Test product exists
SELECT id, description, ncm FROM products WHERE id = 'PROD123';

-- Example: Check if rule priority is blocking it
SELECT * FROM regras_de_classificacao
WHERE prioridade > 50  -- Your rule's priority
AND ativo = true;
-- If results exist, they might block your rule
```

### Step 4: Common Issues

**Problem**: Rule created but never matches

**Solutions**:
1. Check `ativo` is true (not false)
2. Check `prioridade` - higher rules might match first
3. Check criteria:
   - Keyword is substring of description? (case-insensitive)
   - NCM matches pattern? (use SQL `LIKE` to test)
   - Size in range? (>= min AND <= max)
   - Quantity in range? (>= min AND <= max)

**Problem**: Wrong rule is matching

**Solutions**:
1. Increase priority of correct rule
2. Use tiebreaker by updating `data_criacao` (make it older)
3. Add more specific criteria to block other rules

**Problem**: "NO_MATCH" for everything

**Solutions**:
1. Verify rules exist: `SELECT COUNT(*) FROM regras_de_classificacao WHERE ativo = true;`
2. Verify database connection is working
3. Check application logs for errors

---

## Best Practices

### 1. Use Meaningful Names

```sql
-- Good: Clear, descriptive name
'Laptop Electronic Devices Rule'

-- Bad: Unclear what this does
'rule123' or 'test'
```

### 2. Group Rules by Specificity

```sql
-- Create rules from specific → general
INSERT VALUES ('Gaming Laptop', 150, ...);  -- Very specific
INSERT VALUES ('All Laptops', 100, ...);    -- Specific
INSERT VALUES ('All Computers', 50, ...);   -- General
INSERT VALUES ('Electronics', 10, ...);     -- Very general
```

### 3. Document Rule Purpose in Comments (Use Description Field)

```sql
-- Use the rule name to document purpose
INSERT INTO regras_de_classificacao (
    nome,  -- Include: WHY this rule exists, WHO requested it
    ...
) VALUES (
    'Laptop Rule (High margin items, created 2025-01-15)',
    ...
);
```

### 4. Test Before Activating

```sql
-- Create with ativo = false
INSERT INTO regras_de_classificacao (
    nome, prioridade, resultado_classificacao,
    criterio_palavras_chave, ativo
) VALUES ('Test Rule', 50, 'TEST', 'test_keyword', false);

-- Query audit log for products that WOULD match
-- Then set ativo = true when confident
UPDATE regras_de_classificacao SET ativo = true
WHERE nome = 'Test Rule';
```

### 5. Avoid Overlapping Keywords

```sql
-- Bad: These will conflict
'laptop' - matches "laptop"
'lap'    - also matches "laptop"

-- Better: Be specific, or adjust priorities
'gaming laptop'  - priority 100
'laptop'         - priority 50
```

### 6. Use Ranges Wisely

```sql
-- Size ranges should be non-overlapping or have priority layers
-- Good:
INSERT VALUES ('Small Items', 50, 'SMALL', NULL, 0.5, ...);
INSERT VALUES ('Large Items', 40, 'LARGE', NULL, 1.5, ...);
-- Small (0.0-0.5), Large (0.5+) - clear boundary

-- Better: Use both min and max for precision
INSERT VALUES ('Small Items', 50, 'SMALL', NULL, 0.0, 0.5, ...);
INSERT VALUES ('Medium Items', 40, 'MEDIUM', NULL, 0.5, 2.0, ...);
INSERT VALUES ('Large Items', 30, 'LARGE', NULL, 2.0, NULL, ...);
```

### 7. Review Audit Logs Regularly

```sql
-- Monthly rule effectiveness review
SELECT
    id_regra,
    resultado_classificacao,
    COUNT(*) as matches,
    AVG(tempo_avaliacao_ms) as avg_time
FROM auditoria_classificacao
WHERE data_classificacao > NOW() - INTERVAL '30 days'
GROUP BY id_regra, resultado_classificacao
ORDER BY matches DESC;
```

### 8. Archive Old Rules

```sql
-- Don't delete rules, deactivate them (keeps audit history intact)
UPDATE regras_de_classificacao SET ativo = false
WHERE data_criacao < NOW() - INTERVAL '1 year'
AND nome LIKE '%deprecated%';
```

### 9. Use Version Control for Rules

```sql
-- Track rule changes manually
UPDATE regras_de_classificacao SET
    nome = 'Laptop Rule v2 (Updated 2025-01-15)',
    criterio_palavras_chave = 'gaming laptop'
WHERE id = 42;

-- Or keep old rule deactivated
UPDATE regras_de_classificacao SET ativo = false WHERE id = 42;
INSERT INTO regras_de_classificacao (...) VALUES (...);  -- New rule
```

---

## Contact & Support

- **Questions about rules?** Check the audit logs first
- **Need to modify a rule?** Use UPDATE statements (doesn't require code change)
- **Rule not working?** See "Debugging Classifications" section above
- **System issues?** Check application logs and database connectivity

---

## Quick Reference

| Task | SQL |
|------|-----|
| Create a rule | `INSERT INTO regras_de_classificacao (...)` |
| Activate a rule | `UPDATE regras_de_classificacao SET ativo = true WHERE id = XX;` |
| Deactivate a rule | `UPDATE regras_de_classificacao SET ativo = false WHERE id = XX;` |
| Change priority | `UPDATE regras_de_classificacao SET prioridade = 75 WHERE id = XX;` |
| View all active rules | `SELECT * FROM regras_de_classificacao WHERE ativo = true ORDER BY prioridade DESC;` |
| View a product's history | `SELECT * FROM auditoria_classificacao WHERE id_produto = 'PROD123' ORDER BY data_classificacao DESC;` |
| See why no match | `SELECT * FROM auditoria_classificacao WHERE id_regra IS NULL ORDER BY data_classificacao DESC LIMIT 20;` |
| Rule performance stats | `SELECT id_regra, COUNT(*), AVG(tempo_avaliacao_ms) FROM auditoria_classificacao GROUP BY id_regra;` |

