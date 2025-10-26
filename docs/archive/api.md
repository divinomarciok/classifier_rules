# API Documentation - Rule Engine Core

## Overview

The classifier engine provides a data-driven product classification system. All classification logic is stored in the database (`regras_de_classificacao` table), allowing rules to be managed without code changes.

## Table of Contents

1. [RuleEngine](#ruleengine)
2. [Matcher](#matcher)
3. [Evaluator](#evaluator)
4. [AuditLog](#auditlog)
5. [Models](#models)
6. [Error Handling](#error-handling)
7. [Examples](#examples)
8. [Performance Considerations](#performance-considerations)

---

## RuleEngine

Main entry point for product classification. Handles loading rules, evaluation, priority resolution, and audit logging.

### Class: `RuleEngine`

```python
from classifier.engine import RuleEngine

engine = RuleEngine(db_connection=None)
```

**Parameters:**
- `db_connection` (optional): Database connection object. If not provided, attempts to connect using `Config.get_db_connection()`.

**Attributes:**
- `_rules_cache`: Internal cache of loaded rules (dict)
- `_cache_timestamp`: When rules were last loaded (datetime)
- `db_connection`: Active database connection

---

### Method: `evaluate(product_input)`

Evaluates a product against all active rules and returns the classification result.

**Signature:**
```python
def evaluate(product_input: dict | Product) -> ClassificationResult
```

**Parameters:**
- `product_input`: Either a dictionary with product data or a `Product` object
  - Required fields: `description` (str), `ncm` (str)
  - Optional fields: `size` (float), `quantity` (int), `category` (str), or any custom fields
  - Dictionary example: `{"description": "laptop", "ncm": "84713090", "size": 0.5}`

**Returns:**
- `ClassificationResult` object with:
  - `success` (bool): Whether a rule matched
  - `classification` (str): The classification result (or "NO_MATCH")
  - `rule_id` (int): ID of the matching rule (or None)
  - `rule_name` (str): Name of the matching rule (or "UNCLASSIFIED")
  - `priority` (int): Priority of the matching rule
  - `matched_criteria` (list): Criterion names that matched
  - `evaluation_time_ms` (int): Time taken to evaluate (milliseconds)
  - `audit_id` (int): ID of the audit log entry

**Raises:**
- `ValueError`: If product is missing required fields (description, ncm)
- `DatabaseError`: If rules cannot be loaded from database
- `Exception`: Any unexpected database or runtime errors

**Example:**
```python
engine = RuleEngine()

# Using dictionary
result = engine.evaluate({
    "description": "Dell laptop computer",
    "ncm": "84713090"
})

# Using Product object
from classifier.models import Product
product = Product(description="Dell laptop", ncm="84713090")
result = engine.evaluate(product)

print(f"Classification: {result.classification}")  # ELECTRONICS
print(f"Rule ID: {result.rule_id}")  # 42
print(f"Evaluation time: {result.evaluation_time_ms}ms")  # 125
```

---

### Method: `get_rules()`

Retrieves all active rules from the database, with caching.

**Signature:**
```python
def get_rules() -> list[Rule]
```

**Returns:**
- List of `Rule` objects representing active rules

**Behavior:**
- First call: Loads rules from database
- Subsequent calls: Returns cached rules (until cache expires)
- Cache TTL: 1 hour (default)

**Example:**
```python
engine = RuleEngine()
rules = engine.get_rules()

for rule in rules:
    print(f"Rule {rule.id}: {rule.nome} (priority: {rule.prioridade})")
```

---

### Method: `refresh_cache()`

Forces reload of rules from database, clearing the cache.

**Signature:**
```python
def refresh_cache() -> int
```

**Returns:**
- Number of rules loaded

**Use Case:** After updating rules in the database, refresh the cache to pick up changes without restarting.

**Example:**
```python
engine = RuleEngine()

# Rules have been updated in database
engine.refresh_cache()  # Reloads all rules

result = engine.evaluate({"description": "test", "ncm": "99999999"})
```

---

## Matcher

Responsible for checking if a product matches a specific rule's criteria.

### Class: `Matcher`

No instantiation needed; all methods are static.

```python
from classifier.matcher import Matcher
```

---

### Static Method: `matches_all_criteria(rule, product)`

Checks if a product matches ALL criteria specified in a rule (AND logic).

**Signature:**
```python
@staticmethod
def matches_all_criteria(rule: Rule, product: Product) -> bool
```

**Parameters:**
- `rule`: Rule object with optional criteria fields
- `product`: Product object with data

**Returns:**
- `True` if ALL specified criteria match
- `False` if ANY criterion fails to match

**Criteria Types (evaluated in order):**
1. **Keyword Criteria** (`criterio_palavras_chave`):
   - Substring search (case-insensitive)
   - Searches product description
   - Example: rule with "laptop" matches "DELL LAPTOP Computer"

2. **NCM Criteria** (`criterio_ncm`):
   - Wildcard pattern matching
   - Supports `*` as wildcard (matches any characters)
   - Example: rule with "8471*" matches NCM "84713090"

3. **Size Criteria** (`criterio_tamanho_min`, `criterio_tamanho_max`):
   - Range matching (inclusive)
   - Product.size must be >= min and <= max
   - Example: min=0.5, max=2.0 matches size=1.5

4. **Quantity Criteria** (`criterio_quantidade_min`, `criterio_quantidade_max`):
   - Range matching (inclusive)
   - Product.quantity must be >= min and <= max
   - Example: min=1, max=100 matches quantity=50

5. **Category Criteria** (`criterio_categoria`):
   - Exact match (case-insensitive)
   - Compares against product.category field
   - Example: rule with "ELECTRONICS" matches product.category="electronics"

**Logic:**
- Only criteria specified in the rule are checked
- All specified criteria must match (AND logic)
- Unspecified criteria are ignored
- Returns False on first mismatch (short-circuit evaluation)

**Example:**
```python
from classifier.matcher import Matcher
from classifier.models import Rule, Product

rule = Rule(
    id=1,
    prioridade=50,
    nome="Laptop Rule",
    ativo=True,
    resultado_classificacao="ELECTRONICS",
    criterio_palavras_chave="laptop",
    criterio_tamanho_max=2.0
)

product = Product(
    description="Dell laptop computer",
    ncm="84713090",
    size=1.5
)

matches = Matcher.matches_all_criteria(rule, product)
# Returns: True (matches keyword AND size)

product2 = Product(
    description="Desktop computer",
    ncm="84713090",
    size=1.5
)

matches = Matcher.matches_all_criteria(rule, product2)
# Returns: False (doesn't match keyword)
```

---

## Evaluator

Responsible for finding matching rules and selecting the winner based on priority.

### Class: `Evaluator`

No instantiation needed; all methods are static.

```python
from classifier.evaluator import Evaluator
```

---

### Static Method: `get_matching_rules(rules, product)`

Finds all rules that match a product's criteria.

**Signature:**
```python
@staticmethod
def get_matching_rules(rules: list[Rule], product: Product) -> list[Rule]
```

**Parameters:**
- `rules`: List of active Rule objects
- `product`: Product object to match against

**Returns:**
- List of Rule objects that match the product (may be empty)

**Example:**
```python
from classifier.evaluator import Evaluator

matching_rules = Evaluator.get_matching_rules(all_rules, product)
print(f"Found {len(matching_rules)} matching rules")
```

---

### Static Method: `select_winner(matching_rules)`

Selects the best matching rule based on priority and tiebreaker.

**Signature:**
```python
@staticmethod
def select_winner(matching_rules: list[Rule]) -> Rule | None
```

**Parameters:**
- `matching_rules`: List of Rule objects that match a product

**Returns:**
- The winning Rule object, or None if list is empty

**Selection Logic:**
1. **Primary**: Highest `prioridade` value wins
2. **Tiebreaker**: If multiple rules have same priority, oldest rule by `data_criacao` wins (FIFO)

**Determinism:**
- Same input always produces same output
- No randomization or timestamp-dependent logic
- Allows consistent classification across runs

**Example:**
```python
from classifier.evaluator import Evaluator

winning_rule = Evaluator.select_winner(matching_rules)
if winning_rule:
    print(f"Winner: Rule {winning_rule.id} (priority: {winning_rule.prioridade})")
```

---

## AuditLog

Records and queries classification decisions for compliance and analysis.

### Class: `AuditLog`

```python
from classifier.audit import AuditLog

audit = AuditLog(db_connection)
```

**Parameters:**
- `db_connection`: Database connection object

---

### Method: `record(rule_id, product_data, matched_criteria, classification_result, evaluation_time_ms, user='system')`

Records a classification decision to the audit log.

**Signature:**
```python
def record(
    rule_id: int | None,
    product_data: dict,
    matched_criteria: list[str],
    classification_result: str,
    evaluation_time_ms: int,
    user: str = 'system'
) -> int
```

**Parameters:**
- `rule_id`: ID of the matching rule (or None if no match)
- `product_data`: Product information (dict with `id` and `description`)
- `matched_criteria`: List of criterion names that matched
- `classification_result`: The resulting classification
- `evaluation_time_ms`: Milliseconds taken to evaluate
- `user`: User or system identifier performing the classification (default: 'system')

**Returns:**
- `int`: ID of the inserted audit log entry

**Raises:**
- `Exception`: If database insert fails

**Stored Fields:**
- `id`: Auto-generated audit entry ID
- `id_regra`: Rule ID (nullable)
- `id_produto`: Product ID
- `descricao_produto`: Product description
- `resultado_classificacao`: Classification result
- `data_classificacao`: Timestamp (auto-set to now)
- `usuario`: User identifier
- `criterios_correspondentes`: Pipe-separated criteria (e.g., "keyword|ncm|size")
- `tempo_avaliacao_ms`: Evaluation time in milliseconds

**Example:**
```python
audit = AuditLog(db_connection)

audit_id = audit.record(
    rule_id=42,
    product_data={'id': 'PROD001', 'description': 'Dell laptop'},
    matched_criteria=['criterio_palavras_chave', 'criterio_tamanho_max'],
    classification_result='ELECTRONICS',
    evaluation_time_ms=125,
    user='analyst1'
)
print(f"Recorded audit entry: {audit_id}")
```

---

### Method: `get_product_history(product_id, limit=100)`

Retrieves all classifications for a specific product.

**Signature:**
```python
def get_product_history(product_id: str, limit: int = 100) -> list[dict]
```

**Parameters:**
- `product_id`: Product ID to query
- `limit`: Maximum number of entries to return (default: 100)

**Returns:**
- List of audit entry dictionaries in reverse chronological order (most recent first)

**Returned Fields:**
- `id`: Audit entry ID
- `id_regra`: Rule ID (nullable)
- `id_produto`: Product ID
- `descricao_produto`: Product description
- `resultado_classificacao`: Classification result
- `data_classificacao`: Timestamp
- `usuario`: User identifier
- `criterios_correspondentes`: Matched criteria
- `tempo_avaliacao_ms`: Evaluation time

**Example:**
```python
audit = AuditLog(db_connection)

history = audit.get_product_history('PROD001', limit=50)
for entry in history:
    print(f"{entry['data_classificacao']}: {entry['resultado_classificacao']} (rule {entry['id_regra']})")
```

---

### Method: `get_rule_statistics(rule_id)`

Retrieves aggregated statistics for a rule.

**Signature:**
```python
def get_rule_statistics(rule_id: int) -> dict
```

**Parameters:**
- `rule_id`: Rule ID to analyze

**Returns:**
- Dictionary with statistics:
  - `times_applied`: How many times the rule matched
  - `last_applied`: When rule was last used (datetime)
  - `avg_evaluation_time_ms`: Average evaluation time (float)
  - `min_evaluation_time_ms`: Fastest evaluation (int)
  - `max_evaluation_time_ms`: Slowest evaluation (int)
- Returns empty dict if rule has no audit entries

**Example:**
```python
audit = AuditLog(db_connection)

stats = audit.get_rule_statistics(42)
if stats:
    print(f"Rule 42 has been applied {stats['times_applied']} times")
    print(f"Average evaluation time: {stats['avg_evaluation_time_ms']:.1f}ms")
```

---

### Method: `get_no_match_classifications(limit=100)`

Finds all products that didn't match any rule.

**Signature:**
```python
def get_no_match_classifications(limit: int = 100) -> list[dict]
```

**Parameters:**
- `limit`: Maximum number of entries to return (default: 100)

**Returns:**
- List of audit entries where no rule matched (id_regra is NULL)

**Use Case:** Identify products that need new classification rules.

**Example:**
```python
audit = AuditLog(db_connection)

no_matches = audit.get_no_match_classifications(limit=100)
print(f"Found {len(no_matches)} products that didn't match any rule")

for entry in no_matches:
    print(f"Product {entry['id_produto']}: {entry['descricao_produto']}")
```

---

## Models

Data models used throughout the system.

### Class: `Product`

Represents a product to be classified.

**Signature:**
```python
from classifier.models import Product

product = Product(
    description: str,
    ncm: str,
    size: float | None = None,
    quantity: int | None = None,
    category: str | None = None,
    **kwargs  # Any additional fields
)
```

**Parameters:**
- `description`: Product description (required)
- `ncm`: NCM code (required)
- `size`: Physical size (optional, for range matching)
- `quantity`: Quantity ordered (optional, for range matching)
- `category`: Product category (optional, for category matching)
- `**kwargs`: Any additional custom fields

**Attributes:**
- `description`: Stored as provided
- `ncm`: Stored as provided
- `size`: None if not provided
- `quantity`: None if not provided
- `category`: None if not provided
- Custom fields accessible via `get_field(name)`

**Methods:**
- `get_field(field_name)`: Get value of any field (including custom ones)
- Returns None if field not found

**Example:**
```python
product = Product(
    description="Dell laptop computer",
    ncm="84713090",
    size=1.5,
    quantity=10,
    supplier="Dell Inc"  # Custom field
)

print(product.description)  # Dell laptop computer
print(product.get_field('supplier'))  # Dell Inc
```

---

### Class: `Rule`

Represents a classification rule from the database.

**Signature:**
```python
from classifier.models import Rule
from datetime import datetime

rule = Rule(
    id: int,
    prioridade: int,
    nome: str,
    ativo: bool,
    resultado_classificacao: str,
    criterio_palavras_chave: str | None = None,
    criterio_ncm: str | None = None,
    criterio_tamanho_min: float | None = None,
    criterio_tamanho_max: float | None = None,
    criterio_quantidade_min: int | None = None,
    criterio_quantidade_max: int | None = None,
    criterio_categoria: str | None = None,
    data_criacao: datetime | None = None
)
```

**Parameters:**
- `id`: Unique rule identifier
- `prioridade`: Priority value (higher = evaluated first)
- `nome`: Human-readable rule name
- `ativo`: Whether rule is active
- `resultado_classificacao`: The classification to apply if rule matches
- `criterio_*`: Optional matching criteria

**Attributes:** Same as parameters

---

### Class: `ClassificationResult`

Represents the result of a product evaluation.

**Signature:**
```python
from classifier.models import ClassificationResult

result = ClassificationResult(
    success: bool,
    classification: str,
    rule_id: int | None,
    rule_name: str,
    priority: int,
    matched_criteria: list[str],
    evaluation_time_ms: int,
    audit_id: int | None
)
```

**Attributes:**
- `success`: Whether a rule matched
- `classification`: Result (or "NO_MATCH")
- `rule_id`: ID of matching rule (or None)
- `rule_name`: Name of matching rule (or "UNCLASSIFIED")
- `priority`: Priority of matching rule
- `matched_criteria`: List of criteria that matched
- `evaluation_time_ms`: Time taken (milliseconds)
- `audit_id`: ID of audit log entry (if recorded)

**Example:**
```python
if result.success:
    print(f"Matched rule {result.rule_id}: {result.rule_name}")
    print(f"Classification: {result.classification}")
else:
    print("No rule matched (NO_MATCH)")
```

---

## Error Handling

### Exception Classes

**ValueError**
- Raised when product validation fails (missing description or ncm)
- Catch to handle invalid input data

**DatabaseError**
- Raised when database connection fails or queries error
- Catch to handle database connectivity issues

**Generic Exception**
- May be raised for unexpected runtime errors
- Log and notify for debugging

### Error Handling Pattern

```python
from classifier.engine import RuleEngine

engine = RuleEngine()

try:
    result = engine.evaluate({"description": "test"})  # Missing ncm
except ValueError as e:
    print(f"Invalid product: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Strategy

For transient database errors, implement exponential backoff:

```python
import time

def evaluate_with_retry(engine, product, max_retries=3):
    for attempt in range(max_retries):
        try:
            return engine.evaluate(product)
        except DatabaseError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                time.sleep(wait_time)
            else:
                raise
```

---

## Examples

### Complete Evaluation Workflow

```python
from classifier.engine import RuleEngine
from classifier.models import Product

# Initialize engine (connects to database)
engine = RuleEngine()

# Create product
product = Product(
    description="Gaming laptop with RTX 4090",
    ncm="84713090",
    size=0.8,
    quantity=5
)

# Evaluate
result = engine.evaluate(product)

# Use result
if result.success:
    print(f"Classification: {result.classification}")
    print(f"Rule: {result.rule_name} (priority {result.priority})")
    print(f"Evaluation took {result.evaluation_time_ms}ms")
    print(f"Audit ID: {result.audit_id}")
else:
    print("No matching rule found")

# Query audit history
from classifier.audit import AuditLog
audit = AuditLog(engine.db_connection)
history = audit.get_product_history(product_id)
for entry in history:
    print(f"{entry['data_classificacao']}: {entry['resultado_classificacao']}")
```

### Batch Processing

```python
from classifier.engine import RuleEngine

engine = RuleEngine()
products = [
    {"description": "Laptop", "ncm": "84713090"},
    {"description": "Desktop", "ncm": "84713090"},
    {"description": "Phone", "ncm": "85171200"}
]

results = []
for product in products:
    result = engine.evaluate(product)
    results.append({
        'product': product,
        'classification': result.classification,
        'rule_id': result.rule_id
    })

for r in results:
    print(f"{r['product']['description']} → {r['classification']}")
```

### Analyzing Rule Performance

```python
from classifier.audit import AuditLog

audit = AuditLog(db_connection)

# Get stats for all top rules
for rule_id in [1, 2, 3, 42, 100]:
    stats = audit.get_rule_statistics(rule_id)
    if stats:
        print(f"Rule {rule_id}: {stats['times_applied']} times, "
              f"avg {stats['avg_evaluation_time_ms']:.1f}ms")
```

---

## Performance Considerations

### Evaluation Performance

**Target:** < 500ms for 95th percentile (per specification SC-003)

**Factors:**
1. **Rule Count**: More rules = slower evaluation (linear O(n))
2. **Database Connectivity**: First evaluation takes longer (connection overhead)
3. **Caching**: Subsequent evaluations use cached rules (fast)
4. **Criteria Complexity**: More criteria = slower matching

**Optimization Tips:**

1. **Cache Warming**: Load rules once, reuse engine instance
   ```python
   engine = RuleEngine()
   engine.refresh_cache()  # Pre-load rules

   for product in many_products:
       result = engine.evaluate(product)  # Uses cached rules
   ```

2. **Connection Pooling**: Use connection pool for concurrent requests
   ```python
   # Use production-grade connection pool (not included in core)
   # e.g., psycopg2.pool.SimpleConnectionPool
   ```

3. **Batch Operations**: Process multiple products efficiently
   ```python
   results = []
   for product in products:
       results.append(engine.evaluate(product))
   ```

4. **Database Indexes**: Ensure indexes on frequently queried columns
   - `regras_de_classificacao(ativo, prioridade, data_criacao)`
   - `auditoria_classificacao(id_regra, id_produto, data_classificacao)`

5. **Monitoring**: Track evaluation times
   ```python
   import statistics
   times = [result.evaluation_time_ms for result in results]
   print(f"p95: {statistics.quantiles(times, n=20)[18]}")
   ```

### Memory Considerations

**Rule Cache:** ~10-20KB per rule (typical)
- 10,000 rules ≈ 100-200MB
- Acceptable for server applications

**Audit Logging:** ~500 bytes per entry
- Keep audit database healthy with periodic archiving
- No performance impact on evaluation

---

## References

- **Specification**: `specs/001-rule-engine/spec.md`
- **Data Model**: `specs/001-rule-engine/data-model.md`
- **Contract API**: `specs/001-rule-engine/contracts/rule_engine_api.md`
- **Business Guide**: `docs/rules_guide.md`
- **Troubleshooting**: `docs/troubleshooting.md`
