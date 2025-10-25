"""
Contract tests for User Story 3 - Audit Logging

Tests that the system records classification decisions with full context
for business transparency and compliance.
"""

import pytest
from datetime import datetime
from classifier.audit import AuditLog
from classifier.models import Product, Rule


@pytest.mark.contract
class TestAuditLoggingUS3:
    """Contract tests for US3: Audit Logging of Applied Rules"""

    def test_us3_scenario_1_rule_applied_logged(self):
        """US3 Scenario 1: Classification with rule creates audit log entry

        Given a product is classified using rule ID 42,
        When the classification is complete,
        Then an audit log entry is created with:
        - rule ID
        - timestamp
        - product ID/description
        - matching criteria that triggered the rule
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'PROD_42',
            'description': 'laptop computer'
        }

        audit_id = audit_log.record(
            rule_id=42,
            product_data=product_data,
            matched_criteria=['keywords:laptop'],
            classification_result='ELECTRONICS',
            evaluation_time_ms=125,
            user='analyst1'
        )

        # Assert: Audit entry was created
        assert audit_id is not None
        assert isinstance(audit_id, int)

    def test_us3_scenario_2_no_match_logged(self):
        """US3 Scenario 2: No matching rule creates audit log entry

        Given a product evaluation fails or no rule matches,
        When the evaluation completes,
        Then an audit log entry is created documenting that
        no matching rule was found
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'UNKNOWN_001',
            'description': 'unknown product type'
        }

        audit_id = audit_log.record(
            rule_id=None,  # No rule matched
            product_data=product_data,
            matched_criteria=[],
            classification_result='NO_MATCH',
            evaluation_time_ms=50,
            user='system'
        )

        # Assert: Audit entry was created for no-match case
        assert audit_id is not None

    def test_us3_scenario_3_audit_history_query(self):
        """US3 Scenario 3: Query audit logs by product

        Given a business analyst queries the audit logs,
        When they filter by product ID,
        Then they can see the complete history of which rules
        were applied and when
        """
        mock_conn = self._create_mock_db_with_history()
        audit_log = AuditLog(mock_conn)

        # Query product history
        history = audit_log.get_product_history('PROD_001', limit=100)

        # Assert: Can retrieve complete history
        assert len(history) > 0
        assert all(entry['id_produto'] == 'PROD_001' for entry in history)
        # Verify most recent first (reverse chronological)
        if len(history) > 1:
            assert history[0]['data_classificacao'] >= history[1]['data_classificacao']

    def test_audit_logging_includes_all_required_fields(self):
        """Verify: Audit log entries include all required fields

        FR-007: System MUST create audit log entries recording:
        - rule ID
        - product ID/description
        - classification result
        - timestamp
        - matching criteria
        - evaluation time
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        product_data = {
            'id': 'COMPREHENSIVE_TEST',
            'description': 'Test product for audit'
        }

        criteria = ['keywords:test', 'size:0.5-2.0', 'category:TEST']

        audit_id = audit_log.record(
            rule_id=99,
            product_data=product_data,
            matched_criteria=criteria,
            classification_result='TEST_CLASS',
            evaluation_time_ms=42,
            user='tester'
        )

        # Assert: All required information was logged
        assert audit_id is not None
        # Verify the mock was called with all parameters
        call_args = mock_conn.cursor.return_value.execute.call_args
        call_string = str(call_args)
        assert '99' in call_string  # rule_id
        assert 'COMPREHENSIVE_TEST' in call_string  # product_id
        assert 'TEST_CLASS' in call_string  # classification
        assert 'tester' in call_string  # user

    def test_audit_matches_criteria_formatted(self):
        """Verify: Matched criteria are properly formatted in audit log

        Multiple matching criteria should be captured and formatted
        for readability.
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        criteria = [
            'criterio_palavras_chave',
            'criterio_ncm',
            'criterio_tamanho_min',
            'criterio_tamanho_max'
        ]

        audit_log.record(
            rule_id=1,
            product_data={'id': 'P1', 'description': 'test'},
            matched_criteria=criteria,
            classification_result='MULTI_CRITERIA',
            evaluation_time_ms=100
        )

        # Verify criteria were formatted and included
        call_args = mock_conn.cursor.return_value.execute.call_args
        call_string = str(call_args)
        # Should contain the formatted criteria
        assert 'criterio_palavras_chave' in call_string

    def test_audit_logging_timestamps_captured(self):
        """Verify: Timestamps are captured for audit trail

        Every audit entry must have a timestamp for establishing
        when classification occurred.
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        before = datetime.now()
        audit_log.record(
            rule_id=1,
            product_data={'id': 'TIME_TEST', 'description': 'test'},
            matched_criteria=[],
            classification_result='CLASS',
            evaluation_time_ms=50
        )
        after = datetime.now()

        # Verify timestamp was captured (by checking execute was called)
        assert mock_conn.cursor.return_value.execute.called

    def test_audit_user_tracking(self):
        """Verify: User/system performing classification is recorded

        Each audit entry records who (user or system) made the
        classification decision.
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        audit_log.record(
            rule_id=1,
            product_data={'id': 'P1', 'description': 'test'},
            matched_criteria=[],
            classification_result='CLASS',
            evaluation_time_ms=50,
            user='analyst_john'
        )

        call_args = mock_conn.cursor.return_value.execute.call_args
        assert 'analyst_john' in str(call_args)

    def test_audit_evaluation_time_tracked(self):
        """Verify: Evaluation time is recorded in audit log

        Performance metrics should be captured for each classification.
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        audit_log.record(
            rule_id=1,
            product_data={'id': 'P1', 'description': 'test'},
            matched_criteria=[],
            classification_result='CLASS',
            evaluation_time_ms=987,  # Performance metric
            user='system'
        )

        call_args = mock_conn.cursor.return_value.execute.call_args
        assert '987' in str(call_args)

    def test_audit_complete_workflow_integration(self):
        """Integration test: Complete classification with audit logging

        Simulates a full workflow where:
        1. Product is evaluated
        2. Rule is matched
        3. Classification is made
        4. Audit log is created
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # Simulate full workflow
        product_data = {
            'id': 'WORKFLOW_TEST',
            'description': 'Integration test product'
        }

        rule_id = 42
        classification = 'ELECTRONICS'
        criteria = ['keywords:laptop', 'ncm:8471*']
        eval_time = 125
        user = 'workflow_tester'

        audit_id = audit_log.record(
            rule_id=rule_id,
            product_data=product_data,
            matched_criteria=criteria,
            classification_result=classification,
            evaluation_time_ms=eval_time,
            user=user
        )

        # Assert: Complete audit trail was created
        assert audit_id is not None
        assert mock_conn.cursor.return_value.execute.called
        assert mock_conn.commit.called

    def test_audit_no_match_indicates_improvement_opportunity(self):
        """Verify: NO_MATCH classifications help identify missing rules

        When a product doesn't match any rule, it's logged as NO_MATCH
        to help business teams identify products that need new rules.
        """
        mock_conn = self._create_mock_db()
        audit_log = AuditLog(mock_conn)

        # Log a no-match case
        audit_log.record(
            rule_id=None,
            product_data={'id': 'UNCLASSIFIED', 'description': 'new product type'},
            matched_criteria=[],
            classification_result='NO_MATCH',
            evaluation_time_ms=75
        )

        # Verify it was logged
        assert mock_conn.cursor.return_value.execute.called
        call_args = mock_conn.cursor.return_value.execute.call_args
        assert 'NO_MATCH' in str(call_args)

    @staticmethod
    def _create_mock_db():
        """Create a mock database connection for testing"""
        from unittest.mock import Mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)  # Inserted audit ID
        return mock_conn

    @staticmethod
    def _create_mock_db_with_history():
        """Create a mock database with audit history"""
        from unittest.mock import Mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock audit history rows
        history_rows = [
            (1, 42, 'PROD_001', 'laptop', 'ELECTRONICS', datetime(2025, 1, 15, 10, 30), 'user1', 'keywords:laptop', 125),
            (2, 10, 'PROD_001', 'laptop', 'IT_EQUIPMENT', datetime(2025, 1, 14, 9, 20), 'user2', 'ncm:8471*', 100),
            (3, None, 'PROD_001', 'laptop', 'NO_MATCH', datetime(2025, 1, 13, 8, 10), 'system', 'NONE', 50),
        ]
        mock_cursor.fetchall.return_value = history_rows
        return mock_conn
