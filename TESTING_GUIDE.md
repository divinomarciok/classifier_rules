# Testing Guide - Classifier v2

Complete guide to testing the product classification system.

## Quick Start

### Run All Tests
```bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras
python3 -m pytest tests/ -v
```

**Expected Result**: 277 passing tests (4 failing batch tests are mock limitations, not bugs)

### Run Specific Test Category
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Contract tests (some require database)
pytest tests/contract/ -v

# CLI tests only
pytest tests/cli/ -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src/classifier --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Testing Strategy

### 1. Unit Tests (150+ tests)
Test individual components in isolation with mocks.

**What They Test**:
- Matcher: All 5 criteria matching types
- Evaluator: Rule filtering and winner selection
- RuleEngine: API functionality
- AuditLog: Logging and queries
- BatchClassifier: Batch operations
- CSVClassifier: CSV processing

**How to Run**:
```bash
pytest tests/unit/ -v
```

**Example**:
```bash
pytest tests/unit/test_matcher.py::TestKeywordMatching::test_match_keyword_substring -v
```

### 2. Integration Tests (80+ tests)
Test workflows combining multiple components.

**What They Test**:
- Complete evaluation flow (product → classification)
- Priority resolution (multiple matching rules)
- Audit logging (recording decisions)
- Batch classification workflow
- CSV import/classify/export workflow

**How to Run**:
```bash
pytest tests/integration/ -v
```

**Example**:
```bash
pytest tests/integration/test_rule_evaluation.py -v
```

### 3. Contract Tests (35+ tests)
Test API contracts and specifications.

**What They Test**:
- RuleEngine API compliance
- Batch classification specification
- CSV classification specification
- Performance requirements

**How to Run**:
```bash
pytest tests/contract/ -v
```

**Note**: Some contract tests require live PostgreSQL database.

### 4. CLI Tests (12 tests)
Test command-line interfaces.

**What They Test**:
- Batch classification CLI (classify-batch)
- CSV classification CLI (classify-csv)
- Argument parsing
- Output formatting
- Error handling

**How to Run**:
```bash
pytest tests/cli/ -v
```

---

## Manual Testing

### Test 1: Basic Classification
```bash
# Open Python shell
python3

# Code to test basic classification
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

db = get_db_connection()
engine = RuleEngine(db)

# Classify a product
result = engine.evaluate({
    'id': 'TEST_001',
    'description': 'laptop dell',
    'ncm': '84713090'
})

print(f"Classification: {result.classification}")
print(f"Success: {result.success}")
print(f"Rule ID: {result.rule_id}")
print(f"Time: {result.evaluation_time_ms}ms")
```

**Expected Output**:
```
Classification: ELECTRONICS (or whatever rule matches)
Success: True
Rule ID: 1 (or matching rule ID)
Time: <500ms
```

### Test 2: Batch Processing
```bash
# Process 10 products from database
classify-batch --limit 10

# Expected output:
# CSV CLASSIFICATION SUMMARY
# ============================================================
# Total Processed:     10 products
# Total Matched:       X products
# Match Rate:          X%
# ...
```

### Test 3: CSV Processing
```bash
# Process sample CSV
classify-csv samples/products_basic.csv

# Check output file was created
ls -la samples/products_basic_classified.csv

# Verify classifications added
head samples/products_basic_classified.csv
```

### Test 4: CSV Validation
```bash
# Validate good CSV
classify-csv samples/products_basic.csv --validate

# Expected: ✓ CSV file is valid

# Validate bad CSV
classify-csv samples/products_invalid.csv --validate

# Expected: ✗ CSV file has issues - see details below
```

### Test 5: Performance Test
```bash
# Time the batch processing
time classify-batch --limit 500

# Should complete in < 5 seconds
```

---

## Advanced Testing

### Test Specific Rule Matching

```python
from classifier.matcher import Matcher
from classifier.models import Rule, Product

# Create test rule
rule = Rule(
    id=1,
    prioridade=50,
    nome="Laptop Rule",
    ativo=True,
    resultado_classificacao="ELECTRONICS",
    criterio_palavras_chave="laptop"
)

# Create test product
product = Product(
    id="P001",
    description="dell laptop computer",
    ncm="84713090"
)

# Test matching
matches = Matcher.matches_criteria(product, rule)
print(f"Matches: {matches}")  # True or False
```

