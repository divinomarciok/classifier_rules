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
                    matched_count += 1
                    classification = item['result'].classification
                    classifications[classification] = classifications.get(classification, 0) + 1

                    # Update database if requested
                    if update_db:
                        self._update_product_classification(
                            item['product_id'],
                            item['result'].classification
                        )
                else:
                    no_match_count += 1
                    no_match_products.append(item['product_id'])

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
        """Query database for unclassified products

        Args:
            limit: Number of rows to fetch
            offset: Starting row offset
            where_clause: Optional WHERE clause for filtering

        Returns:
            list: Tuples of (id, description, ncm, categoria, size, quantity, ...)
        """
        try:
            cursor = self.db_connection.cursor()

            # Build query for unclassified products
            query = "SELECT * FROM produtos_tabela WHERE categoria IS NULL"

            if where_clause:
                query += f" AND {where_clause}"

            query += f" LIMIT %s OFFSET %s"

            params = [limit, offset]
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()

            logger.debug(f"Queried {len(rows)} unclassified products")
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

    def _update_product_classification(self, product_id: str, classification: str) -> bool:
        """Update database with classification result

        Args:
            product_id: Product ID to update
            classification: Classification result to store

        Returns:
            bool: True if update successful
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                "UPDATE produtos_tabela SET categoria = %s, data_classificacao = %s WHERE id = %s",
                (classification, datetime.now(), product_id)
            )

            self.db_connection.commit()
            cursor.close()

            logger.debug(f"Updated product {product_id} with classification {classification}")
            return True

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            self.db_connection.rollback()
            raise

    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get overall batch processing statistics

        Useful for monitoring progress across multiple batch runs.

        Returns:
            dict: Aggregate statistics
        """
        try:
            cursor = self.db_connection.cursor()

            # Count classified vs unclassified
            cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NOT NULL")
            classified_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NULL")
            unclassified_count = cursor.fetchone()[0]

            total_count = classified_count + unclassified_count

            cursor.close()

            statistics = {
                'total_products': total_count,
                'classified': classified_count,
                'unclassified': unclassified_count,
                'classification_rate': classified_count / total_count if total_count > 0 else 0.0,
            }

            return statistics

        except Exception as e:
            logger.error(f"Error getting batch statistics: {e}")
            return {}
