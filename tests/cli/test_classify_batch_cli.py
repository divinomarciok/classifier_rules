"""
Integration tests for classify_batch CLI script

Tests command-line interface for batch classification operations.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from io import StringIO

# Import the CLI module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from classifier.cli.classify_batch import main, format_summary, format_statistics


@pytest.mark.integration
class TestClassifyBatchCLI:
    """Integration tests for classify_batch CLI"""

    def test_cli_main_with_stats_flag(self):
        """Test: CLI returns statistics when --stats flag is used"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.get_batch_statistics.return_value = {
                    'total_products': 1000,
                    'classified': 750,
                    'unclassified': 250,
                    'classification_rate': 0.75
                }

                # Capture output
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    with patch('sys.argv', ['classify-batch', '--stats']):
                        result = main()

                    output = fake_out.getvalue()

                assert result == 0
                assert 'BATCH CLASSIFICATION STATISTICS' in output
                assert '1000' in output or '1,000' in output

    def test_cli_main_batch_classification(self):
        """Test: CLI processes batch classification"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 100,
                    'total_matched': 85,
                    'total_no_match': 15,
                    'match_rate': 0.85,
                    'classifications': {'CLASS_A': 50, 'CLASS_B': 35},
                    'elapsed_time_ms': 5000,
                    'no_match_products': ['P001', 'P002', 'P003']
                }

                with patch('sys.stdout', new=StringIO()) as fake_out:
                    with patch('sys.argv', ['classify-batch', '--limit', '100']):
                        result = main()

                    output = fake_out.getvalue()

                assert result == 0
                assert 'BATCH CLASSIFICATION SUMMARY' in output
                assert '100' in output

    def test_cli_main_dry_run_mode(self):
        """Test: CLI respects --dry-run flag (no database update)"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 50,
                    'total_matched': 40,
                    'total_no_match': 10,
                    'match_rate': 0.8,
                    'classifications': {'CLASS_A': 40},
                    'elapsed_time_ms': 2000,
                    'no_match_products': []
                }

                with patch('sys.argv', ['classify-batch', '--limit', '50', '--dry-run']):
                    result = main()

                # Verify update_db=False was passed
                call_args = mock_batch.classify_batch.call_args
                assert call_args[1]['update_db'] is False
                assert result == 0

    def test_cli_main_with_limit_and_offset(self):
        """Test: CLI passes limit and offset to batch classifier"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 100,
                    'total_matched': 80,
                    'total_no_match': 20,
                    'match_rate': 0.8,
                    'classifications': {},
                    'elapsed_time_ms': 3000,
                    'no_match_products': []
                }

                with patch('sys.argv', ['classify-batch', '--limit', '100', '--offset', '500']):
                    result = main()

                call_args = mock_batch.classify_batch.call_args
                assert call_args[1]['limit'] == 100
                assert call_args[1]['offset'] == 500
                assert result == 0

    def test_cli_main_with_where_clause(self):
        """Test: CLI passes custom WHERE clause to batch classifier"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 50,
                    'total_matched': 40,
                    'total_no_match': 10,
                    'match_rate': 0.8,
                    'classifications': {},
                    'elapsed_time_ms': 2000,
                    'no_match_products': []
                }

                where_clause = "ncm LIKE '8471%'"
                with patch('sys.argv', ['classify-batch', '--where', where_clause]):
                    result = main()

                call_args = mock_batch.classify_batch.call_args
                assert call_args[1]['where_clause'] == where_clause
                assert result == 0

    def test_cli_main_json_output(self):
        """Test: CLI outputs JSON when --json flag is used"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 100,
                    'total_matched': 85,
                    'total_no_match': 15,
                    'match_rate': 0.85,
                    'classifications': {'CLASS_A': 85},
                    'elapsed_time_ms': 5000,
                    'no_match_products': []
                }

                with patch('sys.stdout', new=StringIO()) as fake_out:
                    with patch('logging.basicConfig'):
                        with patch('sys.argv', ['classify-batch', '--json']):
                            result = main()

                        output = fake_out.getvalue()

                assert result == 0
                # Verify JSON output
                data = json.loads(output)
                assert data['total_processed'] == 100
                assert data['total_matched'] == 85

    def test_cli_main_error_handling(self):
        """Test: CLI handles errors gracefully"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            with patch('sys.stderr', new=StringIO()):
                with patch('sys.argv', ['classify-batch']):
                    result = main()

                assert result == 1

    def test_cli_main_keyboard_interrupt(self):
        """Test: CLI handles Ctrl+C gracefully"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.side_effect = KeyboardInterrupt()

                with patch('sys.argv', ['classify-batch']):
                    result = main()

                assert result == 130

    def test_cli_main_no_match_products(self):
        """Test: CLI shows no-match products in output"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 50,
                    'total_matched': 35,
                    'total_no_match': 15,
                    'match_rate': 0.7,
                    'classifications': {'CLASS_A': 35},
                    'elapsed_time_ms': 3000,
                    'no_match_products': ['P001', 'P002', 'P003', 'P004', 'P005']
                }

                with patch('sys.stdout', new=StringIO()) as fake_out:
                    with patch('sys.argv', ['classify-batch']):
                        result = main()

                    output = fake_out.getvalue()

                assert result == 0
                assert 'No Match Products' in output

    def test_format_summary_basic(self):
        """Test: format_summary produces valid output"""
        summary = {
            'total_processed': 100,
            'total_matched': 85,
            'total_no_match': 15,
            'match_rate': 0.85,
            'classifications': {'CLASS_A': 50, 'CLASS_B': 35},
            'elapsed_time_ms': 5000,
            'no_match_products': ['P001', 'P002']
        }

        output = format_summary(summary)

        assert 'BATCH CLASSIFICATION SUMMARY' in output
        assert '100' in output
        assert '85' in output
        assert '15' in output
        assert 'CLASS_A' in output
        assert 'CLASS_B' in output

    def test_format_summary_empty_classifications(self):
        """Test: format_summary handles empty classifications"""
        summary = {
            'total_processed': 50,
            'total_matched': 0,
            'total_no_match': 50,
            'match_rate': 0.0,
            'classifications': {},
            'elapsed_time_ms': 2000,
            'no_match_products': list(f'P{i}' for i in range(50))
        }

        output = format_summary(summary)

        assert 'BATCH CLASSIFICATION SUMMARY' in output
        assert '50' in output

    def test_format_statistics(self):
        """Test: format_statistics produces valid output"""
        stats = {
            'total_products': 1000,
            'classified': 750,
            'unclassified': 250,
            'classification_rate': 0.75
        }

        output = format_statistics(stats)

        assert 'BATCH CLASSIFICATION STATISTICS' in output
        assert '1000' in output or '1,000' in output
        assert '750' in output
        assert '250' in output
        assert '75.0%' in output or '75%' in output

    def test_cli_main_all_products_matched(self):
        """Test: CLI returns 0 when all products matched"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 100,
                    'total_matched': 100,
                    'total_no_match': 0,
                    'match_rate': 1.0,
                    'classifications': {'CLASS_A': 100},
                    'elapsed_time_ms': 4000,
                    'no_match_products': []
                }

                with patch('sys.argv', ['classify-batch']):
                    result = main()

                assert result == 0

    def test_cli_main_no_products_matched_returns_error(self):
        """Test: CLI returns 1 when no products matched"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 100,
                    'total_matched': 0,
                    'total_no_match': 100,
                    'match_rate': 0.0,
                    'classifications': {},
                    'elapsed_time_ms': 4000,
                    'no_match_products': list(f'P{i}' for i in range(100))
                }

                with patch('sys.stdout', new=StringIO()):
                    with patch('sys.argv', ['classify-batch']):
                        result = main()

                assert result == 1

    def test_cli_main_empty_batch_returns_success(self):
        """Test: CLI returns 0 for empty batch (no products found)"""
        with patch('classifier.cli.classify_batch.get_db_connection') as mock_get_db:
            mock_conn = Mock()
            mock_get_db.return_value = mock_conn

            with patch('classifier.cli.classify_batch.BatchClassifier') as mock_batch_class:
                mock_batch = Mock()
                mock_batch_class.return_value = mock_batch
                mock_batch.classify_batch.return_value = {
                    'total_processed': 0,
                    'total_matched': 0,
                    'total_no_match': 0,
                    'match_rate': 0.0,
                    'classifications': {},
                    'elapsed_time_ms': 100,
                    'no_match_products': []
                }

                with patch('sys.argv', ['classify-batch']):
                    result = main()

                assert result == 0
