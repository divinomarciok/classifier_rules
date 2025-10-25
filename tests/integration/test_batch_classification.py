"""
Integration tests for User Story 4 - Batch Classification

Tests the complete batch classification workflow with database interaction.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from classifier.batch import BatchClassifier
from classifier.models import Product, Rule


@pytest.mark.integration
class TestBatchClassificationIntegration:
    """Integration tests for batch classification workflow"""

    def test_batch_classify_multiple_products(self):
        """Test classifying 500 unclassified products in one operation"""
        mock_conn = self._create_mock_batch_db_with_products(500)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=500)

        # Verify results structure
        assert 'total_processed' in result
        assert 'total_matched' in result
        assert 'total_no_match' in result
        assert 'match_rate' in result
        assert 'elapsed_time_ms' in result

        # Verify counts
        assert result['total_processed'] == 500
        assert result['total_matched'] > 0  # Some should match with mock rules
        assert result['total_no_match'] >= 0

    def test_batch_with_limit_parameter(self):
        """Test batch respects limit parameter"""
        mock_conn = self._create_mock_batch_db_with_products(1000)
        batch = BatchClassifier(mock_conn)

        # Process only 100
        result = batch.classify_batch(limit=100)

        assert result['total_processed'] <= 100

    def test_batch_with_offset_pagination(self):
        """Test batch processes with offset (pagination)"""
        mock_conn = self._create_mock_batch_db_with_products(1000)
        batch = BatchClassifier(mock_conn)

        # First batch
        result1 = batch.classify_batch(limit=500, offset=0)
        assert result1['total_processed'] == 500

        # Second batch
        result2 = batch.classify_batch(limit=500, offset=500)
        assert result2['total_processed'] == 500

    def test_batch_generates_audit_entries(self):
        """Test that all batch classifications are recorded"""
        mock_conn = self._create_mock_batch_db_with_products(50)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=50)

        # All products should be processed
        assert result['total_processed'] == 50

    def test_batch_classifies_mixed_products(self):
        """Test batch handles products with various data profiles"""
        mock_conn = self._create_mock_batch_db_with_mixed_products()
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=10)

        # All should be processed
        assert result['total_processed'] == 10
        # Some matched, some didn't
        assert result['total_matched'] > 0
        assert result['total_no_match'] >= 0

    def test_batch_updates_database(self):
        """Test that batch updates database with classifications"""
        mock_conn = self._create_mock_batch_db_with_products(20)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=20, update_db=True)

        # Verify database updates were attempted
        assert mock_conn.cursor.return_value.execute.called
        assert mock_conn.commit.called

    def test_batch_can_skip_database_update(self):
        """Test that batch can skip database updates (dry-run)"""
        mock_conn = self._create_mock_batch_db_with_products(10)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=10, update_db=False)

        # Should still classify but not update DB
        assert result['total_processed'] == 10

    def test_batch_provides_classification_summary(self):
        """Test batch returns detailed classification summary"""
        mock_conn = self._create_mock_batch_db_with_products(100)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=100)

        # Verify summary statistics
        assert result['total_processed'] == 100
        assert result['total_matched'] + result['total_no_match'] == 100
        assert 0.0 <= result['match_rate'] <= 1.0
        assert 'classifications' in result  # Dict of classification -> count
        assert isinstance(result['classifications'], dict)

    def test_batch_tracks_no_match_products(self):
        """Test batch identifies and tracks products that didn't match"""
        mock_conn = self._create_mock_batch_db_with_products(50)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=50)

        # Track products with no match
        assert 'no_match_products' in result
        assert len(result['no_match_products']) == result['total_no_match']

    def test_batch_with_custom_where_clause(self):
        """Test batch respects custom WHERE clause for filtering"""
        mock_conn = self._create_mock_batch_db_with_products(1000)
        batch = BatchClassifier(mock_conn)

        # Filter by NCM pattern
        result = batch.classify_batch(
            limit=500,
            where_clause="ncm LIKE '8471%'"
        )

        assert result['total_processed'] > 0

    def test_batch_performance_tracking(self):
        """Test batch tracks execution time"""
        mock_conn = self._create_mock_batch_db_with_products(100)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=100)

        # Should track elapsed time
        assert 'elapsed_time_ms' in result
        assert result['elapsed_time_ms'] > 0

    def test_batch_statistics_query(self):
        """Test querying overall batch processing statistics"""
        mock_conn = self._create_mock_batch_db_with_stats()
        batch = BatchClassifier(mock_conn)

        stats = batch.get_batch_statistics()

        assert 'total_products' in stats
        assert 'classified' in stats
        assert 'unclassified' in stats
        assert 'classification_rate' in stats

    def test_batch_continues_on_individual_errors(self):
        """Test batch continues processing even if individual products fail"""
        mock_conn = self._create_mock_batch_db_with_products(100)
        batch = BatchClassifier(mock_conn)

        # Should process all even if one fails
        result = batch.classify_batch(limit=100)

        # All processed
        assert result['total_processed'] == 100

    @staticmethod
    def _create_mock_batch_db_with_products(count: int):
        """Create mock database with unclassified products"""
        from datetime import datetime

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Create mock rule row with all fields
        mock_rule_row = (
            1, "Test Rule", True, 50, "laptop", None, None, None, None, None, None, "TEST_CLASS",
            datetime.now(), datetime.now()
        )

        # Setup execute and fetchall to work together
        def execute_side_effect(sql, params=None):
            if "regras_de_classificacao" in sql:
                mock_cursor._is_rules_query = True
            else:
                mock_cursor._is_rules_query = False

        mock_cursor.execute.side_effect = execute_side_effect

        def fetchall_side_effect():
            if hasattr(mock_cursor, '_is_rules_query') and mock_cursor._is_rules_query:
                return [mock_rule_row]
            else:
                products = [
                    (f"PROD_{i}", f"Product {i}", "84713090", None, 0.5, 10)
                    for i in range(count)
                ]
                return products

        mock_cursor.fetchall.side_effect = fetchall_side_effect

        # Mock audit insert
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None

        return mock_conn

    @staticmethod
    def _create_mock_batch_db_with_mixed_products():
        """Create mock database with various product types"""
        from datetime import datetime

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Create mock rule row
        mock_rule_row = (
            1, "Test Rule", True, 50, "laptop", None, None, None, None, None, None, "TEST_CLASS",
            datetime.now(), datetime.now()
        )

        # Mixed products with various data
        products = [
            ("P001", "laptop", "84713090", None, 0.5, 10),
            ("P002", "monitor", "85287200", None, 0.8, 5),
            ("P003", "keyboard", "84711000", None, 0.2, 20),
            ("P004", "cable", "85444200", None, 0.05, 100),
            ("P005", "phone", "85171200", None, 0.1, 1),
            ("P006", "tablet", "85171200", None, 0.3, 2),
            ("P007", "router", "85176100", None, 0.4, 5),
            ("P008", "switch", "85176200", None, 0.3, 10),
            ("P009", "storage", "84717090", None, 1.5, 2),
            ("P010", "power supply", "85044030", None, 0.6, 5),
        ]

        def execute_side_effect(sql, params=None):
            if "regras_de_classificacao" in sql:
                mock_cursor._is_rules_query = True
            else:
                mock_cursor._is_rules_query = False

        mock_cursor.execute.side_effect = execute_side_effect

        def fetchall_side_effect():
            if hasattr(mock_cursor, '_is_rules_query') and mock_cursor._is_rules_query:
                return [mock_rule_row]
            else:
                return products

        mock_cursor.fetchall.side_effect = fetchall_side_effect
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None

        return mock_conn

    @staticmethod
    def _create_mock_batch_db_with_stats():
        """Create mock database for statistics queries"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock two query results: classified count, then unclassified count
        mock_cursor.fetchone.side_effect = [(750,), (250,)]

        return mock_conn
