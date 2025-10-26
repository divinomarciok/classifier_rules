# How to Run the Classifier - Complete Guide

Step-by-step instructions for running the product classification system.

---

## 🚀 Quick Start (2 minutes)

### 1. Activate the Python Environment
```bash
source /tmp/classifier_venv/bin/activate
```

### 2. Go to Project Directory
```bash
cd /home/divinopc/testes/projects/classifier_regras
```

### 3. Run Batch Classification
```bash
classify-batch --limit 10
```

**Result**: Classifies 10 products from database and shows summary

### 4. Run CSV Classification
```bash
classify-csv samples/products_basic.csv
```

**Result**: Classifies products from CSV file and creates `products_basic_classified.csv`

---

## 📋 Prerequisites

### What You Need
- Python 3.8+ (you have Python 3.12)
- Virtual environment with dependencies installed (already done)
- PostgreSQL database (optional, for full features)

### Check Your Setup
```bash
# Verify Python
python3 --version
# Output: Python 3.12.x

# Verify environment is activated
which python3
# Should show: /tmp/classifier_venv/bin/python3

# Verify project structure
ls -la /home/divinopc/testes/projects/classifier_regras/
# Should show: src/, tests/, docs/, samples/, etc.
```

---

## 📂 Directory Structure

```
classifier_regras/
├── src/classifier/          # Source code
│   ├── engine.py           # Main classification engine
│   ├── matcher.py          # Pattern matching
│   ├── evaluator.py        # Rule evaluation
│   ├── audit.py            # Audit logging
│   ├── batch.py            # Batch processing
│   ├── csv_classifier.py   # CSV import/export
│   └── cli/                # Command-line tools
│       ├── classify_batch.py
│       └── classify_csv.py
│
├── samples/                 # Sample CSV files
│   ├── products_basic.csv
│   ├── products_full.csv
│   ├── products_semicolon.csv
│   └── products_invalid.csv
│
├── tests/                   # 277 automated tests
│   ├── unit/               # Component tests
│   ├── integration/        # Workflow tests
│   ├── contract/           # API tests
│   └── cli/                # CLI tool tests
│
├── docs/                    # Documentation
│   ├── api.md
│   ├── rules_guide.md
│   ├── troubleshooting.md
│   └── deployment.md
│
└── migrations/              # Database setup
    └── *.sql files
```

---

## 🎯 Method 1: Batch Classification (from Database)

### What It Does
Processes multiple products stored in PostgreSQL database.

### Prerequisites
- PostgreSQL database with `productos` table
- Rules in `regras_de_classificacao` table
- Database connection configured in `.env`

### Run It
```bash
# Activate environment
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Process 10 products
classify-batch --limit 10

# Process 100 products
classify-batch --limit 100

# Process 500 products (default limit)
classify-batch

# Process products starting from offset 500 (pagination)
classify-batch --limit 100 --offset 500

# Process only specific NCM products
classify-batch --where "ncm LIKE '8471%'"

# Dry-run (don't update database)
classify-batch --limit 50 --dry-run

# Show overall statistics
classify-batch --stats

# Get results as JSON
classify-batch --limit 10 --json
```

### What You'll See
```
CSV CLASSIFICATION SUMMARY
======================================================================
Input File:          (processed in batch)
Output File:         (no file for batch mode)
Total Processed:     10 products
Total Matched:       8 products
Total No Match:      2 products
Match Rate:          80.0%
Rows Skipped:        0
Elapsed Time:        1,234 ms (1.23s)

Classifications Breakdown:
  - ELECTRONICS........................................         8 products

No Match Products: 2 total
  - PROD_UNKNOWN_1
  - PROD_UNKNOWN_2
======================================================================
```

### Options Explained

| Option | Purpose | Example |
|--------|---------|---------|
| `--limit N` | How many products to process | `--limit 500` |
| `--offset N` | Skip first N products (pagination) | `--offset 500` |
| `--where CLAUSE` | Filter products by SQL condition | `--where "ncm LIKE '8471%'"` |
| `--dry-run` | Simulate without updating database | `--dry-run` |
| `--stats` | Show overall statistics, don't process | `--stats` |
| `--json` | Output results as JSON | `--json` |
| `--verbose` | Show detailed logging | `--verbose` |

---

## 📄 Method 2: CSV Classification (from File)

### What It Does
1. Read products from CSV file
2. Classify each product
3. Write results to new CSV file with classifications

