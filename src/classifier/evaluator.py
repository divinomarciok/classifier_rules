"""
Rule evaluator - Finds matching rules and resolves conflicts via priority

Implements US2 (Priority resolution) and FR-004, FR-005, FR-006
"""

import logging
from typing import List, Optional

from classifier.models import Rule
from classifier.matcher import Matcher

logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluates products against rules and selects the best match

    Responsibilities:
    1. Filter rules that match product criteria (via Matcher)
    2. Resolve conflicts when multiple rules match (via priority)
    3. Apply consistent tiebreaker (oldest rule by creation date)
    """

    @staticmethod
    def get_matching_rules(product, rules: List[Rule]) -> List[Rule]:
        """Find all rules that match the product

        Filters rules where Matcher.matches_all_criteria returns True.
        Applies Matcher to each rule in order.

        Args:
            product: Product object to match
            rules: List of Rule objects to evaluate

        Returns:
            list: Filtered list of matching Rule objects (may be empty)

        Implementation Plan:
            1. For each rule in rules list:
               - Use Matcher.matches_all_criteria(product, rule)
               - If True, add to matches list
            2. Return list of matching rules
        """
        # TODO: Implement matching logic
        pass

    @staticmethod
    def select_winner(matching_rules: List[Rule]) -> Rule:
        """Select highest-priority rule from matching rules

        Implements FR-004, FR-005, FR-006:
        - Returns rule with highest prioridade (FR-004)
        - If tied, returns oldest rule by data_criacao (FR-006)
        - Deterministic: same input always returns same output

        Args:
            matching_rules: List of rules that matched the product

        Returns:
            Rule: Single Rule with highest priority (oldest if tied)

        Raises:
            EvaluationError: If matching_rules is empty

        Examples:
            >>> rules = [
            ...     Rule(id=1, prioridade=10, nome="Low", data_criacao=datetime.now()),
            ...     Rule(id=2, prioridade=20, nome="High", data_criacao=datetime.now()),
            ... ]
            >>> winner = Evaluator.select_winner(rules)
            >>> assert winner.id == 2  # Higher priority wins

            >>> # Tiebreaker: oldest rule wins
            >>> old_rule = Rule(id=1, prioridade=20, data_criacao=datetime(2020, 1, 1))
            >>> new_rule = Rule(id=2, prioridade=20, data_criacao=datetime(2025, 1, 1))
            >>> winner = Evaluator.select_winner([new_rule, old_rule])
            >>> assert winner.id == 1  # Older rule wins tiebreaker
        """
        # TODO: Implement priority resolution with tiebreaker
        pass
