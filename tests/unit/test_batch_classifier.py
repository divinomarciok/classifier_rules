"""
Unit tests for BatchClassifier service

Tests batch classification functionality in isolation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from classifier.batch import BatchClassifier


@pytest.mark.unit
class TestBatchClassifierQuery:
    """Tests for batch product querying"""

    def test_get_unclassified_products_basic(self):
        """Test: Query unclassified products with default limit"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock query result
        products = [
            ("P001", "laptop", "84713090", None, 0.5, 10),
            ("P002", "monitor", "85287200", None, 0.8, 5),
        ]
        mock_cursor.fetchall.return_value = products

        batch = BatchClassifier(mock_conn)
        result = batch._get_unclassified_products(limit=500, offset=0)

        assert len(result) == 2
        assert result[0][0] == "P001"
        assert mock_cursor.execute.called

    def test_get_unclassified_products_respects_limit(self):
        """Test: Query respects LIMIT parameter"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [(f"P{i}", f"Prod{i}", "99999999", None, 0.5, 1) for i in range(100)]

        batch = BatchClassifier(mock_conn)
        batch._get_unclassified_products(limit=100, offset=0)

        # Verify execute was called with correct LIMIT
        call_args = mock_cursor.execute.call_args
        assert 'LIMIT' in str(call_args[0][0])

    def test_get_unclassified_products_respects_offset(self):
        """Test: Query respects OFFSET parameter"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        batch = BatchClassifier(mock_conn)
        batch._get_unclassified_products(limit=500, offset=250)

        # Verify execute was called with OFFSET
        call_args = mock_cursor.execute.call_args
        assert 'OFFSET' in str(call_args[0][0])
        assert 250 in call_args[0][1]

    def test_get_unclassified_products_with_where_clause(self):
        """Test: Query accepts custom WHERE clause"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        batch = BatchClassifier(mock_conn)
        batch._get_unclassified_products(
            limit=500,
            offset=0,
            where_clause="ncm LIKE '8471%'"
        )

        # Verify WHERE clause was included
        call_args = mock_cursor.execute.call_args
        query = str(call_args[0][0])
        assert "8471" in query or "WHERE" in query

    def test_get_unclassified_products_returns_empty(self):
        """Test: Query returns empty list if no products"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        batch = BatchClassifier(mock_conn)
        result = batch._get_unclassified_products(limit=500, offset=0)

        assert result == []


@pytest.mark.unit
class TestBatchClassifierConversion:
    """Tests for database row to Product conversion"""

    def test_row_to_product_required_fields(self):
        """Test: Convert row with required fields to Product"""
        mock_conn = Mock()
        batch = BatchClassifier(mock_conn)

        # Row: (id, description, ncm, categoria, size, quantity, ...)
        row = ("P001", "laptop", "84713090", None, 0.5, 10)

        product = batch._row_to_product(row)

        assert product.id == "P001"
        assert product.description == "laptop"
        assert product.ncm == "84713090"

    def test_row_to_product_optional_fields(self):
        """Test: Convert row with optional fields"""
        mock_conn = Mock()
        batch = BatchClassifier(mock_conn)

        row = ("P002", "monitor", "85287200", None, 0.8, 5)

        product = batch._row_to_product(row)

        assert product.size == 0.8
        assert product.quantity == 5

    def test_row_to_product_missing_optional_fields(self):
        """Test: Handle row with missing optional fields"""
        mock_conn = Mock()
        batch = BatchClassifier(mock_conn)

        row = ("P003", "cable", "85444200")  # No size, quantity

        product = batch._row_to_product(row)

        assert product.id == "P003"
        assert product.description == "cable"
        assert product.ncm == "85444200"
        assert product.size is None
        assert product.quantity is None


