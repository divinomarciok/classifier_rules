"""
Core RuleEngine class - Main entry point for rule evaluation

Implements US1, US2, US3 (Basic evaluation, priority resolution, audit logging)
Implements Constitutional Principle I (Data-Driven Logic)
"""

from typing import Optional, Dict, Any
import time
import logging

from classifier import ProductError, DatabaseError, EvaluationError
from classifier.models import Product, ClassificationResult, Rule, Category
from classifier.matcher import Matcher
from classifier.evaluator import Evaluator
from classifier.utils import get_db_connection
from classifier.category_service import CategoryService

logger = logging.getLogger(__name__)


class RuleEngine:
    """Core rule evaluation engine

    Reads classification rules from database, applies them with priority resolution,
    and logs all decisions for auditability.

    Usage:
        >>> engine = RuleEngine()
        >>> product = {'id': 'P001', 'description': 'laptop', 'ncm': '84713090'}
        >>> result = engine.evaluate(product)
        >>> print(result.to_dict())
    """

    def __init__(self, db_connection=None, cache_rules: bool = True):
        """Initialize RuleEngine

        Args:
            db_connection: Database connection. If None, creates new connection.
            cache_rules: Whether to cache rules in memory for performance
        """
        self.db_connection = db_connection
        self.cache_rules = cache_rules
        self._rules_cache = None
        self.category_service = CategoryService(db_connection) if db_connection else None
        self.logger = logging.getLogger(__name__)

    def _load_rules(self) -> list:
        """Load all active rules from database

        Returns:
            list: List of Rule objects (only active rules)

        Raises:
            DatabaseError: If query fails
        """
        try:
            if not self.db_connection:
                raise DatabaseError("Database connection not configured")

            cursor = self.db_connection.cursor()

            # FR-003: Only fetch active rules
            cursor.execute("""
                SELECT
                    id, prioridade, nome, ativo,
                    criterio_palavras_chave, criterio_ncm,
                    criterio_tamanho_min, criterio_tamanho_max,
                    criterio_quantidade_min, criterio_quantidade_max,
                    criterio_categoria,
                    categoria_id,
                    data_criacao, data_atualizacao
                FROM regras_de_classificacao
                WHERE ativo = TRUE
                ORDER BY prioridade DESC, data_criacao ASC
            """)

            rows = cursor.fetchall()
            rules = [Rule.from_db_row(row) for row in rows]

            cursor.close()

            logger.info(f"Loaded {len(rules)} active rules from database")
            return rules

        except Exception as e:
            logger.error(f"Error loading rules from database: {e}")
            raise DatabaseError(f"Failed to load rules from database: {e}") from e

    def _initialize_cache(self) -> None:
        """Load rules into memory cache if caching enabled"""
        if self.cache_rules:
            self._rules_cache = self._load_rules()
            logger.info(f"Loaded {len(self._rules_cache)} rules into cache")

    def get_rules(self, active_only: bool = True) -> list:
        """Get list of rules

        Args:
            active_only: If True, return only active rules

        Returns:
            list: List of Rule objects
        """
        if self._rules_cache is not None:
            # Return cached rules
            if active_only:
                return [r for r in self._rules_cache if r.is_active()]
            return self._rules_cache

        # No cache, load from database
        return self._load_rules()

    def refresh_cache(self) -> None:
        """Reload rules from database into cache"""
        self._rules_cache = None
        if self.cache_rules:
            self._initialize_cache()
        logger.info("Rule cache refreshed")

    def evaluate(
        self,
        product_data: Dict[str, Any],
        user: Optional[str] = None,
    ) -> ClassificationResult:
        """Evaluate a product against rules and return classification

        This is the main entry point for rule evaluation.

        Args:
            product_data: Product data as dictionary with keys:
                - id: Product ID
                - description: Product description
                - ncm: NCM code
                - size: Product size (optional)
                - quantity: Product quantity (optional)
                - (any other fields)
            user: User/system performing the evaluation (default: 'system')

        Returns:
            ClassificationResult: Classification result with matched rule details

        Raises:
            ProductError: If product data is invalid
            DatabaseError: If database operation fails
            EvaluationError: If evaluation fails

        Implementation Plan:
            1. Validate product data (FR-009)
            2. Get all active rules from database or cache
            3. Use Evaluator to find matching rules (FR-002, FR-003)
            4. Use priority resolver to select winner (FR-004, FR-005, FR-006)
            5. Log decision to audit table (FR-007)
            6. Return result

        Performance:
            Must complete in < 500ms for 95th percentile with 10,000 rules (SC-003)
        """
        start_time = time.time()

        try:
            if user is None:
                user = 'system'

            # 1. Validate and convert product data to Product object
            if isinstance(product_data, dict):
                # Extract required fields
                description = product_data.get('description')
                ncm = product_data.get('ncm')

                if not description or not ncm:
                    raise ProductError(
                        "Product data missing required fields: 'description' and 'ncm' are required"
                    )

                # Create Product object
                product = Product(**product_data)
            elif isinstance(product_data, Product):
                product = product_data
            else:
                raise ProductError(f"Invalid product type: {type(product_data)}")

            # 2. Get all active rules
            rules = self.get_rules(active_only=True)

            if not rules:
                logger.warning("No active rules found in database")
                return ClassificationResult(
                    classification='NO_MATCH',
                    success=True,
                    message='No active rules in system'
                )

            # 3. Find matching rules (FR-002, FR-003)
            matching_rules = Evaluator.get_matching_rules(product, rules)

            elapsed_ms = int((time.time() - start_time) * 1000)

            # 4. Handle no-match case (FR-008)
            if not matching_rules:
                logger.info(f"No rules matched for product {product.id} ({product.description})")
                return ClassificationResult(
                    classification='NO_MATCH',
                    success=True,
                    evaluation_time_ms=elapsed_ms,
                    message='No matching rules found'
                )

            # 5. Select winner (FR-004, FR-005, FR-006)
            try:
                winner = Evaluator.select_winner(matching_rules)
            except EvaluationError as e:
                logger.error(f"Error selecting winner: {e}")
                raise

            # 6. Get category name from categoria_id
            category_name = 'UNKNOWN'
            if self.category_service and winner.categoria_id:
                category = self.category_service.get_category_by_id(winner.categoria_id)
                if category:
                    category_name = category.nome
                else:
                    logger.warning(f"Category {winner.categoria_id} not found in database")
                    category_name = f'CATEGORY_{winner.categoria_id}'

            # 7. Build result
            result = ClassificationResult(
                classification=category_name,
                categoria_id=winner.categoria_id,
                rule_id=winner.id,
                rule_name=winner.nome,
                priority=winner.prioridade,
                matched_criteria=['criterio_' + c for c in ['palavras_chave', 'ncm', 'tamanho_min', 'tamanho_max', 'quantidade_min', 'quantidade_max', 'categoria'] if getattr(winner, f'criterio_{c}', None) is not None],
                evaluation_time_ms=elapsed_ms,
                success=True,
                message=f'Matched rule {winner.id} ({winner.nome})'
            )

            logger.info(f"Product {product.id} ({product.description}) classified as {result.classification} (id={result.categoria_id}) by rule {winner.id}")

            # 8. Log to audit table (FR-007) - delegated to caller or middleware
            # This is typically done at a higher level, but we can record here if needed

            return result

        except (ProductError, DatabaseError, EvaluationError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Unexpected error during evaluation: {e}", exc_info=True)
            raise EvaluationError(f"Unexpected error during evaluation: {e}") from e
