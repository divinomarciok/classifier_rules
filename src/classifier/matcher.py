"""
Criteria matcher - Matches product attributes against rule criteria

Implements FR-002 (Criteria evaluation) and FR-009 (Criteria validation)
"""

import logging
import re
from typing import Optional, List

from classifier.models import Product, Rule

logger = logging.getLogger(__name__)


class Matcher:
    """Matches products against rule criteria

    Supports:
    - Keyword matching (case-insensitive substring in description)
    - NCM pattern matching (wildcard * support)
    - Size range matching (min/max)
    - Quantity range matching (min/max)
    - Category exact matching

    Returns True only if ALL specified criteria match.
    """

    @staticmethod
    def matches_all_criteria(product: Product, rule: Rule) -> bool:
        """Check if product matches ALL criteria specified in rule

        A product matches the rule only if ALL of the following are true:
        - If rule has keyword criteria, product description contains keyword
        - If rule has NCM criteria, product NCM matches pattern
        - If rule has size criteria, product size is within range
        - If rule has quantity criteria, product quantity is within range
        - If rule has category criteria, product category matches exactly

        Args:
            product: Product object to match
            rule: Rule object with criteria to match against

        Returns:
            bool: True if product matches all specified criteria, False otherwise

        Implementation Plan:
            1. Check keyword criteria (if specified)
            2. Check NCM criteria (if specified)
            3. Check size range (if specified)
            4. Check quantity range (if specified)
            5. Check category criteria (if specified)
            6. Return True only if ALL checks pass
        """
        # Check each criterion IF it's specified in the rule
        # If criterion is None/empty, it's not used (passes the check)

        # 1. Keyword matching
        if rule.criterio_palavras_chave:
            if not Matcher._match_keywords(product.description or '', rule.criterio_palavras_chave):
                return False

        # 2. NCM pattern matching
        if rule.criterio_ncm:
            if not Matcher._match_ncm(product.ncm or '', rule.criterio_ncm):
                return False

        # 3. Size range matching
        if rule.criterio_tamanho_min is not None or rule.criterio_tamanho_max is not None:
            if not Matcher._match_size(
                product.size,
                rule.criterio_tamanho_min,
                rule.criterio_tamanho_max
            ):
                return False

        # 4. Quantity range matching
        if rule.criterio_quantidade_min is not None or rule.criterio_quantidade_max is not None:
            if not Matcher._match_quantity(
                product.quantity,
                rule.criterio_quantidade_min,
                rule.criterio_quantidade_max
            ):
                return False

        # 5. Category exact matching
        if rule.criterio_categoria:
            if not Matcher._match_category(product.category, rule.criterio_categoria):
                return False

        # All specified criteria matched
        return True

    @staticmethod
    def _match_keywords(description: str, keywords: str) -> bool:
        """Match keywords in product description

        Supports comma-separated keywords, case-insensitive substring matching.

        Args:
            description: Product description
            keywords: Comma-separated keywords (e.g., "laptop,computer")

        Returns:
            bool: True if description contains at least one keyword

        Examples:
            >>> Matcher._match_keywords("laptop computer", "laptop")
            True
            >>> Matcher._match_keywords("USB cable", "laptop")
            False
            >>> Matcher._match_keywords("Monitor display", "monitor,screen")
            True
        """
        if not description or not keywords:
            return False

        # Convert to lowercase for case-insensitive matching
        description_lower = description.lower()

        # Split keywords by comma and check each one
        keyword_list = [kw.strip().lower() for kw in keywords.split(',')]

        # Return True if ANY keyword is found (substring match)
        for keyword in keyword_list:
            if keyword in description_lower:
                logger.debug(f"Keyword match: '{keyword}' found in '{description}'")
                return True

        logger.debug(f"No keywords matched: {keywords} not in '{description}'")
        return False

    @staticmethod
    def _match_ncm(ncm_code: str, ncm_pattern: str) -> bool:
        """Match NCM code against pattern

        Supports wildcard matching with * (matches any characters).
        Example: "8471*" matches "84713090" or "84714000"

        Args:
            ncm_code: Product NCM code
            ncm_pattern: Pattern with optional * wildcard

        Returns:
            bool: True if NCM code matches pattern

        Examples:
            >>> Matcher._match_ncm("84713090", "8471*")
            True
            >>> Matcher._match_ncm("85444290", "8544*")
            True
            >>> Matcher._match_ncm("85444290", "8471*")
            False
        """
        if not ncm_code or not ncm_pattern:
            return False

        # Convert pattern to regex for wildcard matching
        # Replace * with .* (regex for any characters)
        regex_pattern = ncm_pattern.replace('*', '.*')
        # Anchor pattern to start and end
        regex_pattern = f"^{regex_pattern}$"

        matches = re.match(regex_pattern, ncm_code) is not None

        if matches:
            logger.debug(f"NCM match: '{ncm_code}' matches pattern '{ncm_pattern}'")
        else:
            logger.debug(f"NCM no match: '{ncm_code}' does not match pattern '{ncm_pattern}'")

        return matches

    @staticmethod
    def _match_size(size: Optional[float], size_min: Optional[float], size_max: Optional[float]) -> bool:
        """Check if size is within range

        Args:
            size: Product size
            size_min: Minimum size (inclusive)
            size_max: Maximum size (inclusive)

        Returns:
            bool: True if size is within range (or if size/range not specified)
        """
        # If size is not specified in product, can't match
        if size is None:
            logger.debug("Size match skipped: product size is None")
            return size_min is None and size_max is None

        # Check minimum
        if size_min is not None and size < size_min:
            logger.debug(f"Size no match: {size} < min {size_min}")
            return False

        # Check maximum
        if size_max is not None and size > size_max:
            logger.debug(f"Size no match: {size} > max {size_max}")
            return False

        logger.debug(f"Size match: {size} within range [{size_min}, {size_max}]")
        return True

    @staticmethod
    def _match_quantity(
        quantity: Optional[int],
        quantity_min: Optional[int],
        quantity_max: Optional[int]
    ) -> bool:
        """Check if quantity is within range

        Args:
            quantity: Product quantity
            quantity_min: Minimum quantity (inclusive)
            quantity_max: Maximum quantity (inclusive)

        Returns:
            bool: True if quantity is within range (or if quantity/range not specified)
        """
        # If quantity is not specified in product, can't match
        if quantity is None:
            logger.debug("Quantity match skipped: product quantity is None")
            return quantity_min is None and quantity_max is None

        # Check minimum
        if quantity_min is not None and quantity < quantity_min:
            logger.debug(f"Quantity no match: {quantity} < min {quantity_min}")
            return False

        # Check maximum
        if quantity_max is not None and quantity > quantity_max:
            logger.debug(f"Quantity no match: {quantity} > max {quantity_max}")
            return False

        logger.debug(f"Quantity match: {quantity} within range [{quantity_min}, {quantity_max}]")
        return True

    @staticmethod
    def _match_category(category: Optional[str], category_criteria: str) -> bool:
        """Check if category matches exactly

        Args:
            category: Product category
            category_criteria: Required category

        Returns:
            bool: True if categories match exactly
        """
        if not category_criteria:
            return True

        if category is None:
            logger.debug(f"Category no match: product category is None, required '{category_criteria}'")
            return False

        matches = category.upper() == category_criteria.upper()

        if matches:
            logger.debug(f"Category match: '{category}' == '{category_criteria}'")
        else:
            logger.debug(f"Category no match: '{category}' != '{category_criteria}'")

        return matches