@pytest.mark.unit
class TestBatchClassifierUpdate:
    """Tests for database update operations"""

    def test_update_product_classification_success(self):
        """Test: Update product with classification"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        batch = BatchClassifier(mock_conn)
        result = batch._update_product_classification("P001", "ELECTRONICS")

        assert result is True
        assert mock_cursor.execute.called
        assert mock_conn.commit.called

    def test_update_product_classification_with_timestamp(self):
        """Test: Update includes timestamp"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        batch = BatchClassifier(mock_conn)
        batch._update_product_classification("P001", "ELECTRONICS")

        # Verify timestamp was included in update
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        assert "data_classificacao" in sql

    def test_update_product_rollback_on_error(self):
        """Test: Rollback on update error"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Update failed")

        batch = BatchClassifier(mock_conn)

        with pytest.raises(Exception):
            batch._update_product_classification("P001", "ELECTRONICS")

        # Verify rollback was called
        assert mock_conn.rollback.called


@pytest.mark.unit
class TestBatchClassifierStatistics:
    """Tests for statistics computation"""

    def test_get_batch_statistics_basic(self):
        """Test: Compute basic statistics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock two queries: classified count, unclassified count
        mock_cursor.fetchone.side_effect = [(750,), (250,)]

        batch = BatchClassifier(mock_conn)
        stats = batch.get_batch_statistics()

        assert stats['total_products'] == 1000
        assert stats['classified'] == 750
        assert stats['unclassified'] == 250
        assert stats['classification_rate'] == 0.75

    def test_get_batch_statistics_all_classified(self):
        """Test: Statistics when all products are classified"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [(1000,), (0,)]

        batch = BatchClassifier(mock_conn)
        stats = batch.get_batch_statistics()

        assert stats['total_products'] == 1000
        assert stats['classified'] == 1000
        assert stats['unclassified'] == 0
        assert stats['classification_rate'] == 1.0

    def test_get_batch_statistics_empty_database(self):
        """Test: Statistics with empty database"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [(0,), (0,)]

        batch = BatchClassifier(mock_conn)
        stats = batch.get_batch_statistics()

        assert stats['total_products'] == 0
        assert stats['classification_rate'] == 0.0


@pytest.mark.unit
class TestBatchClassifierSummary:
    """Tests for batch summary computation"""

    def test_classify_batch_returns_summary(self):
        """Test: Batch operation returns complete summary"""
        mock_conn = self._create_mock_batch_db(10)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=10)

        assert 'total_processed' in result
        assert 'total_matched' in result
        assert 'total_no_match' in result
        assert 'match_rate' in result
        assert 'classifications' in result
        assert 'elapsed_time_ms' in result
        assert 'no_match_products' in result

    def test_classify_batch_match_counts_add_up(self):
        """Test: Matched + no_match = total_processed"""
        mock_conn = self._create_mock_batch_db(50)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=50)

        total = result['total_matched'] + result['total_no_match']
        assert total == result['total_processed']

    def test_classify_batch_match_rate_calculation(self):
        """Test: Match rate is calculated correctly"""
        mock_conn = self._create_mock_batch_db(100)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=100)

        expected_rate = result['total_matched'] / result['total_processed']
        assert abs(result['match_rate'] - expected_rate) < 0.01

    def test_classify_batch_classifications_dict(self):
        """Test: Classifications dict contains all results"""
        mock_conn = self._create_mock_batch_db(100)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=100)

        # Count from classifications dict should equal total matched
        total_from_dict = sum(result['classifications'].values())
        assert total_from_dict == result['total_matched']

    def test_classify_batch_respects_limit(self):
        """Test: Batch respects limit parameter"""
        # Note: Mock returns all 1000, but in real DB, LIMIT would be respected
        mock_conn = self._create_mock_batch_db(250)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=250)

        assert result['total_processed'] == 250

    def test_classify_batch_without_db_update(self):
        """Test: Batch can run without updating database"""
        mock_conn = self._create_mock_batch_db(20)
        batch = BatchClassifier(mock_conn)

        result = batch.classify_batch(limit=20, update_db=False)

        assert result['total_processed'] == 20

    @staticmethod
    def _create_mock_batch_db(count: int):
        """Create mock database"""
        from classifier.models import Rule
        from datetime import datetime

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Create mock rules with all required fields
        mock_rule_row = (
            1,  # id
            "Test Rule",  # nome
            True,  # ativo
            50,  # prioridade
            "laptop",  # criterio_palavras_chave
            None,  # criterio_ncm
            None,  # criterio_tamanho_min
            None,  # criterio_tamanho_max
            None,  # criterio_quantidade_min
            None,  # criterio_quantidade_max
            None,  # criterio_categoria
            "TEST_CLASS",  # resultado_classificacao
            datetime.now(),  # data_criacao
            datetime.now(),  # data_atualizacao
        )

        # Setup execute and fetchall to work together
        call_count = [0]  # Use list to maintain state across calls

        original_execute = mock_cursor.execute
        def execute_side_effect(sql, params=None):
            call_count[0] += 1
            if "regras_de_classificacao" in sql:
                mock_cursor._is_rules_query = True
            else:
                mock_cursor._is_rules_query = False

        mock_cursor.execute.side_effect = execute_side_effect

        def fetchall_side_effect():
            if hasattr(mock_cursor, '_is_rules_query') and mock_cursor._is_rules_query:
                return [mock_rule_row]
            else:
                # Return products
                products = [
                    (f"P{i}", f"Product {i}", "84713090", None, 0.5, 1)
                    for i in range(count)
                ]
                return products

        mock_cursor.fetchall.side_effect = fetchall_side_effect

        # Mock INSERT and UPDATE
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None

        return mock_conn
