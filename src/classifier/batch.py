"""
Batch classification service - Processes multiple products efficiently

Implements US4 (Batch Classification)
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from classifier.engine import RuleEngine
from classifier.models import Product

logger = logging.getLogger(__name__)


class BatchClassifier:
    """Batch processes products for classification

    Efficiently classifies multiple products from database in a single operation.
    Supports limiting, offset, and comprehensive reporting.

    Constitutional Principle I: Business-Driven Development
    """

    def __init__(self, db_connection):
        """Initialize batch classifier

        Args:
            db_connection: Database connection for product and rule queries
        """
        self.db_connection = db_connection
        self.engine = RuleEngine(db_connection)

    def classify_batch(
        self,
        limit: int = 500,
        offset: int = 0,
        where_clause: Optional[str] = None,
        update_db: bool = True
    ) -> Dict[str, Any]:
        """Classify a batch of products from database

        Queries database for unclassified products, evaluates each against rules,
        optionally updates database, and returns comprehensive summary.

        Args:
            limit: Maximum number of products to process (default: 500)
            offset: Starting row offset for pagination (default: 0)
            where_clause: Custom WHERE clause for filtering (e.g., "ncm LIKE '84%'")
            update_db: Whether to update database with classifications (default: True)

        Returns:
            dict: Batch processing summary with:
                - total_processed: Number of products evaluated
                - total_matched: Count of products that matched a rule
                - total_no_match: Count of products with no match
                - match_rate: Percentage of matched products (0.0-1.0)
                - classifications: Dict of classification -> count
                - elapsed_time_ms: Total processing time
                - no_match_products: List of unclassified products for review

        Implementation Plan:
            1. Query database for unclassified products with limit/offset
            2. For each product, call engine.evaluate()
            3. Optionally update database with classification
            4. Collect all results and compute statistics
            5. Return comprehensive summary
        """
        try:
            start_time = time.time()
            logger.info(f"Starting batch classification: limit={limit}, offset={offset}")

            # 1. Query unclassified products
            products = self._get_unclassified_products(limit, offset, where_clause)
            logger.info(f"Found {len(products)} products to classify")

            # 2. Evaluate each product
            results = []
            for product_row in products:
                product = self._row_to_product(product_row)
                result = self.engine.evaluate(product)
                results.append({
                    'product_id': product.id,
                    'product_description': product.description,
                    'result': result,
                    'row_data': product_row
                })

            # 3. Process results
            matched_count = 0
            no_match_count = 0
            classifications = {}
            no_match_products = []
            audit_ids = []

            for item in results:
                if item['result'].success:
                    classification = item['result'].classification
                    categoria_id = item['result'].categoria_id
                    product_description = item['product_description']

                    # Check if this is a NO_MATCH result
                    if classification == 'NO_MATCH':
                        # Product with no matching rules
                        no_match_count += 1
                        no_match_products.append({
                            'id': item['product_id'],
                            'description': product_description
                        })

                        # IMPORTANT: Do NOT update database for NO_MATCH products
                        # They remain with status='pending' so they can be reprocessed
                        # when new rules are added
                        logger.debug(
                            f"Product {item['product_id']} ({product_description}) has no matching rules. "
                            f"Status remains 'pending' for future reprocessing."
                        )
                    else:
                        # Product matched a rule - update database
                        matched_count += 1
                        classifications[classification] = classifications.get(classification, 0) + 1

                        # Update database if requested (only for matches, not NO_MATCH)
                        if update_db:
                            self._update_product_classification(
                                item['product_id'],
                                categoria_id,
                                classification
                            )
                else:
                    no_match_count += 1
                    no_match_products.append({
                        'id': item['product_id'],
                        'description': item['product_description']
                    })
                    logger.warning(f"Product {item['product_id']} ({item['product_description']}) evaluation failed (success=False)")

            # 4. Compute statistics
            elapsed_ms = (time.time() - start_time) * 1000
            match_rate = matched_count / len(results) if results else 0.0

            summary = {
                'total_processed': len(results),
                'total_matched': matched_count,
                'total_no_match': no_match_count,
                'match_rate': match_rate,
                'classifications': classifications,
                'elapsed_time_ms': int(elapsed_ms),
                'no_match_products': no_match_products,
            }

            logger.info(
                f"Batch classification complete: "
                f"processed={len(results)}, matched={matched_count}, "
                f"no_match={no_match_count}, time={elapsed_ms:.0f}ms"
            )

            return summary

        except Exception as e:
            logger.error(f"Error during batch classification: {e}")
            raise

    def _get_unclassified_products(
        self,
        limit: int,
        offset: int,
        where_clause: Optional[str] = None
    ) -> List[tuple]:
        """Query database for products pending classification

        Queries for products with status='pending' (never attempted classification).
        Products with no_match status are NOT reprocessed unless explicitly requested.

        Args:
            limit: Number of rows to fetch
            offset: Starting row offset
            where_clause: Optional WHERE clause for filtering

        Returns:
            list: Tuples of (id, description, ncm, categoria, size, quantity, ...)
        """
        try:
            cursor = self.db_connection.cursor()

            # Build query for pending products (never classified)
            # Products with status='pending' have never been processed
            # Products with status='no_match' were attempted but no rules matched
            # We only process 'pending' to avoid reprocessing infinitely
            query = "SELECT * FROM produtos_tabela WHERE status_classificacao = 'pending'"

            if where_clause:
                query += f" AND {where_clause}"

            query += f" LIMIT %s OFFSET %s"

            params = [limit, offset]
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            logger.debug(f"Queried {len(rows)} pending products for classification")
            return rows

        except Exception as e:
            logger.error(f"Error querying products: {e}")
            raise

    def _row_to_product(self, row: tuple) -> Product:
        """Convert database row to Product object

        Handles various row formats with optional fields.

        Args:
            row: Database row tuple (id, description, ncm, categoria, size, quantity, ...)

        Returns:
            Product: Product object for evaluation
        """
        # Extract required fields (always present)
        product_id = row[0]
        description = row[1]
        ncm = row[2]

        # Extract optional fields with safe indexing
        categoria = row[3] if len(row) > 3 else None
        size = row[4] if len(row) > 4 else None
        quantity = row[5] if len(row) > 5 else None

        # Create product with flexible schema
        product = Product(
            id=product_id,
            description=description,
            ncm=ncm,
            size=size,
            quantity=quantity,
            category=categoria  # Store category if present
        )

        return product

    def _update_product_classification(self, product_id: str, categoria_id: int, classification_name: str) -> bool:
        """Update database with classification result

        Args:
            product_id: Product ID to update
            categoria_id: Category ID to assign
            classification_name: Category name for logging

        Returns:
            bool: True if update successful
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                "UPDATE produtos_tabela SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE id = %s",
                (categoria_id, 'matched', datetime.now(), product_id)
            )

            self.db_connection.commit()
            cursor.close()

            logger.debug(f"Updated product {product_id} with categoria_id={categoria_id} ({classification_name})")
            return True

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            self.db_connection.rollback()
            raise

    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get overall batch processing statistics

        Useful for monitoring progress across multiple batch runs.
        Breaks down products by status:
        - 'pending': Never attempted classification
        - 'matched': Has categoria assigned
        - 'no_match': Attempted classification but no rules matched

        Returns:
            dict: Aggregate statistics by status
        """
        try:
            cursor = self.db_connection.cursor()

            # Count by status (if column exists)
            try:
                cursor.execute("""
                    SELECT
                        COALESCE(status_classificacao, 'unknown') as status,
                        COUNT(*) as count
                    FROM produtos_tabela
                    GROUP BY status_classificacao
                """)
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            except Exception:
                # Fallback if status_classificacao column doesn't exist yet
                logger.warning("status_classificacao column not found, using fallback query")
                cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NOT NULL")
                classified_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NULL")
                unclassified_count = cursor.fetchone()[0]

                status_counts = {
                    'matched': classified_count,
                    'pending': unclassified_count
                }

            # Count totals
            total_count = sum(status_counts.values())
            matched_count = status_counts.get('matched', 0)
            pending_count = status_counts.get('pending', 0)
            no_match_count = status_counts.get('no_match', 0)

            cursor.close()

            statistics = {
                'total_products': total_count,
                'by_status': status_counts,
                'matched': matched_count,
                'pending': pending_count,
                'no_match': no_match_count,
                'classification_rate': matched_count / total_count if total_count > 0 else 0.0,
                'note': 'pending=never attempted, matched=has categoria, no_match=no rules matched'
            }

            return statistics

        except Exception as e:
            logger.error(f"Error getting batch statistics: {e}")
            return {}