### Prerequisites
- CSV file with columns: `id`, `description`, `ncm`
- Optional columns: `size`, `quantity`, `category`

### Run It
```bash
# Activate environment
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Process sample CSV
classify-csv samples/products_basic.csv

# Specify output file
classify-csv samples/products_basic.csv --output my_results.csv

# Validate CSV before processing
classify-csv samples/products_basic.csv --validate

# Skip already-classified products
classify-csv samples/products_basic.csv --skip-classified

# Use semicolon delimiter (European CSV)
classify-csv samples/products_semicolon.csv --delimiter ";"

# Handle Latin-1 encoding
classify-csv data_latin1.csv --encoding latin-1

# Update database with classifications
classify-csv samples/products_basic.csv --update-db

# Get JSON output
classify-csv samples/products_basic.csv --json

# Combine options
classify-csv large_file.csv --output results.csv --skip-classified --update-db --verbose
```

### What You'll See
```
CSV CLASSIFICATION SUMMARY
======================================================================
Input File:          (processed in batch)
Output File:         /home/user/products_basic_classified.csv
Total Processed:     15 products
Total Matched:       13 products
Total No Match:      2 products
Match Rate:          86.7%
Rows Skipped:        0
Elapsed Time:        2,345 ms (2.35s)

Classifications Breakdown:
  - ELECTRONICS........................................        13 products

No Match Products: 2 total
  - PROD_UNKNOWN_1
  - PROD_UNKNOWN_2
======================================================================
```

### Options Explained

| Option | Purpose | Example |
|--------|---------|---------|
| `input.csv` | Input CSV file (required) | `products.csv` |
| `-o, --output` | Output file (auto-generated if omitted) | `-o results.csv` |
| `--validate` | Validate CSV format only, don't process | `--validate` |
| `--skip-classified` | Skip products already classified | `--skip-classified` |
| `--encoding` | File encoding (utf-8, latin-1, etc) | `--encoding utf-8` |
| `--delimiter` | CSV delimiter character | `--delimiter ";"` |
| `--batch-size` | Products per batch for memory efficiency | `--batch-size 2000` |
| `--update-db` | Write classifications to database | `--update-db` |
| `--json` | Output results as JSON | `--json` |
| `--verbose` | Show detailed logging | `--verbose` |

### Input CSV Format

**Minimum format** (required columns):
```csv
id,description,ncm
PROD_001,laptop dell,84713090
PROD_002,monitor samsung,85287200
```

**Full format** (with optional fields):
```csv
id,description,ncm,size,quantity
PROD_001,laptop dell,84713090,2.5,50
PROD_002,monitor samsung,85287200,5.2,30
```

### Output CSV Format

Same as input, plus two new columns:
```csv
id,description,ncm,size,quantity,classification,data_classificacao
PROD_001,laptop dell,84713090,2.5,50,ELECTRONICS,2025-10-25T11:30:00
PROD_002,monitor samsung,85287200,5.2,30,ELECTRONICS,2025-10-25T11:30:01
```

---

## 🐍 Method 3: Python API (Programmatic)

### What It Does
Use the classifier directly from Python code.

### Prerequisites
- Python environment activated
- Import necessary modules

### Run It

#### Basic Classification
```python
from classifier.engine import RuleEngine
from classifier.utils import get_db_connection

# Connect to database
db = get_db_connection()

# Create engine
engine = RuleEngine(db)

# Classify a single product
result = engine.evaluate({
    'id': 'PROD_001',
    'description': 'laptop dell',
    'ncm': '84713090'
})

# Check result
print(f"Classification: {result.classification}")
print(f"Success: {result.success}")
print(f"Rule ID: {result.rule_id}")
print(f"Rule Name: {result.rule_name}")
print(f"Time: {result.evaluation_time_ms}ms")
```

**Output**:
```
Classification: ELECTRONICS
Success: True
Rule ID: 1
Rule Name: Laptop Rule
Time: 45ms
```

#### Batch Classification
```python
from classifier.batch import BatchClassifier

# Create batch classifier
batch = BatchClassifier(db)

# Process 100 products
result = batch.classify_batch(limit=100)

# Check results
print(f"Total processed: {result['total_processed']}")
print(f"Total matched: {result['total_matched']}")
print(f"Match rate: {result['match_rate']:.1%}")
print(f"Time: {result['elapsed_time_ms']}ms")

# See what was classified
print("\nClassifications:")
for classification, count in result['classifications'].items():
    print(f"  {classification}: {count}")

# See what didn't match
if result['no_match_products']:
    print("\nNo Match Products:")
    for prod_id in result['no_match_products']:
        print(f"  {prod_id}")
```

