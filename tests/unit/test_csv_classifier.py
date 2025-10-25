"""
Unit tests for CSVClassifier service

Tests CSV import, classification, and export functionality in isolation.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from classifier.csv_classifier import CSVClassifier
from classifier.models import ClassificationResult


@pytest.mark.unit
class TestCSVClassifierRowConversion:
    """Tests for CSV row to Product conversion"""

    def test_row_to_product_required_fields(self):
        """Test: Convert CSV row with required fields to Product"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        row = {
            'id': 'PROD_001',
            'description': 'laptop',
            'ncm': '84713090'
        }

        product = csv_classifier._row_to_product(row)

        assert product.id == 'PROD_001'
        assert product.description == 'laptop'
        assert product.ncm == '84713090'

    def test_row_to_product_optional_fields(self):
        """Test: Convert CSV row with optional fields"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        row = {
            'id': 'PROD_002',
            'description': 'monitor',
            'ncm': '85287200',
            'size': '0.8',
            'quantity': '5'
        }

        product = csv_classifier._row_to_product(row)

        assert product.size == 0.8
        assert product.quantity == 5.0

    def test_row_to_product_missing_optional_fields(self):
        """Test: Handle CSV row with missing optional fields"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        row = {
            'id': 'PROD_003',
            'description': 'cable',
            'ncm': '85444200'
        }

        product = csv_classifier._row_to_product(row)

        assert product.id == 'PROD_003'
        assert product.size is None
        assert product.quantity is None

    def test_row_to_product_invalid_numeric_values(self):
        """Test: Handle invalid numeric values in optional fields"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        row = {
            'id': 'PROD_004',
            'description': 'item',
            'ncm': '99999999',
            'size': 'invalid',
            'quantity': 'not_a_number'
        }

        product = csv_classifier._row_to_product(row)

        assert product.size is None
        assert product.quantity is None

    def test_row_to_product_category_field(self):
        """Test: Handle both category and categoria fields"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        row = {
            'id': 'PROD_005',
            'description': 'product',
            'ncm': '84713090',
            'category': 'ELECTRONICS'
        }

        product = csv_classifier._row_to_product(row)

        assert product.category == 'ELECTRONICS'


@pytest.mark.unit
class TestCSVClassifierValidation:
    """Tests for CSV validation functionality"""

    def test_validate_csv_valid_file(self):
        """Test: Validate a valid CSV file"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
            writer.writeheader()
            writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})
            f.flush()
            temp_file = f.name

        try:
            result = csv_classifier.validate_csv(temp_file)

            assert result['valid'] is True
            assert result['row_count'] == 1
            assert len(result['issues']) == 0
        finally:
            Path(temp_file).unlink()

    def test_validate_csv_missing_required_columns(self):
        """Test: Detect missing required columns"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'description'])  # Missing ncm
            writer.writeheader()
            writer.writerow({'id': 'P001', 'description': 'laptop'})
            f.flush()
            temp_file = f.name

        try:
            result = csv_classifier.validate_csv(temp_file)

            assert result['valid'] is False
            assert len(result['issues']) > 0
        finally:
            Path(temp_file).unlink()

    def test_validate_csv_missing_required_fields_in_rows(self):
        """Test: Detect rows with missing required field values"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
            writer.writeheader()
            writer.writerow({'id': 'P001', 'description': '', 'ncm': '84713090'})  # Empty description
            f.flush()
            temp_file = f.name

        try:
            result = csv_classifier.validate_csv(temp_file)

            assert result['valid'] is False
            assert len(result['missing_fields']) > 0
        finally:
            Path(temp_file).unlink()

    def test_validate_csv_empty_file(self):
        """Test: Handle empty CSV file"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            f.flush()
            temp_file = f.name

        try:
            result = csv_classifier.validate_csv(temp_file)

            assert result['valid'] is False
        finally:
            Path(temp_file).unlink()


