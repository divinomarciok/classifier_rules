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
        # TODO: Implement all criteria matching
        pass

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
        # TODO: Implement keyword matching
        pass

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
        # TODO: Implement NCM pattern matching
        pass

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
        # TODO: Implement size range checking
        pass

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
        # TODO: Implement quantity range checking
        pass

    @staticmethod
    def _match_category(category: Optional[str], category_criteria: str) -> bool:
        """Check if category matches exactly

        Args:
            category: Product category
            category_criteria: Required category

        Returns:
            bool: True if categories match exactly
        """
        # TODO: Implement category exact matching
        pass