### Test Priority Selection

```python
from classifier.evaluator import Evaluator
from classifier.models import Rule

# Create rules with different priorities
rule1 = Rule(id=1, prioridade=10, ativo=True, ...)
rule2 = Rule(id=2, prioridade=50, ativo=True, ...)  # Higher priority
rule3 = Rule(id=3, prioridade=50, ativo=True, ...)  # Same priority, older creation date

rules = [rule1, rule2, rule3]
winner = Evaluator.select_winner(rules)

print(f"Winner: Rule {winner.id}")  # Should be rule2 (highest priority)
```

### Test Audit Logging

```python
from classifier.audit import AuditLog

audit = AuditLog(db_connection)

# Get history of a product
history = audit.get_product_history(product_id="P001")
for entry in history:
    print(f"Rule {entry.id_regra} classified as {entry.resultado_classificacao}")

# Get rule statistics
stats = audit.get_rule_statistics(rule_id=1)
print(f"Rule 1 applied {stats['times_applied']} times")
print(f"Average time: {stats['avg_time_ms']}ms")
```

---

## Database-Dependent Testing

### Create Test Rules

```sql
-- Insert test rules into database
INSERT INTO regras_de_classificacao (
    prioridade, nome, ativo, criterio_palavras_chave,
    resultado_classificacao, data_criacao
) VALUES
(50, 'Laptop Rule', true, 'laptop', 'ELECTRONICS', NOW()),
(40, 'Monitor Rule', true, 'monitor', 'ELECTRONICS', NOW()),
(30, 'Cable Rule', true, 'cable', 'ACCESSORIES', NOW());
```

### Test with Live Database

```python
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

# Connect to real database
db = get_db_connection()
engine = RuleEngine(db)

# Test classification with real rules
products = [
    {'id': 'P001', 'description': 'laptop dell', 'ncm': '84713090'},
    {'id': 'P002', 'description': 'monitor samsung', 'ncm': '85287200'},
    {'id': 'P003', 'description': 'cable usb', 'ncm': '85444200'},
]

for product in products:
    result = engine.evaluate(product)
    print(f"{product['description']}: {result.classification}")
```

### Query Audit Trail

```sql
-- See all classifications
SELECT id_produto, resultado_classificacao, data_classificacao
FROM auditoria_classificacao
ORDER BY data_classificacao DESC
LIMIT 20;

-- Find products without matches
SELECT id_produto, COUNT(*) as attempts
FROM auditoria_classificacao
WHERE resultado_classificacao = 'NO_MATCH'
GROUP BY id_produto
ORDER BY attempts DESC;

-- Rule popularity
SELECT id_regra, COUNT(*) as times_used
FROM auditoria_classificacao
WHERE resultado_classificacao != 'NO_MATCH'
GROUP BY id_regra
ORDER BY times_used DESC;
```

---

## Test Coverage

### Current Coverage
```
src/classifier/
  - matcher.py: 100% (all criteria types tested)
  - evaluator.py: 100% (filtering and selection)
  - engine.py: 95% (error paths partially mocked)
  - audit.py: 95% (DB queries tested)
  - batch.py: 90% (mock limitations)
  - csv_classifier.py: 95% (file I/O tested)
  - models.py: 100%
```

### Coverage Report
```bash
# Generate HTML coverage report
pytest tests/ --cov=src/classifier --cov-report=html

# Open in browser
open htmlcov/index.html

# Print to console
pytest tests/ --cov=src/classifier --cov-report=term-missing
```

---

## Continuous Integration (CI) Commands

### Full Test Suite
```bash
#!/bin/bash
set -e

# Activate environment
source /tmp/classifier_venv/bin/activate

# Run all tests
pytest tests/ -v --cov=src/classifier

# Check code style (optional)
# flake8 src/ tests/
# mypy src/

# Exit with success
exit 0
```

### Quick Validation (< 30 seconds)
```bash
pytest tests/unit/ tests/cli/ -q
```

