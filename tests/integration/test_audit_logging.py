"""
Integration tests for User Story 3 - Audit Logging

Tests the complete audit logging workflow with classification results.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from classifier.audit import AuditLog


@pytest.mark.integration
class TestAuditLoggingIntegration:
    """Integration tests for audit logging with classification workflow"""

    def test_audit_logging_with_matching_rule(self):
        """Test complete audit trail when rule matches

        1. Product is classified
        2. Rule ID 42 matches with criteria
        3. Audit log records all context
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # Simulate classification workflow
        product_data = {
            'id': 'PROD_MATCH_001',
            'description': 'Dell laptop computer'
        }

        matched_criteria = [
            'criterio_palavras_chave',
            'criterio_ncm'
        ]

        audit_id = audit_log.record(
            rule_id=42,
            product_data=product_data,
            matched_criteria=matched_criteria,
            classification_result='ELECTRONICS',
            evaluation_time_ms=125,
            user='analyst1'
        )

        assert audit_id == 1
        assert mock_conn.cursor.return_value.execute.called
        assert mock_conn.commit.called

    def test_audit_logging_with_no_match(self):
        """Test complete audit trail when no rule matches

        1. Product is evaluated
        2. No rule matches (rule_id = None)
        3. NO_MATCH is logged with full context
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'PROD_NOMATCH_001',
            'description': 'Unknown product type'
        }

        audit_id = audit_log.record(
            rule_id=None,
            product_data=product_data,
            matched_criteria=[],
            classification_result='NO_MATCH',
            evaluation_time_ms=75,
            user='system'
        )

        assert audit_id == 1
        assert mock_conn.commit.called

    def test_audit_history_retrieval(self):
        """Test retrieving complete history for a product

        Given product history is logged over multiple evaluations,
        When we query product history,
        Then we get all classifications in reverse chronological order
        """
        mock_conn = self._create_mock_db_with_history()
        audit_log = AuditLog(mock_conn)

        history = audit_log.get_product_history('PROD_HIST_001')

        assert len(history) == 3
        assert history[0]['id'] == 1  # Most recent first
        assert history[1]['id'] == 2
        assert history[2]['id'] == 3

    def test_audit_history_respects_product_filter(self):
        """Test that product history only returns entries for that product"""
        mock_conn = self._create_mock_db_with_history()
        audit_log = AuditLog(mock_conn)

        history = audit_log.get_product_history('PROD_HIST_001')

        # All entries should be for the queried product
        assert all(entry['id_produto'] == 'PROD_HIST_001' for entry in history)

    def test_audit_history_with_different_rule_ids(self):
        """Test product history shows different rules applied over time

        Same product might match different rules if rules change
        or if evaluation is repeated
        """
        mock_conn = self._create_mock_db_with_history()
        audit_log = AuditLog(mock_conn)

        history = audit_log.get_product_history('PROD_HIST_001')

        # Verify different rule IDs are present
        rule_ids = [entry['id_regra'] for entry in history]
        # History shows: rule 42, rule 10, no match (None)
        assert 42 in rule_ids
        assert 10 in rule_ids
        assert None in rule_ids

    def test_audit_statistics_by_rule(self):
        """Test retrieving statistics for a specific rule

        Given a rule has been applied multiple times,
        When we query rule statistics,
        Then we get usage metrics
        """
        mock_conn = self._create_mock_db_with_stats()
        audit_log = AuditLog(mock_conn)

        stats = audit_log.get_rule_statistics(42)

        assert stats['times_applied'] == 100
        assert stats['avg_evaluation_time_ms'] == 125.5
        assert stats['min_evaluation_time_ms'] == 50
        assert stats['max_evaluation_time_ms'] == 500

    def test_audit_no_match_classification_query(self):
        """Test finding products that didn't match any rule

        This helps identify gaps in rules and improve coverage
        """
        mock_conn = self._create_mock_db_with_no_matches()
        audit_log = AuditLog(mock_conn)

        no_matches = audit_log.get_no_match_classifications()

        assert len(no_matches) == 2
        # All entries should have NO_MATCH classification
        assert all(e['resultado_classificacao'] == 'NO_MATCH' for e in no_matches)
        # All should have null rule_id
        assert all(e['id_regra'] is None for e in no_matches)

    def test_audit_workflow_multiple_evaluations_same_product(self):
        """Test audit trail for product evaluated multiple times

        Same product evaluated:
        1. First time - no rule matches (NO_MATCH)
        2. New rule added
        3. Second evaluation - rule matches
        4. Audit shows complete history
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        product_data = {'id': 'EVOLUTION_001', 'description': 'Product over time'}

        # First evaluation - no match
        audit_log.record(
            rule_id=None,
            product_data=product_data,
            matched_criteria=[],
            classification_result='NO_MATCH',
            evaluation_time_ms=50,
            user='system'
        )

        # Second evaluation - new rule added and matches
        audit_log.record(
            rule_id=100,
            product_data=product_data,
            matched_criteria=['new_criterion'],
            classification_result='NEW_CLASS',
            evaluation_time_ms=120,
            user='system'
        )

        assert mock_conn.commit.call_count == 2

    def test_audit_performance_metrics_captured(self):
        """Test that evaluation performance metrics are captured

        Each audit entry records evaluation_time_ms for performance
        monitoring and optimization
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # Fast evaluation
        audit_log.record(
            rule_id=1,
            product_data={'id': 'P_FAST', 'description': 'fast'},
            matched_criteria=[],
            classification_result='FAST',
            evaluation_time_ms=10,  # Very fast
            user='system'
        )

        # Slow evaluation
        audit_log.record(
            rule_id=1,
            product_data={'id': 'P_SLOW', 'description': 'slow'},
            matched_criteria=[],
            classification_result='SLOW',
            evaluation_time_ms=950,  # Slow
            user='system'
        )

        # Both should be recorded
        assert mock_conn.commit.call_count == 2

    def test_audit_user_tracking_different_users(self):
        """Test audit logs track different users performing classifications

        Different users/systems might perform classifications
        and should be tracked separately
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # System classification
        audit_log.record(
            rule_id=1,
            product_data={'id': 'P1', 'description': 'test'},
            matched_criteria=[],
            classification_result='CLASS',
            evaluation_time_ms=50,
            user='system'  # Default system user
        )

        # Analyst classification
        audit_log.record(
            rule_id=1,
            product_data={'id': 'P2', 'description': 'test'},
            matched_criteria=[],
            classification_result='CLASS',
            evaluation_time_ms=50,
            user='analyst_john'  # Specific analyst
        )

        # Both should be logged
        assert mock_conn.commit.call_count == 2

    def test_audit_complete_context_preserved(self):
        """Test that all context is preserved in audit log

        Complete context includes:
        - Product ID, description
        - Rule ID, name/criteria
        - Classification result
        - Timestamp
        - User/system
        - Evaluation time
        - Matched criteria
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # Create comprehensive audit entry
        product_data = {
            'id': 'COMPREHENSIVE_001',
            'description': 'Comprehensive test product with full context'
        }

        criteria = [
            'criterio_palavras_chave:laptop',
            'criterio_ncm:8471*',
            'criterio_tamanho_max:2.0',
            'criterio_quantidade_min:1'
        ]

        audit_log.record(
            rule_id=99,
            product_data=product_data,
            matched_criteria=criteria,
            classification_result='COMPREHENSIVE_CLASS',
            evaluation_time_ms=175,
            user='comprehensive_tester'
        )

        # Verify complete context was captured
        call_args = mock_conn.cursor.return_value.execute.call_args
        call_string = str(call_args)

        # All context should be present
        assert 'COMPREHENSIVE_001' in call_string  # Product ID
        assert 'Comprehensive test product' in call_string  # Description
        assert '99' in call_string  # Rule ID
        assert 'COMPREHENSIVE_CLASS' in call_string  # Classification
        assert 'comprehensive_tester' in call_string  # User

    @staticmethod
    def _create_mock_db():
        """Create mock database for single record"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        return mock_conn

    @staticmethod
    def _create_mock_db_with_history():
        """Create mock database with product history"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Product history (reverse chronological)
        history = [
            (1, 42, 'PROD_HIST_001', 'laptop', 'ELECTRONICS', datetime(2025, 1, 15), 'user1', 'keywords', 125),
            (2, 10, 'PROD_HIST_001', 'laptop', 'IT_EQUIPMENT', datetime(2025, 1, 14), 'user2', 'ncm', 100),
            (3, None, 'PROD_HIST_001', 'laptop', 'NO_MATCH', datetime(2025, 1, 13), 'system', 'NONE', 50),
        ]
        mock_cursor.fetchall.return_value = history
        return mock_conn

    @staticmethod
    def _create_mock_db_with_stats():
        """Create mock database with rule statistics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Rule statistics
        mock_cursor.fetchone.return_value = (
            100,  # times_applied
            datetime(2025, 1, 15),  # last_applied
            125.5,  # avg_evaluation_time_ms
            50,  # min_evaluation_time_ms
            500,  # max_evaluation_time_ms
        )
        return mock_conn

    @staticmethod
    def _create_mock_db_with_no_matches():
        """Create mock database with no-match classifications"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # No-match entries
        no_matches = [
            (10, None, 'UNKNOWN_001', 'unknown', 'NO_MATCH', datetime(2025, 1, 15), 'system', 'NONE', 50),
            (11, None, 'MYSTERY_001', 'mystery', 'NO_MATCH', datetime(2025, 1, 14), 'system', 'NONE', 75),
        ]
        mock_cursor.fetchall.return_value = no_matches
        return mock_conn
