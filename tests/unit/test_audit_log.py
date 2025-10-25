"""
Unit tests for AuditLog service

Tests audit logging functionality for classification decisions.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from classifier.audit import AuditLog


@pytest.mark.unit
class TestAuditLogRecord:
    """Tests for recording classification decisions to audit log"""

    def test_record_with_matching_rule(self):
        """Test: Record audit entry when rule matched"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # Inserted audit ID

        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'PROD001',
            'description': 'laptop computer'
        }
        matched_criteria = ['keywords:laptop']
        result = audit_log.record(
            rule_id=42,
            product_data=product_data,
            matched_criteria=matched_criteria,
            classification_result='ELECTRONICS',
            evaluation_time_ms=125,
            user='analyst1'
        )

        # Verify database call was made
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
        assert result == 1  # Returned inserted ID

    def test_record_with_no_match(self):
        """Test: Record audit entry when no rule matched"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (2,)

        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'PROD002',
            'description': 'unknown product'
        }
        result = audit_log.record(
            rule_id=None,  # No match
            product_data=product_data,
            matched_criteria=[],
            classification_result='NO_MATCH',
            evaluation_time_ms=50
        )

        assert result == 2
        assert mock_conn.commit.called

    def test_record_without_connection(self):
        """Test: Record handles missing database connection gracefully"""
        audit_log = AuditLog(None)

        result = audit_log.record(
            rule_id=42,
            product_data={'id': 'P001', 'description': 'test'},
            matched_criteria=['test'],
            classification_result='TEST',
            evaluation_time_ms=100
        )

        # Should return None without error
        assert result is None

    def test_record_includes_matched_criteria(self):
        """Test: Record includes matched criteria in audit entry"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        audit_log = AuditLog(mock_conn)

        product_data = {'id': 'P001', 'description': 'test'}
        matched_criteria = [
            'keywords:laptop',
            'size:0.5-2.0',
            'quantity:1-100'
        ]

        audit_log.record(
            rule_id=1,
            product_data=product_data,
            matched_criteria=matched_criteria,
            classification_result='CLASS',
            evaluation_time_ms=100
        )

        # Verify criteria were included in the call
        call_args = mock_cursor.execute.call_args
        assert 'keywords:laptop | size:0.5-2.0 | quantity:1-100' in str(call_args)

    def test_record_with_multiple_criteria(self):
        """Test: Record handles multiple matched criteria"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (5,)

        audit_log = AuditLog(mock_conn)

        matched_criteria = [
            'criterio_palavras_chave',
            'criterio_ncm',
            'criterio_tamanho_min'
        ]

        result = audit_log.record(
            rule_id=10,
            product_data={'id': 'P10', 'description': 'complex'},
            matched_criteria=matched_criteria,
            classification_result='COMPLEX',
            evaluation_time_ms=200
        )

        assert result == 5


@pytest.mark.unit
class TestAuditLogQuery:
    """Tests for querying audit logs"""

    def test_get_product_history_returns_entries(self):
        """Test: Get product history returns list of audit entries"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock database rows
        mock_rows = [
            (1, 42, 'P001', 'laptop', 'ELECTRONICS', datetime.now(), 'user1', 'criteria1', 100),
            (2, 10, 'P001', 'laptop', 'IT_EQUIPMENT', datetime.now(), 'user2', 'criteria2', 150),
        ]
        mock_cursor.fetchall.return_value = mock_rows

        audit_log = AuditLog(mock_conn)
        history = audit_log.get_product_history('P001')

        assert len(history) == 2
        assert history[0]['id'] == 1
        assert history[1]['id'] == 2
        assert mock_cursor.execute.called

    def test_get_product_history_empty(self):
        """Test: Get product history returns empty list if no entries"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        audit_log = AuditLog(mock_conn)
        history = audit_log.get_product_history('NONEXISTENT')

        assert history == []

    def test_get_product_history_respects_limit(self):
        """Test: get_product_history respects limit parameter"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        audit_log = AuditLog(mock_conn)
        audit_log.get_product_history('P001', limit=50)

        # Verify LIMIT 50 was in the query
        call_args = mock_cursor.execute.call_args
        assert 'LIMIT' in str(call_args[0][0])


@pytest.mark.unit
class TestAuditLogStatistics:
    """Tests for rule statistics queries"""

    def test_get_rule_statistics(self):
        """Test: Get rule statistics returns aggregated data"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock statistics row: count, max date, avg time, min time, max time
        mock_cursor.fetchone.return_value = (
            100,  # times_applied
            datetime(2025, 1, 1),  # last_applied
            125.5,  # avg_evaluation_time_ms
            50,  # min_evaluation_time_ms
            500,  # max_evaluation_time_ms
        )

        audit_log = AuditLog(mock_conn)
        stats = audit_log.get_rule_statistics(42)

        assert stats['times_applied'] == 100
        assert stats['avg_evaluation_time_ms'] == 125.5
        assert stats['min_evaluation_time_ms'] == 50
        assert stats['max_evaluation_time_ms'] == 500

    def test_get_rule_statistics_empty(self):
        """Test: Get rule statistics returns empty dict if no data"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        audit_log = AuditLog(mock_conn)
        stats = audit_log.get_rule_statistics(999)

        assert stats == {}


@pytest.mark.unit
class TestAuditLogNoMatch:
    """Tests for querying no-match classifications"""

    def test_get_no_match_classifications(self):
        """Test: Get no-match classifications returns entries with NULL rule"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_rows = [
            (10, None, 'P100', 'unknown', 'NO_MATCH', datetime.now(), 'user', 'NONE', 75),
            (11, None, 'P101', 'mystery', 'NO_MATCH', datetime.now(), 'user', 'NONE', 60),
        ]
        mock_cursor.fetchall.return_value = mock_rows

        audit_log = AuditLog(mock_conn)
        no_matches = audit_log.get_no_match_classifications(limit=50)

        assert len(no_matches) == 2
        assert all(entry['id_regra'] is None for entry in no_matches)
        assert all(entry['resultado_classificacao'] == 'NO_MATCH' for entry in no_matches)

    def test_get_no_match_empty(self):
        """Test: Get no-match returns empty list if no no-matches"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        audit_log = AuditLog(mock_conn)
        no_matches = audit_log.get_no_match_classifications()

        assert no_matches == []


@pytest.mark.unit
class TestAuditLogErrorHandling:
    """Tests for error handling in AuditLog"""

    def test_record_handles_database_error(self):
        """Test: Record handles database errors gracefully"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        audit_log = AuditLog(mock_conn)

        with pytest.raises(Exception):
            audit_log.record(
                rule_id=1,
                product_data={'id': 'P1', 'description': 'test'},
                matched_criteria=[],
                classification_result='TEST',
                evaluation_time_ms=100
            )

        # Verify rollback was called
        assert mock_conn.rollback.called

    def test_query_handles_database_error(self):
        """Test: Query methods handle errors gracefully"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query error")

        audit_log = AuditLog(mock_conn)

        # Should return empty list instead of raising
        history = audit_log.get_product_history('P1')
        assert history == []

        stats = audit_log.get_rule_statistics(1)
        assert stats == {}

        no_matches = audit_log.get_no_match_classifications()
        assert no_matches == []