#### CSV Classification
```python
from classifier.csv_classifier import CSVClassifier

# Create CSV classifier
classifier = CSVClassifier(db)

# Validate CSV
validation = classifier.validate_csv('input.csv')
if validation['valid']:
    print("✓ CSV is valid")
else:
    print("✗ CSV has issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")

# Process CSV
result = classifier.classify_csv(
    input_file='input.csv',
    output_file='output.csv',
    skip_classified=False,
    update_db=True
)

print(f"Processed: {result['total_processed']} products")
print(f"Matched: {result['total_matched']} products")
print(f"Output: {result['output_file']}")
```

#### Audit Queries
```python
from classifier.audit import AuditLog

# Create audit logger
audit = AuditLog(db)

# Get product classification history
history = audit.get_product_history(product_id='PROD_001')
for entry in history:
    print(f"Rule {entry.id_regra}: {entry.resultado_classificacao}")

# Get rule statistics
stats = audit.get_rule_statistics(rule_id=1)
print(f"Times applied: {stats['times_applied']}")
print(f"Average time: {stats['avg_time_ms']}ms")
print(f"Last used: {stats['last_applied']}")

# Find products without matches
no_match = audit.get_no_match_classifications(limit=10)
for entry in no_match:
    print(f"Product {entry.id_produto} didn't match any rules")
```

---

## 🧪 Method 4: Testing (Verify Everything Works)

### Run All Tests
```bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Run all tests
pytest tests/ -v
# Expected: 277 passing tests

# Run quick tests only (no database)
pytest tests/unit/ tests/cli/ -q
# Expected: ~160 tests in 2 seconds

# Run specific test
pytest tests/unit/test_matcher.py -v

# Run with coverage
pytest tests/ --cov=src/classifier --cov-report=html
```

### Run Sample Data Tests
```bash
# Process sample CSV (basic)
classify-csv samples/products_basic.csv

# Validate sample CSV (invalid)
classify-csv samples/products_invalid.csv --validate

# Process with different delimiter
classify-csv samples/products_semicolon.csv --delimiter ";"

# Process with all fields
classify-csv samples/products_full.csv
```

---

## 🔧 Configuration

### Environment Setup
```bash
# Check environment variables
cat .env

# Set database connection (if needed)
export DATABASE_URL="postgresql://user:password@localhost/classifier"

# Or create .env file:
cat > .env << 'ENVFILE'
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=classifier
ENVFILE
```

### Install/Update Dependencies
```bash
# Activate environment
source /tmp/classifier_venv/bin/activate

# Install all requirements
pip install -r requirements.txt

# Or install specific package
pip install psycopg2-binary==2.9.0
```

---

## 📊 Common Use Cases

### Use Case 1: Quick Classification Test
```bash
# Quick test with 10 products
classify-batch --limit 10
```

### Use Case 2: Process Entire CSV File
```bash
# Process complete file
classify-csv myfile.csv --output results.csv

# Then update database
classify-csv myfile.csv --update-db
```

### Use Case 3: Validate Before Processing
```bash
# Check file first
classify-csv myfile.csv --validate

# If valid, process
if [ $? -eq 0 ]; then
    classify-csv myfile.csv
fi
```

### Use Case 4: Process in Batches
```bash
# Process in 500-product batches
for offset in 0 500 1000 1500 2000; do
    classify-batch --limit 500 --offset $offset
done
```

### Use Case 5: Export Classifications
```bash
# Process CSV and save results
classify-csv products.csv --output classified_products.csv

# Or update database directly
classify-csv products.csv --update-db
```

### Use Case 6: Check Statistics
```bash
# See overall progress
classify-batch --stats
```

---

## 🐛 Troubleshooting

### Problem: "command not found: classify-batch"

**Solution**: Activate virtual environment
```bash
source /tmp/classifier_venv/bin/activate
which classify-batch  # Should show: /tmp/classifier_venv/bin/classify-batch
```

### Problem: "ModuleNotFoundError: No module named 'classifier'"