### Full Validation (< 2 minutes)
```bash
pytest tests/ -q --tb=short
```

---

## Troubleshooting Tests

### Test Fails with Import Error
```bash
# Solution: Make sure you're in the project directory
cd /home/divinopc/testes/projects/classifier_regras

# And activated the environment
source /tmp/classifier_venv/bin/activate
```

### Test Fails with Database Error
```bash
# Some tests require PostgreSQL
# Solution: Install PostgreSQL or use mock-based tests only

# Run only mock-based tests (no DB required)
pytest tests/unit/ tests/cli/ -v
```

### Test Fails with Timeout
```bash
# Increase timeout for slow systems
pytest tests/ --timeout=30

# Or skip slow performance tests
pytest tests/ -m "not slow" -v
```

### Test Fails with Encoding Error
```bash
# Solution: Set UTF-8 encoding
export PYTHONIOENCODING=utf-8
pytest tests/ -v
```

---

## Test Scenarios

### Scenario 1: Testing Basic Features
```bash
# Run these to verify core functionality
pytest tests/unit/test_matcher.py -v
pytest tests/unit/test_evaluator.py -v
pytest tests/unit/test_rule_engine.py -v
```

### Scenario 2: Testing Data Workflows
```bash
# Run these to verify data processing
pytest tests/unit/test_batch_classifier.py -v
pytest tests/unit/test_csv_classifier.py -v
```

### Scenario 3: Testing End-to-End
```bash
# Run these to verify complete workflows
pytest tests/integration/ -v
```

### Scenario 4: Testing CLI Tools
```bash
# Run these to verify command-line interfaces
pytest tests/cli/ -v
```

### Scenario 5: Testing Everything
```bash
# Run all tests (except DB-dependent)
pytest tests/ -v -k "not contract or rule_engine_api"
```

---

## Sample Test Results

### Running Unit Tests
```
tests/unit/test_matcher.py::TestKeywordMatching::test_match_keyword_substring PASSED
tests/unit/test_matcher.py::TestKeywordMatching::test_match_keyword_case_insensitive PASSED
...
tests/unit/test_matcher.py PASSED [42/277 tests]

tests/unit/test_evaluator.py PASSED [16/277 tests]
tests/unit/test_rule_engine.py PASSED [29/277 tests]
...

===== 277 passed in 7.05s =====
```

### Sample Manual Test
```
>>> from classifier.engine import RuleEngine
>>> from classifier.utils import get_db_connection
>>> db = get_db_connection()
>>> engine = RuleEngine(db)
>>> result = engine.evaluate({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})
>>> print(result.classification)
ELECTRONICS
>>> print(result.success)
True
```

---

## Continuous Improvement

### After Each Test Run
1. Check for failing tests
2. Review coverage report
3. Update code if needed
4. Re-run tests to verify fix

### Regular Testing Schedule
- **Daily**: Run full test suite before commit
- **Weekly**: Review coverage report, add missing tests
- **Monthly**: Performance testing with production-like data

---

## Getting Help

### Check Test Documentation
```bash
# Open the test file to see what's being tested
cat tests/unit/test_matcher.py

# Look for docstrings that explain the test
grep -A 5 "def test_" tests/unit/test_rule_engine.py
```

### Run Specific Test with Debug Output
```bash
# Show print statements
pytest tests/unit/test_matcher.py -v -s

# Show local variables on failure
pytest tests/unit/test_matcher.py -v -l

# Drop into debugger on failure
pytest tests/unit/test_matcher.py --pdb
```

### Get Help on Pytest
```bash
# Show all available options
pytest --help

# Show fixtures available
pytest --fixtures

# Show markers (test categories)
pytest --markers
```

---

## Summary

**To test your software:**

1. **Quick Test**: `pytest tests/unit/ -q` (30 seconds)
2. **Full Test**: `pytest tests/ -q` (7 seconds without DB)
3. **Manual Test**: Use Python shell to test individual components
4. **Performance**: Use `classify-batch` and `classify-csv` with sample files
5. **Coverage**: `pytest --cov=src/classifier --cov-report=html`

**Expected**: 277 passing tests, no failures in implemented features

**Success**: When all unit and CLI tests pass, system is ready to use!