@pytest.mark.unit
class TestCSVClassifierProcessing:
    """Tests for CSV processing and classification"""

    def test_process_csv_creates_output_file(self):
        """Test: CSV processing creates output file"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        csv_classifier = CSVClassifier(mock_conn)

        # Mock engine.evaluate
        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='TEST_CLASS',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})

            # Process CSV
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                update_db=False
            )

            assert result['total_processed'] == 1
            assert result['total_matched'] == 1
            assert output_file.exists()

    def test_process_csv_skip_classified_products(self):
        """Test: Skip already classified products when flag is set"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        # Mock engine.evaluate
        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='NEW_CLASS',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV with some classified products
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm', 'classification'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090', 'classification': None})
                writer.writerow({'id': 'P002', 'description': 'monitor', 'ncm': '85287200', 'classification': 'CLASS_A'})

            # Process CSV with skip_classified=True
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                skip_classified=True,
                update_db=False
            )

            # Should only process 1 (skip the already classified one)
            assert result['rows_skipped'] == 1

    def test_process_csv_handles_invalid_rows(self):
        """Test: Handle rows with missing required fields"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV with some invalid rows
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})
                writer.writerow({'id': '', 'description': 'monitor', 'ncm': '85287200'})  # Missing id
                writer.writerow({'id': 'P003', 'description': '', 'ncm': '84711000'})  # Missing description

            # Process CSV
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                update_db=False
            )

            # Should have skipped invalid rows
            assert result['rows_skipped'] >= 1

    def test_process_csv_with_no_matches(self):
        """Test: Handle products that don't match any rules"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        csv_classifier = CSVClassifier(mock_conn)

        # Mock engine.evaluate with no match
        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification=None,
            rule_id=None,
            matched_criteria=[],
            success=False
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'unknown', 'ncm': '99999999'})

            # Process CSV
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                update_db=False
            )

            assert result['total_no_match'] == 1
            assert 'P001' in result['no_match_products']

    def test_process_csv_encoding_utf8(self):
        """Test: Handle UTF-8 encoded CSV files"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='CLASS_A',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV with UTF-8 characters
            with open(input_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'café', 'ncm': '84713090'})

            # Process CSV
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                encoding='utf-8',
                update_db=False
            )

            assert result['total_processed'] == 1

    def test_process_csv_custom_delimiter(self):
        """Test: Handle CSV with custom delimiter"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='CLASS_A',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input with semicolon delimiter
            with open(input_file, 'w', newline='') as f:
                f.write('id;description;ncm\n')
                f.write('P001;laptop;84713090\n')

            # Process CSV with semicolon delimiter
            result = csv_classifier.classify_csv(
                str(input_file),
                str(output_file),
                delimiter=';',
                update_db=False
            )

            assert result['total_processed'] == 1


@pytest.mark.unit
class TestCSVClassifierIntegration:
    """Tests for CSV classifier integration with engine"""

    def test_classify_csv_returns_summary(self):
        """Test: CSV classification returns complete summary"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='TEST_CLASS',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                for i in range(10):
                    writer.writerow({'id': f'P{i:03d}', 'description': 'item', 'ncm': '84713090'})

            # Process CSV
            result = csv_classifier.classify_csv(str(input_file), update_db=False)

            assert 'total_processed' in result
            assert 'total_matched' in result
            assert 'total_no_match' in result
            assert 'match_rate' in result
            assert 'classifications' in result
            assert 'elapsed_time_ms' in result
            assert 'no_match_products' in result
            assert 'output_file' in result

    def test_classify_csv_output_has_classification_column(self):
        """Test: Output CSV includes classification column"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='CLASS_A',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})

            # Process CSV
            csv_classifier.classify_csv(str(input_file), str(output_file), update_db=False)

            # Verify output has classification column
            with open(output_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                assert 'classification' in headers
                assert 'data_classificacao' in headers

                for row in reader:
                    assert row['classification'] == 'CLASS_A'


@pytest.mark.unit
class TestCSVClassifierEdgeCases:
    """Tests for edge cases and error handling"""

    def test_classify_csv_file_not_found(self):
        """Test: Handle missing input file"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with pytest.raises(FileNotFoundError):
            csv_classifier.classify_csv('/nonexistent/file.csv')

    def test_classify_csv_invalid_csv_format(self):
        """Test: Handle invalid CSV format"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'

            # Create CSV with missing required columns
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description'])  # Missing ncm
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop'})

            with pytest.raises(ValueError):
                csv_classifier.classify_csv(str(input_file))

    def test_classify_csv_default_output_filename(self):
        """Test: Generate default output filename"""
        mock_conn = Mock()
        csv_classifier = CSVClassifier(mock_conn)

        csv_classifier.engine.evaluate = Mock(return_value=ClassificationResult(
            classification='CLASS_A',
            rule_id=None,
            matched_criteria=[],
            success=True
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})

            # Process CSV without specifying output
            result = csv_classifier.classify_csv(str(input_file), update_db=False)

            # Output filename should be generated
            assert 'input_classified.csv' in result['output_file']