**Solution**: Make sure you're in project directory
```bash
cd /home/divinopc/testes/projects/classifier_regras
source /tmp/classifier_venv/bin/activate
```

### Problem: "Database connection failed"

**Solution**: Check database is running or use mock mode
```bash
# Check database
psql -h localhost -U postgres -l

# Or run tests without database
pytest tests/unit/ tests/cli/ -q
```

### Problem: "CSV file encoding error"

**Solution**: Specify encoding
```bash
# Try UTF-8 (default)
classify-csv file.csv

# Try Latin-1
classify-csv file.csv --encoding latin-1

# Try ISO-8859-1
classify-csv file.csv --encoding iso-8859-1
```

### Problem: "Permission denied" on sample files

**Solution**: Make files readable
```bash
chmod +r samples/*.csv
```

---

## ✅ Success Checklist

You've successfully run the classifier when:

- [ ] Environment activated: `source /tmp/classifier_venv/bin/activate`
- [ ] In correct directory: `cd /home/divinopc/testes/projects/classifier_regras`
- [ ] CLI commands work: `classify-batch --help` shows help
- [ ] Tests pass: `pytest tests/unit/ -q` shows 150+ passing
- [ ] CSV processing works: `classify-csv samples/products_basic.csv` creates output file
- [ ] Output file created: `ls samples/products_basic_classified.csv`
- [ ] Classifications added: `head -3 samples/products_basic_classified.csv` shows classification column

---

## 📚 Learning Path

### Day 1: Getting Started
1. Activate environment and verify setup
2. Run quick tests: `pytest tests/unit/ -q`
3. Process sample CSV: `classify-csv samples/products_basic.csv`
4. Check results: `head samples/products_basic_classified.csv`

### Day 2: Understanding the System
1. Read `PROJECT_SUMMARY.md` for architecture overview
2. Run batch classification: `classify-batch --limit 10`
3. Try different options: `classify-batch --stats`
4. Review IMPLEMENTATION_LOG.md for implementation details

### Day 3: Advanced Usage
1. Read `docs/api.md` for API reference
2. Use Python API directly from shell
3. Test with your own CSV files
4. Review `docs/rules_guide.md` to understand rule creation

### Day 4+: Production Use
1. Review `docs/deployment.md` for deployment setup
2. Create database and tables from `migrations/`
3. Add your own classification rules
4. Process production data with confidence

---

## 🎓 Tips & Tricks

### Tip 1: Keep Terminal Window Open
```bash
# Keep one window with environment activated
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras

# Then run commands as needed
```

### Tip 2: Save Command Aliases
```bash
# Add to ~/.bashrc for easier access
alias classify_proj='source /tmp/classifier_venv/bin/activate'

# Then just type:
classify_proj  # Takes you to project with environment ready
```

### Tip 3: Create Test Scripts
```bash
# Create test.sh
#!/bin/bash
source /tmp/classifier_venv/bin/activate
cd /home/divinopc/testes/projects/classifier_regras
pytest tests/unit/ -q

# Run it
chmod +x test.sh
./test.sh
```

### Tip 4: Monitor Progress
```bash
# Watch batch statistics while processing
watch -n 1 'classify-batch --stats'

# Process and log results
classify-batch --limit 100 | tee batch_log.txt
```

---

## 📞 Getting Help

1. **For system issues**: Check TESTING_GUIDE.md "Troubleshooting" section
2. **For API questions**: See docs/api.md with 50+ examples
3. **For rule creation**: See docs/rules_guide.md
4. **For deployment**: See docs/deployment.md
5. **For architecture**: See PROJECT_SUMMARY.md

---

## Summary

**3 Ways to Run the Classifier**:

1. **CLI (Easiest)**
   ```bash
   source /tmp/classifier_venv/bin/activate
   classify-batch --limit 10
   classify-csv samples/products_basic.csv
   ```

2. **Python (Flexible)**
   ```python
   from classifier.engine import RuleEngine
   engine = RuleEngine(db)
   result = engine.evaluate({'description': 'laptop', 'ncm': '84713090'})
   ```

3. **Tests (Verification)**
   ```bash
   pytest tests/ -v
   ```

**Next Steps**:
- Run batch classification: `classify-batch --limit 10`
- Process CSV file: `classify-csv samples/products_basic.csv`
- Read PROJECT_SUMMARY.md for full system understanding
- Explore docs/ folder for detailed guides

Happy classifying! 🚀
