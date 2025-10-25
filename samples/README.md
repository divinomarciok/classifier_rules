# Sample CSV Files for Product Classification

This directory contains example CSV files for testing the CSV classification functionality.

## Files

### 1. products_basic.csv
Basic CSV file with minimal columns (id, description, ncm).

**Usage:**
```bash
classify-csv samples/products_basic.csv
```

**Features:**
- 15 sample products
- Required columns only
- Electronics products with real NCM codes
- No optional fields (size, quantity)

### 2. products_full.csv
Complete CSV file with all optional columns.

**Usage:**
```bash
classify-csv samples/products_full.csv
```

**Features:**
- 20 sample products
- All columns: id, description, ncm, size, quantity
- Real-world product data
- Size and quantity for rule matching
- Good for testing complex rule evaluation

### 3. products_semicolon.csv
CSV file using semicolon (;) delimiter instead of comma.

**Usage:**
```bash
classify-csv samples/products_semicolon.csv --delimiter ";"
```

**Features:**
- 10 sample products
- Semicolon-delimited format
- Tests custom delimiter handling
- Common in European systems (Excel exports)

### 4. products_invalid.csv
Invalid CSV file with missing required fields.

**Usage:**
```bash
classify-csv samples/products_invalid.csv --validate
```

**Expected Result:**
```
✗ CSV file has issues - see details below

Columns Found: id, description, ncm
Data Rows: 6

Issues Found:
  - (none)

Rows with Missing Fields: 3 rows
  - Row 3 (missing description)
  - Row 4 (missing ncm)
  - Row 6 (missing ncm)
```

**Features:**
- 6 products with various missing fields
- Tests CSV validation and error handling
- Tests --validate mode
- Demonstrates row-level error reporting

## Quick Start

### Test Basic Classification
```bash
# Validate before processing
classify-csv samples/products_basic.csv --validate

# Classify products
classify-csv samples/products_basic.csv

# Check output
head samples/products_basic_classified.csv
```

### Test Full Data Processing
```bash
# Process with all optional fields
classify-csv samples/products_full.csv --output products_classified.csv

# Get statistics
cat products_classified.csv | wc -l  # Should be 21 (header + 20 products)
```

### Test Delimiter Handling
```bash
# Process semicolon-delimited file
classify-csv samples/products_semicolon.csv --delimiter ";" --output products_semi_classified.csv
```

### Test Validation
```bash
# Validate good CSV
classify-csv samples/products_basic.csv --validate

# Validate bad CSV
classify-csv samples/products_invalid.csv --validate
```

### Test JSON Output
```bash
# Get results as JSON
classify-csv samples/products_basic.csv --json | jq .

# Validate as JSON
classify-csv samples/products_invalid.csv --validate --json
```

## NCM Codes Used

| NCM | Product Type | Examples |
|-----|--------------|----------|
| 84713090 | Computer components | Laptops, Desktop computers |
| 85287200 | Monitors | Display devices |
| 84711000 | Keyboards | Input devices |
| 84714000 | Computer mice, Graphics cards | Input/compute |
| 85444200 | Cables | Connection cables |
| 85171200 | Mobile devices | Tablets, Smartphones |
| 85184200 | Audio equipment | Headphones, Speakers |
| 85044030 | Power supplies | Power banks, PSUs |
| 85176100 | Network equipment | Routers, WiFi |
| 85176200 | Network equipment | Switches, Hubs |
| 84717090 | Storage | SSDs, External drives |
| 85258090 | Cameras | Webcams, USB cameras |
| 85042990 | Memory | RAM modules |

## Testing Scenarios

### Scenario 1: Simple Classification
1. Use `products_basic.csv`
2. Run: `classify-csv samples/products_basic.csv`
3. Check that all products are classified
4. Verify output file created with classifications

### Scenario 2: Optional Fields
1. Use `products_full.csv`
2. Run: `classify-csv samples/products_full.csv`
3. Check that size/quantity rules can match
4. Verify products with size/quantity constraints are classified

### Scenario 3: Custom Delimiter
1. Use `products_semicolon.csv`
2. Run: `classify-csv samples/products_semicolon.csv --delimiter ";"`
3. Verify parsing with semicolon delimiter works
4. Check output file created correctly

### Scenario 4: Validation Only
1. Use `products_invalid.csv`
2. Run: `classify-csv samples/products_invalid.csv --validate`
3. Verify validation detects missing fields
4. Check error messages point to specific rows

### Scenario 5: Skip Already Classified
1. Run first classification: `classify-csv samples/products_basic.csv --output temp.csv`
2. Add classification column to CSV manually
3. Run again with `--skip-classified` flag
4. Verify already-classified products are skipped

## Expected Output Example

```
CSV CLASSIFICATION SUMMARY
======================================================================
Input File:          (processed in batch)
Output File:         /path/to/products_basic_classified.csv
Total Processed:     15 products
Total Matched:       13 products
Total No Match:      2 products
Match Rate:          86.7%
Rows Skipped:        0
Elapsed Time:        1,234 ms (1.23s)

Classifications Breakdown:
  - ELECTRONICS....................................         13 products

No Match Products: 2 total
  - PROD_UNKNOWN_1
  - PROD_UNKNOWN_2
======================================================================
```

## For Developers

### Adding New Test Data
1. Create new CSV file in `samples/` directory
2. Follow naming convention: `products_[scenario].csv`
3. Update this README with file description
4. Add to test suite if needed

### Automated Testing
Sample CSV files are used in:
- `tests/unit/test_csv_classifier.py` - Unit tests
- `tests/integration/test_batch_classification.py` - Integration tests
- `tests/cli/test_classify_csv_cli.py` - CLI tests

### Performance Testing
For large-scale testing, you can generate files programmatically:
```python
import csv

# Generate 10,000 product CSV
with open('products_large.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
    writer.writeheader()
    for i in range(10000):
        writer.writerow({
            'id': f'PROD_{i:06d}',
            'description': f'Product {i}',
            'ncm': '84713090'
        })
```

Then test:
```bash
time classify-csv samples/products_large.csv
```
