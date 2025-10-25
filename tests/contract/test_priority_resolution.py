"""
Contract tests for User Story 2 - Priority Resolution

Tests that the system correctly selects the highest-priority matching rule
and provides deterministic results when priorities are tied.
"""

import pytest
from datetime import datetime
from classifier.engine import RuleEngine
from classifier.models import Product, Rule


@pytest.mark.contract
class TestPriorityResolutionUS2:
    """Contract tests for US2: Rule Priority & Conflict Resolution"""

    def test_us2_scenario_1_keyword_vs_ncm(self):
        """US2 Scenario 1: Keyword rule (priority 10) wins over NCM rule (priority 5)

        Given a product matching both a keyword rule (priority 10) and an NCM rule (priority 5),
        When the rule engine evaluates it,
        Then the keyword rule (higher priority) is selected and its classification is returned
        """
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=10, nome="Keyword Rule", ativo=True,
                 resultado_classificacao="KEYWORD_MATCH",
                 criterio_palavras_chave="laptop"),
            Rule(id=2, prioridade=5, nome="NCM Rule", ativo=True,
                 resultado_classificacao="NCM_MATCH",
                 criterio_ncm="8471*"),
        ]
        engine._load_rules = lambda: rules

        # Product matches both rules
        product = Product(description="Dell laptop", ncm="84713090")
        result = engine.evaluate(product)

        # Assert: Keyword rule (priority 10) is selected
        assert result.success is True
        assert result.classification == "KEYWORD_MATCH"
        assert result.rule_id == 1
        assert result.priority == 10

    def test_us2_scenario_2_three_rules_highest_wins(self):
        """US2 Scenario 2: Three matching rules with priorities 20, 15, and 25

        Given three rules all matching the same product with priorities 20, 15, and 25,
        When the rule engine evaluates it,
        Then only the rule with priority 25 is applied
        """
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=20, nome="Priority 20", ativo=True,
                 resultado_classificacao="PRIORITY_20",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=15, nome="Priority 15", ativo=True,
                 resultado_classificacao="PRIORITY_15",
                 criterio_palavras_chave="test"),
            Rule(id=3, prioridade=25, nome="Priority 25", ativo=True,
                 resultado_classificacao="PRIORITY_25",
                 criterio_palavras_chave="test"),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test product", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Highest priority rule (25) is selected
        assert result.success is True
        assert result.classification == "PRIORITY_25"
        assert result.rule_id == 3
        assert result.priority == 25

    def test_us2_scenario_3_identical_priority_deterministic(self):
        """US2 Scenario 3: Two rules with identical priority - deterministic result

        Given two rules with identical priority matching the same product,
        When the rule engine evaluates it,
        Then the system returns a deterministic result (oldest rule by creation date, documented clearly)
        """
        engine = RuleEngine()

        old_date = datetime(2020, 1, 1)
        new_date = datetime(2025, 1, 1)

        rules = [
            Rule(id=1, prioridade=50, nome="Older Rule", ativo=True,
                 resultado_classificacao="OLDER",
                 criterio_palavras_chave="test",
                 data_criacao=old_date),
            Rule(id=2, prioridade=50, nome="Newer Rule", ativo=True,
                 resultado_classificacao="NEWER",
                 criterio_palavras_chave="test",
                 data_criacao=new_date),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test product", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Older rule wins (deterministic tiebreaker)
        assert result.success is True
        assert result.classification == "OLDER"
        assert result.rule_id == 1
        assert result.priority == 50

    def test_priority_resolution_is_deterministic(self):
        """Verify: Priority resolution is deterministic (same input = same output)

        This tests FR-006: System MUST provide a deterministic tiebreaker
        when two rules have identical priority
        """
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=100, nome="Rule 1", ativo=True,
                 resultado_classificacao="RESULT_1",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2020, 1, 1)),
            Rule(id=2, prioridade=100, nome="Rule 2", ativo=True,
                 resultado_classificacao="RESULT_2",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2025, 1, 1)),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")

        # Evaluate multiple times
        result1 = engine.evaluate(product)
        result2 = engine.evaluate(product)
        result3 = engine.evaluate(product)

        # Assert: All results are identical
        assert result1.rule_id == result2.rule_id == result3.rule_id == 1
        assert result1.classification == result2.classification == result3.classification == "RESULT_1"

    def test_priority_numeric_higher_number_wins(self):
        """Verify: Higher numeric priority value wins

        This tests FR-005: System MUST handle rule priority as a numeric field
        with higher numbers = higher priority
        """
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=1, nome="Low", ativo=True,
                 resultado_classificacao="LOW",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=50, nome="Medium", ativo=True,
                 resultado_classificacao="MEDIUM",
                 criterio_palavras_chave="test"),
            Rule(id=3, prioridade=99, nome="High", ativo=True,
                 resultado_classificacao="HIGH",
                 criterio_palavras_chave="test"),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Highest numeric priority (99) wins
        assert result.classification == "HIGH"
        assert result.rule_id == 3

    def test_priority_resolution_with_partial_matches(self):
        """Complex scenario: Priority resolution when only some rules match

        Verifies that priority is only considered among matching rules,
        not globally among all rules.
        """
        engine = RuleEngine()

        rules = [
            # High priority but doesn't match
            Rule(id=1, prioridade=100, nome="No Match", ativo=True,
                 resultado_classificacao="HIGH_NO_MATCH",
                 criterio_palavras_chave="laptop"),
            # Low priority but matches
            Rule(id=2, prioridade=10, nome="Low Match", ativo=True,
                 resultado_classificacao="LOW_MATCH",
                 criterio_palavras_chave="cable"),
            # Medium priority and matches
            Rule(id=3, prioridade=50, nome="Medium Match", ativo=True,
                 resultado_classificacao="MEDIUM_MATCH",
                 criterio_palavras_chave="cable"),
        ]
        engine._load_rules = lambda: rules

        # Product matches rules 2 and 3 (not 1)
        product = Product(description="copper cable", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Rule 3 (medium priority, matching) wins over rule 1 (high priority, non-matching)
        assert result.classification == "MEDIUM_MATCH"
        assert result.rule_id == 3

    def test_priority_with_complex_criteria(self):
        """Priority resolution with rules having multiple complex criteria

        Ensures that priority takes precedence over criteria complexity.
        """
        engine = RuleEngine()

        rules = [
            # Complex rule with low priority
            Rule(id=1, prioridade=10, nome="Complex Low", ativo=True,
                 resultado_classificacao="COMPLEX_LOW",
                 criterio_palavras_chave="laptop",
                 criterio_ncm="8471*",
                 criterio_tamanho_max=2.0,
                 criterio_quantidade_min=1,
                 criterio_categoria="ELECTRONICS"),
            # Simple rule with high priority
            Rule(id=2, prioridade=100, nome="Simple High", ativo=True,
                 resultado_classificacao="SIMPLE_HIGH",
                 criterio_palavras_chave="laptop"),
        ]
        engine._load_rules = lambda: rules

        # Product matches both rules
        product = Product(
            description="gaming laptop",
            ncm="84713090",
            size=1.5,
            quantity=5,
            category="ELECTRONICS"
        )
        result = engine.evaluate(product)

        # Assert: High priority simple rule wins
        assert result.classification == "SIMPLE_HIGH"
        assert result.rule_id == 2

    def test_priority_with_many_matching_rules(self):
        """Priority resolution with 10+ matching rules

        Stress test: ensure correct winner selection with many matches.
        """
        engine = RuleEngine()

        # Create 15 rules with different priorities, all matching
        rules = [
            Rule(id=i, prioridade=i*10, nome=f"Rule {i}", ativo=True,
                 resultado_classificacao=f"CLASS_{i}",
                 criterio_palavras_chave="test")
            for i in range(1, 16)
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Highest priority rule (15*10=150) wins
        assert result.rule_id == 15
        assert result.priority == 150
        assert result.classification == "CLASS_15"

    def test_priority_zero_is_valid(self):
        """Priority value of 0 is valid and can win if it's the highest

        Edge case: negative and zero priorities should work.
        """
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=-10, nome="Negative", ativo=True,
                 resultado_classificacao="NEGATIVE",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=0, nome="Zero", ativo=True,
                 resultado_classificacao="ZERO",
                 criterio_palavras_chave="test"),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Zero (higher than -10) wins
        assert result.rule_id == 2
        assert result.priority == 0
