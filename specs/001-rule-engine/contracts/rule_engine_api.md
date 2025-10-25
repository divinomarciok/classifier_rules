# RuleEngine API Contract

**Branch**: `001-rule-engine`
**Created**: 2025-10-25
**Purpose**: Define the interface and expected behavior of the RuleEngine

## Library API (Python)

### RuleEngine Class

Main entry point for rule evaluation.

#### Constructor

```python
from classifier.engine import RuleEngine

engine = RuleEngine(db_connection=None, cache_rules=True)
```

**Parameters**:
- `db_connection` (optional): Pre-configured database connection. If None, uses `.env` configuration
- `cache_rules` (optional, default=True): Cache active rules in memory for performance

**Raises**:
- `ConfigError`: If `.env` not found and no connection provided
- `DatabaseError`: If database connection fails

#### evaluate()

Evaluate a product against all active rules and return the matching classification.

```python
result = engine.evaluate(product_data, user=None)
```

**Parameters**:
- `product_data` (dict, required): Product information
  - `id` (str, optional): Product identifier
  - `description` (str, optional): Product description
  - `ncm` (str, optional): NCM code
  - `size` (float, optional): Product size
  - `quantity` (int, optional): Product quantity
  - `category` (str, optional): Product category
  - Other fields as needed (arbitrary key-value pairs)
- `user` (str, optional): System user/process name for audit logging

**Returns** (dict):
```python
{
    "classification": "ELECTRONICS",        # Result classification code
    "rule_id": 1,                           # ID of matching rule
    "rule_name": "Laptop Rule",             # Name of matching rule
    "priority": 100,                        # Priority of rule
    "matched_criteria": [                   # Which criteria matched
        "keywords: laptop, computer"
    ],
    "evaluation_time_ms": 45,               # Time to evaluate
    "success": True,                        # Evaluation succeeded
    "message": None                         # Error message if failed
}
```

**Special Cases**:
- If NO rule matches: `classification = "NO_MATCH"`, `rule_id = None`
- If error occurs: `success = False`, `message = "error details"`

**Raises**:
- `ProductError`: If product_data is invalid
- `DatabaseError`: If rule lookup fails
- `EvaluationError`: If evaluation fails

#### get_rules()

Fetch all active rules from database.

```python
rules = engine.get_rules(active_only=True)
```

**Parameters**:
- `active_only` (bool, default=True): Only return active rules

**Returns** (list of dict):
```python
[
    {
        "id": 1,
        "prioridade": 100,
        "nome": "Laptop Rule",
        "ativo": True,
        "criterio_palavras_chave": "laptop,computer",
        "criterio_ncm": None,
        "criterio_tamanho_min": None,
        "criterio_tamanho_max": None,
        "criterio_quantidade_min": None,
        "criterio_quantidade_max": None,
        "criterio_categoria": None,
        "resultado_classificacao": "ELECTRONICS",
        "data_criacao": "2025-10-25T10:00:00",
        "data_atualizacao": "2025-10-25T10:00:00"
    },
    ...
]
```

#### refresh_cache()

Reload rules from database (for when rules are updated externally).

```python
engine.refresh_cache()
```

**Returns**: None

**Raises**:
- `DatabaseError`: If rule reload fails

---

## Matcher API

Internal API for checking if a product matches criteria.

### Matcher.matches_all_criteria()

Check if product matches ALL criteria in a rule.

```python
from classifier.matcher import Matcher

matcher = Matcher()
matches = matcher.matches_all_criteria(product, rule)
```

**Parameters**:
- `product` (dict): Product data
- `rule` (dict): Rule with criteria fields

**Returns**: bool (True if all criteria match, False otherwise)

#### Criteria Matching Logic

**Keywords** (`criterio_palavras_chave`):
- Comma-separated list of keywords
- Match: ANY keyword appears (case-insensitive) in product description
- Example: "laptop,computer" matches description containing "laptop" or "computer"

**NCM** (`criterio_ncm`):
- Supports wildcard patterns (e.g., "8471*")
- Match: Product NCM matches pattern (begins with, for wildcards)
- Example: "8471*" matches "84713090", "84710000", etc.

**Size Range** (`criterio_tamanho_min`, `criterio_tamanho_max`):
- Both optional; if set, BOTH must match
- Match: `criterio_tamanho_min <= product.size <= criterio_tamanho_max`

**Quantity Range** (`criterio_quantidade_min`, `criterio_quantidade_max`):
- Both optional; if set, BOTH must match
- Match: `criterio_quantidade_min <= product.quantity <= criterio_quantidade_max`

**Category** (`criterio_categoria`):
- Exact string match (case-sensitive)
- Match: `product.category == criterio_categoria`

