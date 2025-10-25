"""
Audit logging service - Records all classification decisions

Implements US3 (Audit Logging) and FR-007
Constitutional Principle V (Auditability)
"""

import logging
import json
from typing import Optional, Dict, List, Any

from classifier.models import AuditEntry

logger = logging.getLogger(__name__)


class AuditLog:
    """Records classification decisions to database for auditability

    Appends to auditoria_classificacao table (immutable, append-only).
    Every classification decision is logged with full context.

    Constitutional Principle V: Full traceability
    """

    def __init__(self, db_connection):
        """Initialize AuditLog service

        Args:
            db_connection: Database connection for queries
        """
        self.db_connection = db_connection

    def record(
        self,
        rule_id: Optional[int],
        product_data: Dict[str, Any],
        matched_criteria: List[str],
        classification_result: str,
        evaluation_time_ms: int,
        user: str = 'system',
    ) -> int:
        """Record a classification decision to audit log

        Creates a single entry in auditoria_classificacao table
        capturing all details of the classification.

        Args:
            rule_id: ID of rule that matched (or None if no match)
            product_data: Product data dict with id, description, ncm, etc
            matched_criteria: List of criterion names that matched
            classification_result: The classification result
            evaluation_time_ms: How long evaluation took
            user: User/system performing classification (default: 'system')

        Returns:
            int: ID of inserted audit log entry

        Raises:
            DatabaseError: If insert fails

        Implementation Plan:
            1. Extract product info from product_data
            2. Format matched_criteria as JSON
            3. Build INSERT statement
            4. Execute INSERT
            5. Return inserted entry ID
        """
        # TODO: Implement audit recording
        pass

    def get_product_history(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all classifications for a product

        Queries audit log for product and returns in reverse chronological order.

        Args:
            product_id: Product ID to query
            limit: Maximum number of entries to return (default: 100)

        Returns:
            list: List of audit log entries for product (most recent first)

        Implementation:
            SELECT * FROM auditoria_classificacao
            WHERE id_produto = product_id
            ORDER BY data_classificacao DESC
            LIMIT limit
        """
        # TODO: Implement product history query
        pass

    def get_rule_statistics(self, rule_id: int) -> Dict[str, Any]:
        """Get statistics for a rule

        Aggregates audit log data to show rule usage stats.

        Args:
            rule_id: Rule ID to analyze

        Returns:
            dict: Statistics including:
                - times_applied: How many times rule matched
                - last_applied: When rule was last used
                - avg_evaluation_time_ms: Average evaluation time
                - min_evaluation_time_ms: Minimum evaluation time
                - max_evaluation_time_ms: Maximum evaluation time

        Implementation:
            SELECT
                COUNT(*) as times_applied,
                MAX(data_classificacao) as last_applied,
                AVG(tempo_avaliacao_ms) as avg_evaluation_time_ms,
                MIN(tempo_avaliacao_ms) as min_evaluation_time_ms,
                MAX(tempo_avaliacao_ms) as max_evaluation_time_ms
            FROM auditoria_classificacao
            WHERE id_regra = rule_id
        """
        # TODO: Implement rule statistics query
        pass

    def get_no_match_classifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get classifications where no rule matched

        Useful for identifying products that need new rules.

        Args:
            limit: Maximum number to return

        Returns:
            list: Audit entries where id_regra IS NULL (no match)
        """
        # TODO: Implement no-match query
        pass
