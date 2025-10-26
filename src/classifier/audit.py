"""
Audit logging service - Records all classification decisions

Implements US3 (Audit Logging) and FR-007
Constitutional Principle V (Auditability)
"""

import logging
from datetime import datetime
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
        categoria_id: Optional[int] = None,
        evaluation_time_ms: int = 0,
        user: str = 'system',
    ) -> int:
        """Record a classification decision to audit log

        Creates a single entry in auditoria_classificacao table
        capturing all details of the classification.

        Args:
            rule_id: ID of rule that matched (or None if no match)
            product_data: Product data dict with id, description, ncm, etc
            matched_criteria: List of criterion names that matched
            classification_result: The classification result (category name)
            categoria_id: Category ID assigned (FK to categorias table)
            evaluation_time_ms: How long evaluation took
            user: User/system performing classification (default: 'system')

        Returns:
            int: ID of inserted audit log entry

        Raises:
            DatabaseError: If insert fails

        Implementation Plan:
            1. Extract product info from product_data
            2. Format matched_criteria as JSON
            3. Build INSERT statement with categoria_id
            4. Execute INSERT
            5. Return inserted entry ID
        """
        try:
            if not self.db_connection:
                logger.warning("No database connection for audit logging")
                return None

            cursor = self.db_connection.cursor()

            # Extract product information
            product_id = product_data.get('id')
            product_description = product_data.get('description', '')

            # Format matched criteria as pipe-separated string
            criteria_str = ' | '.join(matched_criteria) if matched_criteria else 'NONE'

            # Insert audit entry
            cursor.execute("""
                INSERT INTO auditoria_classificacao (
                    id_regra,
                    id_produto,
                    descricao_produto,
                    categoria_id,
                    resultado_classificacao,
                    data_classificacao,
                    usuario,
                    criterios_correspondentes,
                    tempo_avaliacao_ms
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
            """, (
                rule_id,
                product_id,
                product_description,
                categoria_id,
                classification_result,
                datetime.now(),
                user,
                criteria_str,
                evaluation_time_ms,
            ))

            audit_id = cursor.fetchone()[0]
            self.db_connection.commit()
            cursor.close()

            logger.info(
                f"Audit log {audit_id}: rule={rule_id}, product={product_id}, "
                f"category={classification_result} (id={categoria_id}), user={user}"
            )

            return audit_id

        except Exception as e:
            logger.error(f"Error recording audit log: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            raise

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
        try:
            if not self.db_connection:
                return []

            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT * FROM auditoria_classificacao
                WHERE id_produto = %s
                ORDER BY data_classificacao DESC
                LIMIT %s
            """, (product_id, limit))

            rows = cursor.fetchall()
            cursor.close()

            entries = [self._row_to_dict(row) for row in rows]
            logger.debug(f"Retrieved {len(entries)} audit entries for product {product_id}")

            return entries

        except Exception as e:
            logger.error(f"Error querying product history: {e}")
            return []

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
        try:
            if not self.db_connection:
                return {}

            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as times_applied,
                    MAX(data_classificacao) as last_applied,
                    AVG(tempo_avaliacao_ms) as avg_evaluation_time_ms,
                    MIN(tempo_avaliacao_ms) as min_evaluation_time_ms,
                    MAX(tempo_avaliacao_ms) as max_evaluation_time_ms
                FROM auditoria_classificacao
                WHERE id_regra = %s
            """, (rule_id,))

            row = cursor.fetchone()
            cursor.close()

            if row:
                return {
                    'times_applied': row[0],
                    'last_applied': row[1],
                    'avg_evaluation_time_ms': float(row[2]) if row[2] else 0,
                    'min_evaluation_time_ms': row[3],
                    'max_evaluation_time_ms': row[4],
                }
            return {}

        except Exception as e:
            logger.error(f"Error querying rule statistics: {e}")
            return {}

    def get_no_match_classifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get classifications where no rule matched

        Useful for identifying products that need new rules.

        Args:
            limit: Maximum number to return

        Returns:
            list: Audit entries where id_regra IS NULL (no match)
        """
        try:
            if not self.db_connection:
                return []

            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT * FROM auditoria_classificacao
                WHERE id_regra IS NULL
                ORDER BY data_classificacao DESC
                LIMIT %s
            """, (limit,))

            rows = cursor.fetchall()
            cursor.close()

            entries = [self._row_to_dict(row) for row in rows]
            logger.debug(f"Retrieved {len(entries)} no-match classifications")

            return entries

        except Exception as e:
            logger.error(f"Error querying no-match classifications: {e}")
            return []

    @staticmethod
    def _row_to_dict(row: tuple) -> Dict[str, Any]:
        """Convert database row to dictionary

        Args:
            row: Database row from auditoria_classificacao

        Returns:
            dict: Row data as dictionary
        """
        return {
            'id': row[0],
            'id_regra': row[1],
            'id_produto': row[2],
            'descricao_produto': row[3],
            'categoria_id': row[4] if len(row) > 4 else None,
            'resultado_classificacao': row[5] if len(row) > 5 else row[4],
            'data_classificacao': row[6] if len(row) > 6 else row[5],
            'usuario': row[7] if len(row) > 7 else row[6],
            'criterios_correspondentes': row[8] if len(row) > 8 else row[7],
            'tempo_avaliacao_ms': row[9] if len(row) > 9 else row[8],
        }