---

## Evaluator API

Internal API for selecting winner rule when multiple match.

### Evaluator.select_winner()

Select highest-priority matching rule; tiebreak by creation date.

```python
from classifier.evaluator import Evaluator

evaluator = Evaluator()
winner = evaluator.select_winner(matching_rules)
```

**Parameters**:
- `matching_rules` (list of dict): Rules that matched product

**Returns** (dict): Single winning rule (highest priority)

**Tiebreaker Logic**:
1. Sort by `prioridade DESC` (highest first)
2. If tied, sort by `data_criacao ASC` (oldest first)
3. Return first rule

---

## AuditLog API

Internal API for recording classification decisions.

### AuditLog.record()

Create an audit log entry for a classification decision.

```python
from classifier.audit import AuditLog

audit = AuditLog()
entry_id = audit.record(
    rule_id=1,
    product_data={'id': 'PROD_001', ...},
    matched_criteria=['keywords: laptop'],
    classification_result='ELECTRONICS',
    evaluation_time_ms=45,
    user='system'
)
```

**Parameters**:
- `rule_id` (int or None): Rule ID that was applied (None if no match)
- `product_data` (dict): Product that was classified
- `matched_criteria` (list): Which criteria matched
- `classification_result` (str): Classification result code
- `evaluation_time_ms` (int): Evaluation time
- `user` (str, optional): System user/process name

**Returns**: int (audit log entry ID)

**Raises**:
- `DatabaseError`: If insert fails

### AuditLog.get_product_history()

Get classification history for a product.

```python
history = audit.get_product_history(product_id, limit=100)
```

**Parameters**:
- `product_id` (str): Product ID to look up
- `limit` (int, default=100): Max results to return

**Returns** (list of dict):
```python
[
    {
        "id": 1001,
        "rule_id": 1,
        "rule_name": "Laptop Rule",
        "product_id": "PROD_001",
        "classification": "ELECTRONICS",
        "criteria_matched": "keywords: laptop",
        "timestamp": "2025-10-25T10:15:30",
        "evaluation_time_ms": 45
    },
    ...
]
```

### AuditLog.get_rule_statistics()

Get performance statistics for a rule.

```python
stats = audit.get_rule_statistics(rule_id)
```

**Parameters**:
- `rule_id` (int): Rule ID

**Returns** (dict):
```python
{
    "rule_id": 1,
    "rule_name": "Laptop Rule",
    "times_applied": 1250,
    "last_applied": "2025-10-25T14:30:00",
    "avg_evaluation_time_ms": 42,
    "min_evaluation_time_ms": 15,
    "max_evaluation_time_ms": 250
}
```

---

## Error Handling

### Error Types

**ConfigError**: Configuration missing or invalid
```python
try:
    engine = RuleEngine()
except ConfigError as e:
    print(f"Configuration error: {e}")
```

**DatabaseError**: Database connection or query failed
```python
try:
    result = engine.evaluate(product)
except DatabaseError as e:
    print(f"Database error: {e}")
    # Implement fallback behavior
```

**ProductError**: Invalid product data
```python
try:
    result = engine.evaluate(invalid_product)
except ProductError as e:
    print(f"Invalid product: {e}")
```

**EvaluationError**: Evaluation logic failed
```python
try:
    result = engine.evaluate(product)
except EvaluationError as e:
    print(f"Evaluation error: {e}")
```

---

## Example Usage

### Simple Classification

```python
from classifier.engine import RuleEngine

engine = RuleEngine()

product = {
    'id': 'PROD_001',
    'description': 'Apple MacBook Pro 16 laptop',
    'ncm': '84713090'
}

result = engine.evaluate(product, user='classification_service')

if result['success']:
    print(f"Classification: {result['classification']}")
    print(f"Applied rule: {result['rule_name']} (ID: {result['rule_id']})")
else:
    print(f"Error: {result['message']}")
```

### Batch Classification

```python
engine = RuleEngine()

products = [
    {'id': 'P1', 'description': 'laptop computer', 'ncm': '84713090'},
    {'id': 'P2', 'description': 'office chair', 'ncm': '94010000'},
    {'id': 'P3', 'description': 'USB cable', 'ncm': '85444290'},
]

for product in products:
    result = engine.evaluate(product, user='batch_import')
    print(f"{product['id']}: {result['classification']}")
```

### With Error Handling

```python
from classifier.engine import RuleEngine
from classifier.exceptions import DatabaseError

engine = RuleEngine()

try:
    result = engine.evaluate(product, user='service')
    classification = result['classification']
except DatabaseError:
    # Fallback to default classification
    classification = 'UNKNOWN'
    print("Database unavailable, using fallback")
```
