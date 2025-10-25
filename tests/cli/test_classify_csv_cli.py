"""
Integration tests for classify_csv CLI script

Tests command-line interface for CSV classification operations.
"""

import pytest
import json
import sys
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from io import StringIO

# Import the CLI module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from classifier.cli.classify_csv import main, format_csv_summary, format_csv_validation


@pytest.mark.integration
class TestClassifyCsvCLI:
    """Integration tests for classify_csv CLI"""

    def test_cli_main_with_input_file(self):
        """Test: CLI processes CSV file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input CSV
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 1,
                        'total_no_match': 0,
                        'match_rate': 1.0,
                        'classifications': {'CLASS_A': 1},
                        'elapsed_time_ms': 1000,
                        'no_match_products': [],
                        'rows_skipped': 0,
                        'output_file': str(Path(tmpdir) / 'input_classified.csv')
                    }

                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        with patch('sys.argv', ['classify-csv', str(input_file)]):
                            result = main()

                    assert result == 0

    def test_cli_main_validation_mode(self):
        """Test: CLI validates CSV when --validate flag is used"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'item', 'ncm': '99999999'})

            with patch('classifier.cli.classify_csv.get_db_connection'):
                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.validate_csv.return_value = {
                        'valid': True,
                        'headers': ['id', 'description', 'ncm'],
                        'row_count': 1,
                        'issues': [],
                        'missing_fields': []
                    }

                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        with patch('sys.argv', ['classify-csv', str(input_file), '--validate']):
                            result = main()

                    assert result == 0

    def test_cli_main_validation_invalid_csv(self):
        """Test: CLI returns error for invalid CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                f.write('id,description\n')  # Missing ncm column
                f.write('P001,laptop\n')

            with patch('classifier.cli.classify_csv.get_db_connection'):
                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.validate_csv.return_value = {
                        'valid': False,
                        'headers': ['id', 'description'],
                        'row_count': 1,
                        'issues': ["Missing required columns: {'ncm'}"],
                        'missing_fields': []
                    }

                    with patch('sys.stdout', new=StringIO()):
                        with patch('sys.argv', ['classify-csv', str(input_file), '--validate']):
                            result = main()

                    assert result == 1

    def test_cli_main_with_output_file(self):
        """Test: CLI respects --output parameter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            output_file = Path(tmpdir) / 'output.csv'

            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090'})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 1,
                        'total_no_match': 0,
                        'match_rate': 1.0,
                        'classifications': {},
                        'elapsed_time_ms': 1000,
                        'no_match_products': [],
                        'rows_skipped': 0,
                        'output_file': str(output_file)
                    }

                    with patch('sys.argv', ['classify-csv', str(input_file), '--output', str(output_file)]):
                        result = main()

                    call_args = mock_csv.classify_csv.call_args
                    assert call_args[1]['output_file'] == str(output_file)
                    assert result == 0

    def test_cli_main_skip_classified(self):
        """Test: CLI passes skip_classified flag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm', 'classification'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'laptop', 'ncm': '84713090', 'classification': None})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 1,
                        'total_no_match': 0,
                        'match_rate': 1.0,
                        'classifications': {},
                        'elapsed_time_ms': 1000,
                        'no_match_products': [],
                        'rows_skipped': 0,
                        'output_file': str(Path(tmpdir) / 'output.csv')
                    }

                    with patch('sys.argv', ['classify-csv', str(input_file), '--skip-classified']):
                        result = main()

                    call_args = mock_csv.classify_csv.call_args
                    assert call_args[1]['skip_classified'] is True
                    assert result == 0

    def test_cli_main_update_db(self):
        """Test: CLI passes update_db flag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'item', 'ncm': '99999999'})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 0,
                        'total_no_match': 1,
                        'match_rate': 0.0,
                        'classifications': {},
                        'elapsed_time_ms': 1000,
                        'no_match_products': ['P001'],
                        'rows_skipped': 0,
                        'output_file': str(Path(tmpdir) / 'output.csv')
                    }

                    with patch('sys.argv', ['classify-csv', str(input_file), '--update-db']):
                        result = main()

                    call_args = mock_csv.classify_csv.call_args
                    assert call_args[1]['update_db'] is True

    def test_cli_main_custom_encoding(self):
        """Test: CLI supports custom encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'café', 'ncm': '84713090'})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 1,
                        'total_no_match': 0,
                        'match_rate': 1.0,
                        'classifications': {},
                        'elapsed_time_ms': 1000,
                        'no_match_products': [],
                        'rows_skipped': 0,
                        'output_file': str(Path(tmpdir) / 'output.csv')
                    }

                    with patch('sys.argv', ['classify-csv', str(input_file), '--encoding', 'utf-8']):
                        result = main()

                    call_args = mock_csv.classify_csv.call_args
                    assert call_args[1]['encoding'] == 'utf-8'
                    assert result == 0

    def test_cli_main_json_output(self):
        """Test: CLI outputs JSON when --json flag is used"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'input.csv'
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'description', 'ncm'])
                writer.writeheader()
                writer.writerow({'id': 'P001', 'description': 'item', 'ncm': '99999999'})

            with patch('classifier.cli.classify_csv.get_db_connection') as mock_get_db:
                mock_conn = Mock()
                mock_get_db.return_value = mock_conn

                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.return_value = {
                        'total_processed': 1,
                        'total_matched': 1,
                        'total_no_match': 0,
                        'match_rate': 1.0,
                        'classifications': {'CLASS_A': 1},
                        'elapsed_time_ms': 1000,
                        'no_match_products': [],
                        'rows_skipped': 0,
                        'output_file': str(Path(tmpdir) / 'output.csv')
                    }

                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        with patch('logging.basicConfig'):
                            with patch('sys.argv', ['classify-csv', str(input_file), '--json']):
                                result = main()

                            output = fake_out.getvalue()

                    assert result == 0
                    data = json.loads(output)
                    assert data['total_processed'] == 1

    def test_cli_main_file_not_found(self):
        """Test: CLI handles missing file gracefully"""
        with patch('classifier.cli.classify_csv.get_db_connection'):
            with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                mock_csv = Mock()
                mock_csv_class.return_value = mock_csv
                mock_csv.classify_csv.side_effect = FileNotFoundError("File not found")

                with patch('sys.stderr', new=StringIO()):
                    with patch('sys.argv', ['classify-csv', '/nonexistent/file.csv']):
                        result = main()

                assert result == 1

    def test_cli_main_invalid_csv_format(self):
        """Test: CLI handles invalid CSV format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / 'invalid.csv'
            with open(input_file, 'w', newline='') as f:
                f.write('id,description\n')  # Missing ncm

            with patch('classifier.cli.classify_csv.get_db_connection'):
                with patch('classifier.cli.classify_csv.CSVClassifier') as mock_csv_class:
                    mock_csv = Mock()
                    mock_csv_class.return_value = mock_csv
                    mock_csv.classify_csv.side_effect = ValueError("Missing required column: ncm")

                    with patch('sys.stderr', new=StringIO()):
                        with patch('sys.argv', ['classify-csv', str(input_file)]):
                            result = main()

                assert result == 1

    def test_format_csv_summary(self):
        """Test: format_csv_summary produces valid output"""
        summary = {
            'total_processed': 100,
            'total_matched': 85,
            'total_no_match': 15,
            'match_rate': 0.85,
            'classifications': {'CLASS_A': 50, 'CLASS_B': 35},
            'elapsed_time_ms': 5000,
            'no_match_products': ['P001', 'P002'],
            'rows_skipped': 0,
            'output_file': '/path/to/output.csv'
        }

        output = format_csv_summary(summary)

        assert 'CSV CLASSIFICATION SUMMARY' in output
        assert 'output.csv' in output
        assert '100' in output
        assert '85' in output
        assert 'CLASS_A' in output

    def test_format_csv_validation(self):
        """Test: format_csv_validation produces valid output"""
        validation = {
            'valid': True,
            'headers': ['id', 'description', 'ncm'],
            'row_count': 50,
            'issues': [],
            'missing_fields': []
        }

        output = format_csv_validation(validation)

        assert 'CSV VALIDATION RESULTS' in output
        assert '✓' in output
        assert 'valid' in output.lower()
